# Design Decisions & Ambiguities Resolved (DECISIONS.md)

This document catalogs key product ambiguities, option matrices, and integrations resolutions applied for the prototype, along with prepared Product Manager questions.

---

## 1. Data Source Format Decisions & Tradeoffs

### Source 1: SAP Fuel & Procurement Data

| Option | Pros | Cons | Best For |
| :--- | :--- | :--- | :--- |
| **OData (REST/JSON) [Chosen]** | - Technical technical names (`WERKS`, `MENGE`) ignore localized headers.<br>- Standard RESTful HTTP + JSON support.<br>- Built-in pagination (`$skip`, `$top`). | - Requires SAP Gateway configuration. | API-based multi-tenant SaaS platforms requiring structured automation. |
| **IDoc (Intermediate Document)** | - Built-in async processing tracking.<br>- Reprocessable via standard transaction `BD87`. | - Legacy technology, complex nested XML schemas.<br>- High middleware overhead. | Large scale EDI/B2B supplier pipelines. |
| **Flat File (CSV/Excel)** | - Simple manual download via standard reports (`MB51`/`ME2N`). | - Brittle automation, inconsistent layouts.<br>- Localized language headers (German vs English). | Ad-hoc imports or manual uploads. |
| **BAPI (RFC Function)** | - Direct access to transaction functions. | - Requires SAP JCo native connectors.<br>- Boilerplate-heavy. | Dedicated desktop/local application integrations. |

* **Decision**: We simulated **OData (REST/JSON) Flat Exports** using a standardized technical column layout: `EBELN, EBELP, MATNR, MENGE, MEINS, WERKS, LIFNR, BEDAT, NETWR, WAERS`. This avoids localized language headers and ensures direct database traceability.

---

### Source 2: Utility Electricity Data

| Option | Pros | Cons | Best For |
| :--- | :--- | :--- | :--- |
| **Green Button CSV [Chosen]** | - Standardized energy consumption schema.<br>- Easy portal export for facility teams.<br>- Handles flexible interval dates. | - Schema variations by utility provider. | Client facility-led imports with zero custom integrations. |
| **Green Button XML** | - Standardized XML schema (NAESB ESPI). | - Parsing complex Atom streams is overkill for monthly usage. | Automated utility-to-system integrations. |
| **PDF Bill** | - Universally available. | - OCR pipelines are brittle and prone to transcription errors. | Manual backup reference only. |
| **Utility API** | - Real-time automated sync. | - Rare, vendor-specific (each utility has a different API). | Direct smart-meter platforms. |

* **Decision**: We adopted the **Green Button CSV** format. It provides a structured, automated-friendly layout using technical columns (`date, kwh_consumed, meter_reading, tariff, billing_period_start, billing_period_end, service_point_id`). PDF scanning via OCR was rejected as it is error-prone, which is unacceptable for audit integrity.

---

### Source 3: Corporate Travel Data (Concur)

| Option | Pros | Cons | Best For |
| :--- | :--- | :--- | :--- |
| **Concur API v4 (JSON) [Chosen]** | - Direct structured JSON access.<br>- Standardized flight, car, hotel nodes.<br>- Pre-calculated carbon fields (`CarbonEmissionLbs`). | - OAuth authentication setup.<br>- Historical query limits (6 months). | Automated real-time corporate travel ingestion. |
| **Concur CSV Export** | - Manual download from portal. | - Columns change per customer configuration. | Ad-hoc historical reporting. |
| **Manual Paste** | - No integrations needed. | - Slow, unscalable, prone to human error. | Testing and sandbox setups. |

* **Decision**: We adopted the **Concur Itinerary JSON schema**, parsing nested segments (`type, origin, destination, cabin, miles, passengers, nights`). It allows direct mapping of transport distance (passenger-miles converted to p-km), cabin multipliers, and hotel stay room-nights.

---

## 2. Technical Ambiguities Resolved

### Billing Period Splits (Utility Data)
* **Ambiguity**: Electricity billing cycles do not align to calendar months. If a bill is from Dec 15 to Jan 14, how should the emissions ledger represent the date?
* **Resolution**: We store both `activity_start_date` and `activity_end_date` in the database. For the main ledger date (`activity_date`), we compute the mid-point of the period. The normalization engine also tracks daily average consumption (`consumption / total_days`), which enables future reporting systems to split the usage proportionally into monthly buckets.

### Travel Distance Failures (Corporate Travel Data)
* **Ambiguity**: Travel booking data from APIs (Concur/Navan) often has missing distance values (`distance_km = null`), only providing origin and destination airport codes.
* **Resolution**: We implemented an airport coordinate database containing coordinates for 20 major international airport hubs. When the API payload lacks distances, the normalization engine uses the Haversine formula to compute the great-circle distance between coordinates. If a code is not in the database, it applies a default fallback distance of 1,000 km and generates a warning flag (`"Airport code pair not found, applied default 1000 km"`).

### German Header Mappings (SAP Data)
* **Ambiguity**: SAP exports vary wildly in language configurations, columns can be German or English.
* **Resolution**: We built an alias-mapping lookup dictionary that resolves German column headers (`WERKS`, `MATNR`, `MENGE`, `MEINS`, `BUDAT`, `KOSTL`, `LIFNR`) to internal normalized attributes. The parser checks all headers case-insensitively, supporting both languages seamlessly.

---

## 3. Questions for the Product Manager

1. **How should we handle Currency Conversion?** 
   SAP procurement exports include cost columns in multiple currencies (EUR, USD, GBP). Should the ledger integrate with an exchange rate API to normalize procurement costs to a base currency before applying spend-based Scope 3 factors?
2. **What is the source of truth for Facility Mapping?**
   SAP uses plant codes (`WERKS`), while Utility data uses meter IDs (`meter_id`). We need a master asset hierarchy. Should we build a "Facilities Directory" in CHI-CHA that maps plant codes and meter IDs to a single corporate building asset?
3. **What workflow permissions are needed for Locking?**
   Should an Analyst have permission to lock their own records, or should locking require an "ESG Operations Manager" or "Lead Auditor" approval role (four-eyes principle)?