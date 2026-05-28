from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import datetime

from ingestion.models import Organization, User, IngestionJob, RawRecord, NormalizedActivity, AuditTrail
from ingestion.parsers import SAPParser, UtilityParser, TravelParser

class ESGPrototypeTestCase(TestCase):
    def setUp(self):
        # Set up Organization and User
        self.org = Organization.objects.create(name="Test Org")
        self.other_org = Organization.objects.create(name="Other Org")
        
        self.user = User.objects.create_user(
            username="testanalyst",
            email="test@test.com",
            password="password123",
            organization=self.org
        )
        self.other_user = User.objects.create_user(
            username="otheranalyst",
            email="other@test.com",
            password="password123",
            organization=self.other_org
        )

    def test_sap_parser_normal(self):
        # 1. Normal SAP OData Data
        csv_content = (
            "EBELN,EBELP,MATNR,MENGE,MEINS,WERKS,LIFNR,BEDAT,NETWR,WAERS\n"
            "PO100001,0001,DIESEL,1000,L,1020,VEND-01,2026-05-15,3500.00,EUR"
        )
        job = IngestionJob.objects.create(
            organization=self.org,
            uploaded_by=self.user,
            source_type='SAP',
            filename='sap_normal.csv',
            raw_file_content=csv_content,
            status='PENDING'
        )
        parser = SAPParser(job)
        parser.run()
        
        job.refresh_from_db()
        self.assertEqual(job.status, 'COMPLETED')
        self.assertEqual(job.raw_records.count(), 1)
        
        raw_record = job.raw_records.first()
        self.assertEqual(raw_record.status, 'NORMALIZED')
        
        activity = raw_record.normalized_activity
        self.assertEqual(activity.activity_category, 'Diesel Fuel')
        self.assertEqual(activity.emissions_scope, 'SCOPE_1')
        self.assertEqual(activity.normalized_quantity, Decimal('1000.0000'))
        self.assertEqual(activity.normalized_unit, 'Liters')
        self.assertEqual(activity.review_state, 'INGESTED')

    def test_sap_parser_german_headers_and_anomalies(self):
        # 2. SAP Data with German headers, negative quantity, unknown plant
        csv_content = (
            "WERKS,MATNR,MENGE,MEINS,BEDAT,LIFNR\n"
            "PL99,DIESEL,-500,GAL,12.05.2026,VEND-01"
        )
        job = IngestionJob.objects.create(
            organization=self.org,
            uploaded_by=self.user,
            source_type='SAP',
            filename='sap_anomaly.csv',
            raw_file_content=csv_content,
            status='PENDING'
        )
        parser = SAPParser(job)
        parser.run()
        
        raw_record = job.raw_records.first()
        self.assertEqual(raw_record.status, 'FLAGGED')
        
        activity = raw_record.normalized_activity
        self.assertEqual(activity.review_state, 'FLAGGED')
        # Gallons conversion: -500 * 3.78541 = -1892.705
        self.assertAlmostEqual(float(activity.normalized_quantity), -1892.705, places=2)
        
        # Verify flags
        self.assertIn("Negative quantity detected.", activity.flags)
        self.assertIn("Unknown plant code 'PL99'.", activity.flags)

    def test_utility_parser_mwh_and_split(self):
        # Utility Data with MWh and Green Button CSV columns
        csv_content = (
            "date,kwh_consumed,meter_reading,tariff,billing_period_start,billing_period_end,service_point_id,unit\n"
            "2026-04-15,10,45678,E-COMM,2026-04-01,2026-04-30,MET-123,MWh"
        )
        job = IngestionJob.objects.create(
            organization=self.org,
            uploaded_by=self.user,
            source_type='UTILITY',
            filename='utility.csv',
            raw_file_content=csv_content,
            status='PENDING'
        )
        parser = UtilityParser(job)
        parser.run()
        
        activity = NormalizedActivity.objects.get(job=job)
        self.assertEqual(activity.emissions_scope, 'SCOPE_2')
        self.assertEqual(activity.activity_category, 'Purchased Electricity')
        # 10 MWh = 10000 kWh
        self.assertEqual(activity.normalized_quantity, Decimal('10000.0000'))
        self.assertEqual(activity.normalized_unit, 'kWh')
        # date is explicitly provided
        self.assertEqual(activity.activity_date, datetime.date(2026, 4, 15))

    def test_travel_parser_missing_distance_haversine(self):
        # Travel trip with missing distance JFK -> LHR, Business class, 2 passengers
        travel_json = """[
            {
                "trip_id": "trip-001",
                "date": "2026-05-01",
                "segments": [
                    {
                        "type": "flight",
                        "origin": "JFK",
                        "destination": "LHR",
                        "cabin": "Business",
                        "miles": null,
                        "passengers": 2
                    }
                ]
            }
        ]"""
        job = IngestionJob.objects.create(
            organization=self.org,
            uploaded_by=self.user,
            source_type='TRAVEL',
            filename='travel.json',
            raw_file_content=travel_json,
            status='PENDING'
        )
        parser = TravelParser(job)
        parser.run()
        
        # JFK -> LHR Haversine is ~5585 km
        # Convert to miles: ~3470 miles
        # Passengers: 2 -> raw miles = ~6940
        # Convert back to km: ~11170 p-km
        # Business multiplier is 1.5 -> total normalized ~16755 p-km
        activity = NormalizedActivity.objects.get(job=job)
        self.assertEqual(activity.emissions_scope, 'SCOPE_3')
        self.assertEqual(activity.activity_category, 'Business Travel - Flights')
        
        self.assertGreater(activity.normalized_quantity, Decimal('15000'))
        self.assertLess(activity.normalized_quantity, Decimal('18000'))
        self.assertEqual(activity.normalized_unit, 'p-km')
        self.assertEqual(activity.review_state, 'INGESTED')

    def test_audit_locking_immutability(self):
        # Create a locked activity and check it cannot be edited or deleted
        csv_content = "EBELN,EBELP,MATNR,MENGE,MEINS,WERKS,LIFNR,BEDAT\nPO1,01,DIESEL,100,L,1020,VEND-01,2026-05-15"
        job = IngestionJob.objects.create(
            organization=self.org, uploaded_by=self.user, source_type='SAP',
            filename='sap_lock.csv', raw_file_content=csv_content, status='PENDING'
        )
        SAPParser(job).run()
        
        activity = NormalizedActivity.objects.get(job=job)
        activity.review_state = 'APPROVED'
        activity.save()
        
        # Lock the activity
        activity.review_state = 'LOCKED'
        activity.save()
        
        # Try to modify the quantity
        activity.normalized_quantity = Decimal('999')
        with self.assertRaises(ValidationError):
            activity.save()
            
        # Try to delete
        with self.assertRaises(ValidationError):
            activity.delete()
