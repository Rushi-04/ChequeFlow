# ChequeFlow: Enterprise Cheque Generation and Audit Dashboard

ChequeFlow is a precision-engineered internal tool designed for the automated synchronization, enrichment, and generation of bank-standard cheques. The system bridges legacy IBM DB2 data with a modern web-based audit interface, ensuring high-fidelity PDF output and secure data management.

## System Architecture

The application follows a modular three-tier architecture to ensure scalability and maintainability:

1.  **Data Integration Tier**: Connects to IBM DB2 (AS/400) to retrieve raw transaction records from `tstkdp.WCHKSP`. It performs real-time relational enrichment using `ameriben.bankfile` to fetch employer and banking institution metadata.
2.  **Service & Persistence Tier**: Utilizes a local SQLite database as a high-performance cache for enriched records. Business logic is encapsulated in a dedicated service layer:
    *   `SyncService`: Manages DB2 connectivity, data transformation, and upsert logic.
    *   `SqliteService`: Handles paginated data retrieval, complex filtering, and sensitive data masking (SSN).
    *   `ChequeService`: Orchestrates on-demand PDF generation using the ReportLab engine.
3.  **Presentation Tier**: A FastAPI-powered web dashboard provides an interactive interface for administrators to review, preview, and download individual cheques.

## Core Technical Specifications

*   **PDF Rendering**: Generates Letter-sized (8.5" x 11") documents including a high-detail Remittance Advice (top 2/3) and a standard bank cheque (bottom 1/3).
*   **Security Compliance**: Implementation of multi-level SSN masking. Sensitive data is never fully exposed in the browser; full decryption/retrieval only occurs server-side during the on-demand PDF rendering process.
*   **MICR Precision**: Utilizes the E13B font for bank-standard MICR line generation, with glyph-to-account mapping compliant with modern banking scanners.
*   **Dynamic Voiding**: Includes customizable void logic and background watermarking to prevent unauthorized reproduction.
*   **Signature Processing**: Advanced image processing for digital signatures, including background transparency subtraction and contrast optimization for high-quality printing.

## Installation and Configuration

### Prerequisites

*   Python 3.9+
*   IBM iSeries Access ODBC Driver
*   `pip install -r requirements.txt`

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```text
DB2_HOST=your_host_address
DB2_PORT=your_port
DB2_DATABASE=your_database_name
DB2_USER=your_username
DB2_PASSWORD=your_password
```

## Operational Workflows

### 1. Database Initialization
Ensure the local cache schema is prepared:
```bash
python src/db_init.py
```

### 2. Data Synchronization
Retrieve and enrich data from the DB2 environment:
```bash
python src/sync_db2.py
```

### 3. Launching the Audit Dashboard
Start the FastAPI server:
```bash
python src/app.py
```
The dashboard will be available at `http://localhost:8000`.

## Project Directory Structure

*   `src/`: Primary application source code.
    *   `services/`: Core business logic and database access objects.
    *   `templates/`: Web dashboard frontend assets.
*   `assets/`: Required fonts (`E13B.ttf`), signatures, and static resources.
*   `outputs/`: Default directory for generated PDF documents.
*   `cheques.db`: Local SQLite persistent cache.
*   `.env`: Environment configuration (not committed).

---
© 2026 ChequeFlow Technical Documentation. Confidential and Proprietary.
