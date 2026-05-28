# Data Source Research & Realities (SOURCES.md)

This document details the real-world research behind each of the three corporate systems, documents the specific schemas chosen, and maps out actual failure vectors in production.

---

## 1. SAP Fuel & Procurement Data

### Real-World Format Researched
We researched SAP Gateway Service exports, exposing database tables like **EKKO** (PO Header), **EKPO** (PO Items), and **MARA** (Material Master) through **OData REST endpoints**.

### What We Learned
- **Technical Column Names**: Direct API access via OData avoids language-dependent Excel headers by exposing standardized technical fields (`EBELN` for PO, `EBELP` for Item, `MATNR` for Material, `MENGE` for Quantity, `MEINS` for Unit, `WERKS` for Plant).
- **Unit Chaos**: Standard SAP tables (`T006`) define internal base units, but operations record transactions in local units (e.g. Liter `L`, Gallon `GAL`, or metric Tonne `TO`).
- **Plant Mapping**: Plant codes (`WERKS`) are short strings (e.g. `1020`) that represent specific buildings or factory sites. They require lookups from table `T001W` to get the geographical facility location.

### Sample Data & Anomaly Design (sample_sap.csv)
Our [sample_sap.csv](./sample_files/sample_sap.csv) simulates an OData-driven flat export containing:
- `EBELN,EBELP,MATNR,MENGE,MEINS,WERKS,LIFNR,BEDAT,NETWR,WAERS`
- Real-world plant codes (`1020`, `3150`) and materials mapping to Scope 1 fuels (`DIESEL_FUEL`, `HEIZOEL`) or Scope 3 procurement (`STEEL_PLATES`).
- Anomaly lines: Negative quantity (`-500`), unregistered plant code (`PL99`), and fuel transaction outlier (`85000` L).

### Real-World Failure Vectors
- **Missing Material Mapping**: New materials added in SAP GUI without corresponding category flags will fail to resolve Scope classification (Scope 1 vs 3).
- **Missing Master Data**: Joining transaction lines (`EKPO`) to material master (`MARA`) will fail if the material number does not exist.

---

## 2. Utility Electricity Data

### Real-World Format Researched
We researched commercial invoices and Green Button portal CSV downloads (mandated by NAESB ESPI standards).

### What We Learned
- **Rolling Billing Cycles**: Utility billing cycles represent dates like the 12th to the 11th, meaning consumption overlaps calendar months.
- **Service Point Identifiers**: Facilities utilize unique Meter IDs / Service Point IDs (`service_point_id`) to track power consumption.
- **Consumption Units**: Scale changes from `Wh` to `MWh` depending on commercial building sizes.

### Sample Data & Anomaly Design (sample_utility.csv)
Our [sample_utility.csv](./sample_files/sample_utility.csv) contains:
- `date,kwh_consumed,meter_reading,tariff,billing_period_start,billing_period_end,service_point_id`
- MWh-to-kWh unit mapping, billing cycle cycles, and tariff rate codes (`T1`).
- Anomaly lines: Inverted date boundaries, negative electricity usage (`-200`), and industrial usage outlier (`150000` kWh).

### Real-World Failure Vectors
- **Overlapping/Duplicate Cycles**: If teams upload duplicate bills for the same Service Point ID, the system will double-count electricity consumption.
- **Estimated Reading Flags**: Utility portal exports flag readings as "Actual" or "Estimated". If estimated readings are not marked, it degrades audit confidence.

---

## 3. Corporate Travel Data (Concur)

### Real-World Format Researched
We researched **SAP Concur Itinerary v4 REST API** payloads.

### What We Learned
- **Nested Itineraries**: Concur payloads represent travel requests containing nested lists of segments (flights, hotel stays, rental cars, rail).
- **Flight Distance Estimation**: Distance metrics (`miles`) are frequently missing. In real deployments, systems must resolve airport IATA codes (`origin`, `destination`) via distance lookups to compute great-circle mileage.
- **Cabin Multipliers**: Emissions calculations scale by cabin class (`cabin` field) as business and first-class seats take up more physical space and weight allocation (applying multipliers 1.5x and 2x).

### Sample Data & Anomaly Design (sample_travel.json)
Our [sample_travel.json](./sample_files/sample_travel.json) models a nested Concur API structure:
- Fields: `trip_id`, `date`, `segments` with `type, origin, destination, cabin, miles, passengers, nights`.
- Flight segment with missing miles between `JFK` and `LHR` (triggers coordinate distance lookup).
- Hotel segment with stay duration defined via `nights`.
- Anomaly lines: Flight segment with same origin/destination, abnormally long hotel stay (45 nights), and rental car segment with zero miles.

### Real-World Failure Vectors
- **Multi-passenger Bookings**: If passenger counts (`passengers`) are missing or incorrectly assumed, total passenger-miles will be skewed.
- **New IATA Codes**: Small municipal airports or newly established airfields will fail the Coordinate lookup dictionary, requiring default fallbacks.