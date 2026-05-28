# Product Requirements Document (PRD)

# Project

Enterprise ESG Data Ingestion & Audit Review Prototype

# Objective

Build a prototype platform that ingests sustainability-related operational data from heterogeneous enterprise systems, normalizes the data into a unified emissions activity model, and enables analysts to review, validate, approve, and lock records for audit readiness.

The prototype should demonstrate realistic handling of enterprise data complexity rather than simplistic CRUD workflows.

---

# Problem Statement

Enterprise sustainability reporting is operationally difficult because emissions-relevant data is fragmented across multiple systems:

* SAP exports for fuel and procurement
* Utility electricity data from portals or invoices
* Corporate travel data from travel management platforms
* Manual spreadsheets maintained by sustainability teams

These sources differ in:

* schema structure
* units
* naming conventions
* completeness
* timestamp formats
* identifiers
* categorization logic

Analysts currently spend substantial manual effort:

* reconciling inconsistent records
* identifying suspicious values
* normalizing units
* validating source integrity
* preparing audit-ready datasets

The system should reduce this operational friction while preserving traceability and auditability.

---

# Goals

## Primary Goals

1. Ingest realistic enterprise data from 3 source categories
2. Normalize all source data into a unified emissions activity model
3. Preserve raw source data for traceability
4. Enable analyst review and approval workflows
5. Maintain immutable audit history
6. Support multiple client organizations (multi-tenancy)

---

# Non-Goals

The prototype will NOT attempt to:

* compute production-grade carbon emissions
* support real-time ingestion pipelines
* integrate directly with live SAP systems
* support automated OCR for PDFs
* implement enterprise authentication providers (SSO/SAML)
* provide complete regulatory reporting exports

---

# Users

## Sustainability Analyst

Reviews imported data, resolves issues, approves records.

## ESG Operations Manager

Monitors ingestion quality and audit readiness.

## Auditor

Views locked and traceable records.

## Platform Administrator

Manages organizations and ingestion configurations.

---

# Source Systems

# 1. SAP Fuel & Procurement Data

## Chosen Representation

CSV export simulating SAP flat-file export behavior.

## Why

Flat-file exports are common in enterprise onboarding workflows and realistic for early-stage integrations.

## Characteristics

* inconsistent units
* plant codes
* vendor metadata
* mixed date formats
* procurement categories
* optional German column names

## Example Fields

* plant_code
* vendor_name
* fuel_type
* quantity
* unit
* posting_date
* cost_center

---

# 2. Utility Electricity Data

## Chosen Representation

CSV export from utility portal.

## Why

Most facilities teams export monthly consumption data manually from utility dashboards.

## Characteristics

* billing periods do not align to months
* mixed tariffs
* meter identifiers
* kWh/MWh variations

## Example Fields

* meter_id
* billing_start
* billing_end
* consumption
* unit
* tariff_type
* facility_name

---

# 3. Corporate Travel Data

## Chosen Representation

Simplified Concur-style JSON export/API payload.

## Why

Travel platforms commonly expose structured APIs or downloadable reports.

## Characteristics

* flights
* hotels
* rail
* ground transport
* airport codes
* missing distance data

## Example Fields

* employee_id
* trip_type
* origin
* destination
* booking_class
* distance_km
* hotel_nights

---

# Core Product Requirements

# 1. Data Ingestion

The system must support:

* file upload ingestion
* ingestion status tracking
* source metadata preservation
* ingestion failure handling

Each upload should generate:

* ingestion job
* raw source record storage
* normalization attempt logs

---

# 2. Data Normalization

The system must:

* map heterogeneous records into unified activities
* normalize units
* standardize timestamps
* assign emissions scopes
* categorize activities

Example:

* diesel purchase → Scope 1
* electricity consumption → Scope 2
* flights → Scope 3

---

# 3. Unified Activity Model

All imported records must normalize into a common internal structure.

Core attributes:

* organization
* source type
* activity category
* emissions scope
* quantity
* normalized unit
* activity date
* review state
* source reference

---

# 4. Analyst Review Dashboard

Analysts must be able to:

* view imported records
* filter by status/source
* inspect normalization warnings
* flag suspicious records
* approve records
* reject records
* lock approved records

---

# 5. Suspicious Record Detection

Prototype heuristics:

* negative quantities
* unusually high consumption
* unsupported units
* missing required fields
* impossible travel routes

Flagged rows require analyst review before approval.

---

# 6. Auditability

The system must preserve:

* original raw payload
* edit history
* reviewer identity
* approval timestamps
* immutable locked records

Auditors should be able to trace:
Normalized Activity → Source Record → Original Upload

---

# 7. Multi-Tenancy

The platform must isolate data by organization.

Every major entity should belong to:

* organization
* ingestion source
* user action context

---

# Functional Requirements

## Authentication

* email/password login
* organization-scoped access

## Upload Management

* upload CSV/JSON files
* ingestion history view
* ingestion error display

## Record Review

* table-based analyst UI
* row inspection modal
* approve/reject workflow

## Audit Locking

* approved rows become immutable once locked

## Search & Filtering

* by source
* by scope
* by status
* by organization

---

# Suggested Architecture

Frontend:

* React
* TypeScript
* Tailwind
* TanStack Table

Backend:

* Django
* Django REST Framework
* PostgreSQL

Deployment:

* Render/Railway/Fly

Storage:

* raw upload storage
* normalized relational storage

---

# Data Model Principles

## Separate Raw vs Normalized Data

Raw source data must remain immutable.

## Preserve Provenance

Every normalized row must trace back to:

* source file
* upload timestamp
* original payload

## Avoid Source-Specific Analyst Workflows

Analysts interact with unified activities, not individual source schemas.

## Explicit Workflow States

Records transition through:

* INGESTED
* FLAGGED
* REVIEWED
* APPROVED
* LOCKED

---

# UX Principles

* analyst-first workflows
* minimal clicks
* table-centric review experience
* transparent validation errors
* no hidden transformations

---

# Success Criteria

The prototype succeeds if:

* all three source types ingest successfully
* normalization is explainable
* analysts can review and approve records
* audit traceability exists
* architectural decisions are defensible

---

# Risks

## Data Ambiguity

Real enterprise exports are inconsistent.

## Unit Conversion Errors

Incorrect normalization can corrupt reporting.

## Over-Engineering

Prototype scope must remain constrained.

## Audit Complexity

True audit systems require deeper immutability guarantees.

---

# Future Improvements

* automated emissions factor engine
* live SAP integrations
* OCR for utility PDFs
* configurable mapping rules
* ML anomaly detection
* workflow notifications
* role-based approvals
* SSO/SAML support
* regulatory reporting exports

---

# Key Tradeoff Philosophy

The prototype prioritizes:

* explainability
* traceability
* realistic modeling
* architectural clarity

over:

* feature breadth
* polished visuals
* production-scale infrastructure
