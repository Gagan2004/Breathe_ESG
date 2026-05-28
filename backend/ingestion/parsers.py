import csv
import json
import math
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import IngestionJob, RawRecord, NormalizedActivity, AuditTrail

# ---------------------------------------------------------
# Airport Coordinates & Haversine Distance Helper
# ---------------------------------------------------------
AIRPORT_COORDINATES = {
    'JFK': (40.6398, -73.7789),
    'LAX': (33.9416, -118.4085),
    'LHR': (51.4700, -0.4543),
    'CDG': (49.0097, 2.5479),
    'DXB': (25.2532, 55.3657),
    'SIN': (1.3644, 103.9911),
    'HND': (35.5494, 139.7798),
    'SYD': (-33.9461, 151.1772),
    'BOM': (19.0896, 72.8656),
    'DEL': (28.5562, 77.1000),
    'FRA': (50.0379, 8.5622),
    'AMS': (52.3105, 4.7683),
    'ORD': (41.9742, -87.9073),
    'SFO': (37.6213, -122.3790),
    'DFW': (32.8998, -97.0403),
    'DEN': (39.8561, -104.6737),
    'ATL': (33.6407, -84.4277),
    'MUC': (48.3538, 11.7861),
    'ZRH': (47.4582, 8.5555),
    'HKG': (22.3080, 113.9185),
    'IAD': (38.9488, -77.4560),  # Washington Dulles added to match user's sample data!
}

def calculate_haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points."""
    R = 6371.0 # Earth's radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ---------------------------------------------------------
# Date Parsing Helpers
# ---------------------------------------------------------
DATE_FORMATS = [
    '%Y-%m-%d',
    '%d.%m.%Y',
    '%m/%d/%Y',
    '%Y/%m/%d',
    '%Y%m%d',
]

def parse_date(date_str):
    """Tries multiple date formats to parse date string."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Could not parse date '{date_str}' using standard formats.")

# ---------------------------------------------------------
# Known Plant Lookup Table for SAP
# ---------------------------------------------------------
KNOWN_PLANTS = {
    '1020': 'Munich ESG HQ',
    '3150': 'Hamburg Assembly Plant',
    'PL01': 'Munich ESG HQ (Legacy)',
    'PL02': 'Hamburg Assembly Plant (Legacy)',
    'PL03': 'Stuttgart R&D Hub (Legacy)',
}

# ---------------------------------------------------------
# Parser Classes
# ---------------------------------------------------------
class BaseParser:
    def __init__(self, job: IngestionJob):
        self.job = job
        self.org = job.organization

    def run(self):
        self.job.status = 'PROCESSING'
        self.job.save()
        try:
            self.parse_and_normalize()
            self.job.status = 'COMPLETED'
            self.job.completed_at = timezone.now()
            self.job.save()
        except Exception as e:
            self.job.status = 'FAILED'
            self.job.error_log = str(e)
            self.job.completed_at = timezone.now()
            self.job.save()
            raise e

    def parse_and_normalize(self):
        raise NotImplementedError("Subclasses must implement parse_and_normalize")


