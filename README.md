# ChequeFlow Pro

**ChequeFlow Pro** is a high-precision, automated bank cheque generation system designed for professional financial workflows. It seamlessly integrates data from an SQLite database to produce perfectly formatted, bank-standard PDFs (8.5" x 3.5") ready for printing.

![Project Banner](https://img.shields.io/badge/Financial-Automation-blue?style=for-the-badge)
![Python Version](https://img.shields.io/badge/Python-3.8%2B-green?style=for-the-badge)
![PDF Engine](https://img.shields.io/badge/Engine-ReportLab-orange?style=for-the-badge)

---

## Key Features

* **Bank-Standard MICR Support**: Native integration of `E-13B` MICR fonts, ensuring all generated cheques are compatible with automated banking reader-sorters.
* **Intelligent Signature Processing**:
  * **Google Drive Integration**: Fetches signatures directly from cloud URLs in-memory.
  * **Auto-Cropping**: Automatically detects signature content and crops square images into clean, rectangular segments.
  * **Direct Embedding**: Uses advanced `ImageReader` matrix embedding to ensure 100% rendering reliability and high-resolution output.
* **Professional Layout Design**:
  * Subliminal "VOID" background watermark.
  * Dynamic multi-line Support for Employer and Bank information.
  * Precise alignment of MICR lines, date tables, and amount boxes.
  * Consistent 2.5-inch signature Scaling for a premium look.
* **Data-Driven Workflow**: Batch generate hundreds of cheques from a single SQLite source with one command.

---

## Project Structure

```text
Cheque_System/
├── assets/
│   ├── fonts/           # Bank-standard MICR fonts (E13B.ttf)
│   └── signatures/      # Local signature backup storage
├── outputs/             # Generated PDF cheques
├── src/
│   ├── cheque_generator.py # Core PDF generation engine
│   ├── db_init.py          # Database schema initializer
│   ├── insert_data.py      # Sample data insertion script
│   └── main.py             # Orchestrator and runner
├── requirements.txt     # Python dependencies
└── README.md            # You are here
```

---

## Installation

1. **Clone the Repository**:

   ```bash
   git clone <repository-url>
   cd Cheque_System
   ```
2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
3. **Prepare Assets**:

   * Ensure the MICR font `E13B.ttf` is present in `assets/fonts/`.
   * Ensure your signature images are either in `assets/signatures/` or available via public Google Drive links.

---

## Usage Guide

### 1. Initialize the Database

Set up the SQLite database and create the required tables:

```bash
python src/db_init.py
```

### 2. Insert Cheque Data

Add records to the database. You can modify `src/insert_data.py` to include your specific payee details:

```bash
python src/insert_data.py
```

### 3. Generate Cheques

Run the main orchestrator to generate all PDFs in the `outputs/` folder:

```bash
python src/main.py
```

---

## Configuration & Database Schema

The system relies on a `cheques` table with the following structure:

| Field                | Description                                                 |
| :------------------- | :---------------------------------------------------------- |
| `employer_name`    | Name of the issuing entity (Supports multi-line).           |
| `employer_address` | Full address of the issuer.                                 |
| `date`             | Issuance date (Appears in dedicated table).                 |
| `ssn`              | Social Security Number for records.                         |
| `bank_info`        | Bank name and branch details.                               |
| `payee_name`       | Name of the recipient.                                      |
| `amount`           | Numerical amount (e.g., 5490.00).                           |
| `amount_words`     | The amount expressed in words for security.                 |
| `cheque_number`    | Unique sequential identifier.                               |
| `micr_line`        | The raw MICR string (includes transit and account symbols). |
| `signature_path`   | Local file path or Google Drive sharing link.               |

---

## Design Specifications

* **Page Size**: 8.5" x 3.5" (Standard Business Cheque).
* **Security Features**:
  * "VOID" watermark with 5% opacity.
  * Thick horizontal headers (0.22" top, 0.12" bottom).
  * "VOID AFTER 90 DAYS" indicator.
* **Signature Placement**: Positioned at `(5.7, 0.9)` with a width of `2.5 inches`.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
