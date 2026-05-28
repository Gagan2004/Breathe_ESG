# Product Tradeoffs & Exclusions (TRADEOFFS.md)

To deliver a reliable, clean, and highly audit-defensible prototype within the timeline, we made three deliberate scope exclusions:

---

## 1. Automated Emissions Factor Matching Engine

### What was excluded
An automatic carbon equivalent ($CO_2e$) calculation engine that links activity items to international databases (e.g. DEFRA, US EPA, Ecoinvent) based on region and year.

### Rationale
Emissions factors are dynamic, heavily audited, and depend on highly granular parameters (e.g., fuel density, vehicle year, local electrical grid sub-region mix). Building a basic factor calculator would result in inaccurate emissions calculations that look like "sustainability slop". Instead, we focused our data model and architecture on **audit-readiness and data lineage** (ensuring quantities, units, and sources are locked and traceable). This creates a solid foundation for adding an enterprise-grade emissions calculation engine (e.g. integrating Climatiq or similar APIs) in a future phase.

---

## 2. Asynchronous Background Task Queue (Celery/Redis)

### What was excluded
Setting up a separate worker server (Celery) with a message broker (Redis/RabbitMQ) to parse uploaded files asynchronously in the background.

### Rationale
Adding a background worker layer introduces infrastructure complexity (managing broker uptime, setting up Docker containers, handling WebSocket notifications for status updates). For a prototype, the file uploads are relatively small (under 10,000 rows). We designed the parsing engine to process files synchronously in the request-response thread inside atomic database transactions. If a file fails, it fails instantly and returns the error. The backend and DB models are fully prepared for background workers (via the `status = PENDING / PROCESSING` model fields), but keeping it synchronous for now reduces deployment friction and ensures a robust local setup.

---

## 3. OCR Utility Bill Parser

### What was excluded
Building a PDF scraper or Optical Character Recognition (OCR) pipeline to extract utility consumption figures from scanned invoices.

### Rationale
OCR models (such as Tesseract or AWS Textract) require complex preprocessing, fail on low-resolution scans, and have high error rates on tabular data (often mixing decimal points or meter numbers). A misread digit of utility electricity consumption directly ruins audit credibility. Rather than building a fragile OCR model, we decided utility data must be ingested through structured portal exports (CSV/JSON). This forces the facility teams to pull structured data from utility accounts, guaranteeing mathematical accuracy.