class SAPParser(BaseParser):
    # Technical columns aligned to user OData spec
    HEADER_ALIASES = {
        'plant_code': ['WERKS', 'plant_code', 'plant', 'Werk'],
        'fuel_type': ['MATNR', 'fuel_type', 'material', 'Material', 'FuelType'],
        'quantity': ['MENGE', 'quantity', 'qty', 'Menge', 'Quantity'],
        'unit': ['MEINS', 'unit', 'uom', 'Einheit', 'Unit'],
        'posting_date': ['BEDAT', 'posting_date', 'date', 'BUDAT', 'Buchungsdatum', 'PostingDate'],
        'vendor_name': ['LIFNR', 'vendor_name', 'vendor', 'Lieferant', 'VendorName'],
        'po_number': ['EBELN', 'po_number', 'PO'],
        'po_item': ['EBELP', 'po_item', 'Item'],
        'price': ['NETWR', 'price', 'net_price'],
        'currency': ['WAERS', 'currency', 'Currency']
    }

    def resolve_headers(self, headers):
        resolved = {}
        for internal_name, aliases in self.HEADER_ALIASES.items():
            for alias in aliases:
                matching_header = next((h for h in headers if h.strip().lower() == alias.lower()), None)
                if matching_header:
                    resolved[internal_name] = matching_header
                    break
        return resolved

    def parse_and_normalize(self):
        content = self.job.raw_file_content
        reader = csv.reader(content.splitlines())
        
        try:
            headers = next(reader)
        except StopIteration:
            raise ValidationError("The uploaded CSV is empty.")

        resolved_headers = self.resolve_headers(headers)
        
        # Ensure minimum required fields exist for SAP
        required_fields = ['fuel_type', 'quantity', 'unit', 'posting_date']
        missing_fields = [f for f in required_fields if f not in resolved_headers]
        if missing_fields:
            raise ValidationError(f"Missing required CSV columns: {', '.join(missing_fields)}. Checked headers: {headers}")

        row_idx = 1
        for row in reader:
            row_idx += 1
            if not row or not any(field.strip() for field in row):
                continue
            
            row_data = {}
            for key, file_header in resolved_headers.items():
                try:
                    idx = headers.index(file_header)
                    row_data[key] = row[idx].strip() if idx < len(row) else ''
                except ValueError:
                    row_data[key] = ''

            raw_record = RawRecord.objects.create(
                job=self.job,
                row_index=row_idx,
                raw_data=row_data,
                status='UNPROCESSED'
            )

            try:
                self.normalize_row(raw_record)
            except Exception as e:
                raw_record.status = 'ERROR'
                raw_record.error_message = str(e)
                raw_record.save()

    def normalize_row(self, raw_record: RawRecord):
        data = raw_record.raw_data
        flags = []
        
        # 1. Parse quantity
        raw_qty_str = data.get('quantity', '0').replace(',', '')
        try:
            raw_qty = Decimal(raw_qty_str)
        except InvalidOperation:
            raise ValidationError(f"Invalid quantity numeric format: '{raw_qty_str}'")

        # 2. Parse date
        posting_date_str = data.get('posting_date')
        try:
            activity_date = parse_date(posting_date_str)
            if not activity_date:
                raise ValidationError("Posting date (BEDAT) is empty.")
        except Exception as e:
            raise ValidationError(f"Date parsing failed: {str(e)}")

        # 3. Handle fuel mapping
        raw_fuel = data.get('fuel_type', '').upper()
        
        category = 'Other Procurement'
        scope = 'SCOPE_3' # Default for general materials
        
        fuel_mappings = {
            'DIESEL': ('Diesel Fuel', 'SCOPE_1'),
            'HEIZOEL': ('Heating Oil', 'SCOPE_1'),
            'HEATING OIL': ('Heating Oil', 'SCOPE_1'),
            'ERDGAS': ('Natural Gas', 'SCOPE_1'),
            'NATURAL GAS': ('Natural Gas', 'SCOPE_1'),
            'PETROL': ('Motor Gasoline', 'SCOPE_1'),
            'GASOLINE': ('Motor Gasoline', 'SCOPE_1'),
            'GASOIL': ('Diesel Fuel', 'SCOPE_1'),
        }
        
        matched_fuel = None
        for key, val in fuel_mappings.items():
            if key in raw_fuel:
                category, scope = val
                matched_fuel = key
                break
        
        if not matched_fuel:
            if 'FUEL' in raw_fuel:
                category = 'Gasoil / Fuel'
                scope = 'SCOPE_1'

        # 4. Unit normalization
        raw_unit = data.get('unit', '').upper()
        norm_qty = raw_qty
        norm_unit = raw_unit
        
        if scope == 'SCOPE_1':
            if raw_unit in ['L', 'LTR', 'LIT', 'LITER', 'LITERS']:
                norm_qty = raw_qty
                norm_unit = 'Liters'
            elif raw_unit in ['GAL', 'GALLON', 'GALLONS', 'GL']:
                norm_qty = raw_qty * Decimal('3.78541')
                norm_unit = 'Liters'
            elif raw_unit in ['KG', 'KILOGRAM', 'KILOGRAMS']:
                norm_qty = raw_qty
                norm_unit = 'kg'
            elif raw_unit in ['TO', 'TON', 'TONNE', 'TONNES', 'T']:
                norm_qty = raw_qty * Decimal('1000')
                norm_unit = 'kg'
            elif raw_unit in ['M3', 'CUBIC_METER', 'M³']:
                norm_qty = raw_qty
                norm_unit = 'm3'
            else:
                flags.append(f"Unrecognized fuel unit '{raw_unit}', no conversion applied.")
        else:
            if raw_unit in ['TO', 'TON', 'TONNE', 'TONNES']:
                norm_qty = raw_qty * Decimal('1000')
                norm_unit = 'kg'
            elif raw_unit in ['KG', 'KILOGRAM', 'KILOGRAMS']:
                norm_qty = raw_qty
                norm_unit = 'kg'
            else:
                norm_unit = raw_unit.lower()

        # Heuristics
        if raw_qty < 0:
            flags.append("Negative quantity detected.")
        elif raw_qty == 0:
            flags.append("Zero quantity detected.")
        
        plant_code = data.get('plant_code')
        if not plant_code:
            flags.append("Missing plant code (WERKS).")
        elif plant_code not in KNOWN_PLANTS:
            flags.append(f"Unknown plant code '{plant_code}'.")

        if scope == 'SCOPE_1':
            if norm_unit == 'Liters' and norm_qty > 50000:
                flags.append(f"Abnormally high fuel quantity: {norm_qty:.2f} Liters.")
            elif norm_unit == 'kg' and norm_qty > 20000:
                flags.append(f"Abnormally high fuel mass: {norm_qty:.2f} kg.")

        review_state = 'FLAGGED' if flags else 'INGESTED'
        
        activity = NormalizedActivity.objects.create(
            organization=self.org,
            raw_record=raw_record,
            job=self.job,
            activity_date=activity_date,
            activity_category=category,
            emissions_scope=scope,
            raw_quantity=raw_qty,
            raw_unit=raw_unit,
            normalized_quantity=norm_qty,
            normalized_unit=norm_unit,
            review_state=review_state,
            flags=flags
        )

        raw_record.status = 'FLAGGED' if flags else 'NORMALIZED'
        raw_record.save()

        AuditTrail.objects.create(
            activity=activity,
            user=self.job.uploaded_by,
            action='REJECT' if flags else 'CREATE',
            notes="Auto-normalized from SAP OData file." + (f" Warnings: {', '.join(flags)}" if flags else "")
        )


