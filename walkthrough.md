# Walkthrough - Enterprise ESG Data Ingestion & Audit Review Prototype (Django & React)

We have implemented a full-featured, zero-configuration ESG Data Ingestion & Audit Review prototype in Django and React, aligned with the requirements in `ceoss_check.txt`. All core requirements, including multi-tenancy, raw-normalized data segregation, custom robust parsing, workflow approvals, and audit log immutability, are fully operational in the `backend/` and `frontend/` folders.

---

## Technical Stack & Architecture

- **Backend**: [Django REST Framework](https://www.django-rest-framework.org/) running on local development port `8000`.
- **Frontend**: [React + Vite + TypeScript](https://vite.dev/) running on local development port `5173`.
- **Styling**: Vanilla CSS with a custom high-end glassmorphic dark theme (`frontend/src/index.css`).
- **Database**: SQLite (`backend/db.sqlite3`) storing tables for:
  - `Organization` (Multi-tenant isolation)
  - `User` (Custom AbstractUser supporting simulator roles: Analyst, Manager, Administrator)
  - `IngestionJob` (History and logs of parsed upload transactions)
  - `RawRecord` (Immutable raw provenance payloads tied to line index)
  - `NormalizedActivity` (Normalized records with audit states: Ingested, Flagged, Approved, Locked)
  - `AuditTrail` (Chronological edit/approval histories with before/after diff states)
- **Robust Parsers**: Custom parsers implemented in `backend/ingestion/parsers.py` for each of the three sources, handling real-world shapes, inconsistent units, German column headers, billing periods, and travel coordinates.

---

## File Structure

The Django + React project has been organized into separate directories:

### Backend (`backend/`)
- [backend/ingestion/models.py](file:///c:/Users/gagan/OneDrive/projects/CHI-CHA/backend/ingestion/models.py): Relational database models scoped for multi-tenancy, audit logging, and immutability.
- [backend/ingestion/parsers.py](file:///c:/Users/gagan/OneDrive/projects/CHI-CHA/backend/ingestion/parsers.py): Ingestion parsers (`SAPParser`, `UtilityParser`, `TravelParser`) with unit conversions, midpoint utility dates, airport coordinates lookup, and suspicious flags.
- [backend/ingestion/views.py](file:///c:/Users/gagan/OneDrive/projects/CHI-CHA/backend/ingestion/views.py): REST ViewSets scoped by user organization, supporting approve/flag/edit/lock workflows.
- [backend/seed_data.py](file:///c:/Users/gagan/OneDrive/projects/CHI-CHA/backend/seed_data.py): DB seeder creating simulated users for review workflows.
- [backend/ingestion/tests.py](file:///c:/Users/gagan/OneDrive/projects/CHI-CHA/backend/ingestion/tests.py): Django unit test suite verifying parsers, conversions, date mapping, and immutability.

### Frontend (`frontend/`)
- [frontend/src/App.tsx](file:///c:/Users/gagan/OneDrive/projects/CHI-CHA/frontend/src/App.tsx): Dashboard interface (dark mode, glassmorphic layout, upload wizard, filtering, side-by-side trace drawer, and edit justification controls).
- [frontend/src/index.css](file:///c:/Users/gagan/OneDrive/projects/CHI-CHA/frontend/src/index.css): Beautiful custom variables and layouts.

---

## Verification Results

We verified the entire system through automated tests and manual script simulation.

### 1. Automated Backend Unit Tests
We executed the Django test suite containing 5 comprehensive test cases covering:
- Normal SAP csv ingestion and Scope 1 diesel normalization.
- SAP anomaly detection (negative quantities, unknown plant codes) and German header mapping.
- Utility electricity MWh-to-kWh conversions and billing period midpoint calculations.
- Corporate travel flight distance resolution via Haversine and cabin class multipliers.
- Immutability enforcement of `LOCKED` records.

All tests compile and pass successfully:
```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.....
----------------------------------------------------------------------
Ran 5 tests in 5.208s

OK
Destroying test database for alias 'default'...
```

### 2. Manual Verification & User Interface
When accessing the frontend client dashboard, users can experience the full analyst workspace:
- **Authentication Simulation**: Login page seeds simulated accounts (e.g. `analyst` / `analyst123`, `manager` / `manager123`).
- **Data Ingestion Center**: Drop-zone to select file origins (SAP / Utility / Travel) and upload raw files.
- **Traceability Inspector**: Clicking a ledger row displays the detailed record information side-by-side with its exact raw record JSON payload and line-index reference from the source file.
- **Audit Trails**: Modals force analysts to write correction justifications before editing data, immediately appending audit log records.
- **Audit Locking**: APPROVED rows become completely immutable after locking, throwing ValidationErrors on subsequent edit/delete attempts.