class UtilityParser(BaseParser):
    # Aligned to Green Button CSV specs
    HEADER_ALIASES = {
        'meter_id': ['service_point_id', 'meter_id', 'meter_number', 'AccountNumber', 'MeterID'],
        'billing_start': ['billing_period_start', 'billing_start', 'start_date', 'BillStartDate'],
        'billing_end': ['billing_period_end', 'billing_end', 'end_date', 'BillEndDate'],
        'consumption': ['kwh_consumed', 'consumption', 'usage', 'Usage'],
        'unit': ['unit', 'Unit', 'UnitOfMeasure'],
        'tariff_type': ['tariff', 'tariff_type', 'Tariff'],
        'facility_name': ['facility_name', 'facility', 'ServiceAddress'],
        'date': ['date', 'reading_date']
    }

    def resolve_headers(self, headers):
        resolved = {}
        for internal_name, aliases in self.HEADER_ALIASES.items():
            for alias in aliases:
                matching_header = next((h for h in headers if h.strip().lower() == alias.lower()), None)
                if matching_header:
                    resolved[internal_name] = matching_header
                    break
        return resolved

    def parse_and_normalize(self):
        content = self.job.raw_file_content
        reader = csv.reader(content.splitlines())
        
        try:
            headers = next(reader)
        except StopIteration:
            raise ValidationError("The uploaded CSV is empty.")

        resolved_headers = self.resolve_headers(headers)
        
        # In Green Button, unit can be implicit (kWh) based on the column name "kwh_consumed"
        required_fields = ['meter_id', 'billing_start', 'billing_end', 'consumption']
        missing_fields = [f for f in required_fields if f not in resolved_headers]
        if missing_fields:
            raise ValidationError(f"Missing required CSV columns: {', '.join(missing_fields)}. Checked headers: {headers}")

        row_idx = 1
        for row in reader:
            row_idx += 1
            if not row or not any(field.strip() for field in row):
                continue
            
            row_data = {}
            for key, file_header in resolved_headers.items():
                try:
                    idx = headers.index(file_header)
                    row_data[key] = row[idx].strip() if idx < len(row) else ''
                except ValueError:
                    row_data[key] = ''

            raw_record = RawRecord.objects.create(
                job=self.job,
                row_index=row_idx,
                raw_data=row_data,
                status='UNPROCESSED'
            )

            try:
                self.normalize_row(raw_record)
            except Exception as e:
                raw_record.status = 'ERROR'
                raw_record.error_message = str(e)
                raw_record.save()

    def normalize_row(self, raw_record: RawRecord):
        data = raw_record.raw_data
        flags = []

        # 1. Parse Consumption
        raw_consumption_str = data.get('consumption', '0').replace(',', '')
        try:
            raw_qty = Decimal(raw_consumption_str)
        except InvalidOperation:
            raise ValidationError(f"Invalid consumption numeric format: '{raw_consumption_str}'")

        # 2. Parse billing dates
        start_date_str = data.get('billing_start')
        end_date_str = data.get('billing_end')
        try:
            start_date = parse_date(start_date_str)
            end_date = parse_date(end_date_str)
            if not start_date or not end_date:
                raise ValidationError("Billing cycle dates are missing.")
        except Exception as e:
            raise ValidationError(f"Date parsing failed: {str(e)}")

        # 3. Unit normalization (implicit to kWh for Green Button, supports other if explicit)
        raw_unit = data.get('unit', 'kWh')
        if not raw_unit or raw_unit.strip() == '':
            raw_unit = 'kWh'
        
        raw_unit_upper = raw_unit.upper()
        norm_qty = raw_qty
        norm_unit = 'kWh'

        if 'MWH' in raw_unit_upper:
            norm_qty = raw_qty * Decimal('1000')
        elif 'WH' in raw_unit_upper and 'K' not in raw_unit_upper:
            norm_qty = raw_qty / Decimal('1000')

        # 4. Resolve date (if reading date column exists, use it; otherwise use cycle midpoint)
        reading_date_str = data.get('date')
        try:
            reading_date = parse_date(reading_date_str) if reading_date_str else None
        except Exception:
            reading_date = None

        total_days = (end_date - start_date).days
        if total_days <= 0:
            flags.append(f"Invalid billing cycle: start date {start_date} is after/same as end date {end_date}.")
            activity_date = end_date
        else:
            activity_date = reading_date if reading_date else start_date + (end_date - start_date) / 2
            if total_days > 45:
                flags.append(f"Abnormally long billing period: {total_days} days.")
            elif total_days < 15:
                flags.append(f"Abnormally short billing period: {total_days} days.")

        if raw_qty < 0:
            flags.append("Negative electricity usage detected.")
        elif raw_qty == 0:
            flags.append("Zero electricity usage detected.")
        elif norm_qty > 100000:
            flags.append(f"Extremely high electricity usage: {norm_qty:.2f} kWh.")

        meter_id = data.get('meter_id')
        if not meter_id:
            flags.append("Missing meter reference (service_point_id).")

        review_state = 'FLAGGED' if flags else 'INGESTED'
        
        activity = NormalizedActivity.objects.create(
            organization=self.org,
            raw_record=raw_record,
            job=self.job,
            activity_date=activity_date,
            activity_start_date=start_date,
            activity_end_date=end_date,
            activity_category='Purchased Electricity',
            emissions_scope='SCOPE_2',
            raw_quantity=raw_qty,
            raw_unit=raw_unit,
            normalized_quantity=norm_qty,
            normalized_unit=norm_unit,
            review_state=review_state,
            flags=flags
        )

        raw_record.status = 'FLAGGED' if flags else 'NORMALIZED'
        raw_record.save()

        AuditTrail.objects.create(
            activity=activity,
            user=self.job.uploaded_by,
            action='REJECT' if flags else 'CREATE',
            notes="Auto-normalized from Green Button CSV file." + (f" Warnings: {', '.join(flags)}" if flags else "")
        )


class TravelParser(BaseParser):
    # Parse Concur Itinerary API JSON schema
    def parse_and_normalize(self):
        content = self.job.raw_file_content
        try:
            trips = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Failed to parse JSON file content: {str(e)}")

        if not isinstance(trips, list):
            if isinstance(trips, dict):
                trips = [trips]
            else:
                raise ValidationError("JSON content must be an array of trip records.")

        row_idx = 0
        for trip in trips:
            row_idx += 1
            
            raw_record = RawRecord.objects.create(
                job=self.job,
                row_index=row_idx,
                raw_data=trip,
                status='UNPROCESSED'
            )

            try:
                self.normalize_trip(raw_record)
            except Exception as e:
                raw_record.status = 'ERROR'
                raw_record.error_message = str(e)
                raw_record.save()

    def normalize_trip(self, raw_record: RawRecord):
        trip = raw_record.raw_data
        flags = []

        # Realigned identifiers to trip_id
        trip_id = trip.get('trip_id') or trip.get('employee_id')
        if not trip_id:
            flags.append("Missing trip/employee reference.")

        booking_date_str = trip.get('date') or trip.get('booking_date') or trip.get('trip_start_date')
        try:
            activity_date = parse_date(booking_date_str)
            if not activity_date:
                raise ValidationError("Trip booking date is missing.")
        except Exception as e:
            raise ValidationError(f"Date parsing failed: {str(e)}")

        segments = trip.get('segments', [])
        if not segments:
            raise ValidationError("Trip has no segments listed.")

        # Realigned mapping attributes (origin, destination, cabin, miles, type)
        # We aggregate multiple segments from a single Concur trip by category
        for seg_idx, segment in enumerate(segments):
            seg_type = segment.get('type', 'flight').lower()
            
            # Sub-category classification
            category = 'Business Travel'
            norm_unit = ''
            norm_qty = Decimal('0')
            raw_qty = Decimal('0')
            raw_unit = ''
            
            passengers = int(segment.get('passengers', 1) or 1)
            
            if seg_type in ['flight', 'air']:
                category = 'Business Travel - Flights'
                norm_unit = 'p-km'
                raw_unit = 'miles'
                
                miles_val = segment.get('miles')
                orig = segment.get('origin', segment.get('StartCityCode', '')).upper().strip()
                dest = segment.get('destination', segment.get('EndCityCode', '')).upper().strip()
                
                if orig and dest and orig == dest:
                    flags.append(f"Segment #{seg_idx+1}: Flight has same origin and destination: {orig}.")
                
                dist_miles = Decimal('0')
                if not miles_val or Decimal(str(miles_val)) <= 0:
                    # Resolve coordinates
                    if orig in AIRPORT_COORDINATES and dest in AIRPORT_COORDINATES:
                        lat1, lon1 = AIRPORT_COORDINATES[orig]
                        lat2, lon2 = AIRPORT_COORDINATES[dest]
                        calculated_dist_km = calculate_haversine(lat1, lon1, lat2, lon2)
                        dist_miles = Decimal(str(round(calculated_dist_km * 0.621371, 2)))
                    else:
                        default_d = Decimal('621.37') # 1000 km in miles
                        dist_miles = default_d
                        flags.append(f"Segment #{seg_idx+1}: Airport code pair '{orig}'->'{dest}' not found in lookup. Applied default.")
                else:
                    dist_miles = Decimal(str(miles_val))

                # Class multiplier (realigned to 'cabin')
                cabin_class = segment.get('cabin', trip.get('booking_class', 'Economy')).lower()
                multiplier = Decimal('1.0')
                if 'business' in cabin_class:
                    multiplier = Decimal('1.5')
                elif 'first' in cabin_class or 'premium' in cabin_class:
                    multiplier = Decimal('2.0')

                # Passenger miles = miles * passengers
                raw_qty = dist_miles * passengers
                # Normalize unit p-km (miles * 1.60934)
                norm_qty = raw_qty * Decimal('1.609344') * multiplier
                
                if norm_qty <= 0:
                    flags.append(f"Segment #{seg_idx+1}: Zero travel distance calculated.")
                elif norm_qty > 25000:
                    flags.append(f"Segment #{seg_idx+1}: Abnormally long travel distance: {norm_qty:.2f} p-km.")

            elif seg_type in ['hotel', 'lodge']:
                category = 'Business Travel - Hotels'
                norm_unit = 'room-nights'
                raw_unit = 'nights'
                
                nights = segment.get('nights') or segment.get('hotel_nights') or trip.get('hotel_nights')
                try:
                    raw_qty = Decimal(str(nights or 0))
                except InvalidOperation:
                    raw_qty = Decimal('0')
                
                norm_qty = raw_qty
                
                if norm_qty <= 0:
                    flags.append(f"Segment #{seg_idx+1}: Hotel stay has zero nights.")
                elif norm_qty > 30:
                    flags.append(f"Segment #{seg_idx+1}: Abnormally long hotel stay: {norm_qty} nights.")

            elif seg_type in ['car', 'ride', 'ground']:
                category = 'Business Travel - Car Rental'
                norm_unit = 'v-km'
                raw_unit = 'miles'
                
                miles_val = segment.get('miles') or segment.get('distance_km') or trip.get('distance_km')
                try:
                    raw_qty = Decimal(str(miles_val or 0))
                except InvalidOperation:
                    raw_qty = Decimal('0')
                    
                # Convert miles to v-km
                norm_qty = raw_qty * Decimal('1.609344')
                
                if norm_qty <= 0:
                    flags.append(f"Segment #{seg_idx+1}: Car rental distance is zero.")

            elif seg_type == 'rail':
                category = 'Business Travel - Rail'
                norm_unit = 'p-km'
                raw_unit = 'miles'
                
                miles_val = segment.get('miles') or segment.get('distance_km') or trip.get('distance_km')
                try:
                    raw_qty = Decimal(str(miles_val or 0))
                except InvalidOperation:
                    raw_qty = Decimal('0')
                    
                raw_qty = raw_qty * passengers
                norm_qty = raw_qty * Decimal('1.609344')
                
                if norm_qty <= 0:
                    flags.append(f"Segment #{seg_idx+1}: Rail distance is zero.")

            else:
                raise ValidationError(f"Unrecognized travel booking type: '{seg_type}'")

            # Create NormalizedActivity for each travel segment
            review_state = 'FLAGGED' if flags else 'INGESTED'
            
            activity = NormalizedActivity.objects.create(
                organization=self.org,
                raw_record=raw_record,
                job=self.job,
                activity_date=activity_date,
                activity_category=category,
                emissions_scope='SCOPE_3',
                raw_quantity=raw_qty,
                raw_unit=raw_unit,
                normalized_quantity=norm_qty,
                normalized_unit=norm_unit,
                review_state=review_state,
                flags=flags
            )

            raw_record.status = 'FLAGGED' if flags else 'NORMALIZED'
            raw_record.save()

            AuditTrail.objects.create(
                activity=activity,
                user=self.job.uploaded_by,
                action='REJECT' if flags else 'CREATE',
                notes=f"Auto-normalized Concur Segment #{seg_idx+1} ({seg_type})." + (f" Warnings: {', '.join(flags)}" if flags else "")
            )
