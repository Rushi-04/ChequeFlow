import sqlite3
import pyodbc
import os
from num2words import num2words
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DB2 connection details (retrieved from environment)
HOST = os.getenv('DB2_HOST')
PORT = os.getenv('DB2_PORT')
DATABASE = os.getenv('DB2_DATABASE')
USER = os.getenv('DB2_USER')
PASSWORD = os.getenv('DB2_PASSWORD')

CONNECTION_STRING = (
    f"DRIVER={{iSeries Access ODBC Driver}};"
    f"SYSTEM={HOST};"
    f"PORT={PORT};"
    f"DATABASE={DATABASE};"
    f"UID={USER};"
    f"PWD={PASSWORD};"
    f"PROTOCOL=TCPIP;"
)

class SyncService:
    def __init__(self, db_path):
        self.db_path = db_path

    def format_amount_words(self, amount_val):
        try:
            amt_float = float(amount_val)
            dollars = int(amt_float)
            cents = int(round((amt_float - dollars) * 100))
            words = num2words(dollars, lang='en').title()
            words = words.replace(',', '').replace('-', ' ').replace(' And ', ' ')
            return f"*** {words} Dollars And {cents:02d}/100***"
        except Exception:
            return "*** Zero Dollars And 00/100***"

    def run_sync(self):
        print("Connecting to DB2...")
        try:
            conn_db2 = pyodbc.connect(CONNECTION_STRING, autocommit=True)
            cursor_db2 = conn_db2.cursor()
        except Exception as e:
            return {"success": False, "error": f"DB2 Connection failed: {str(e)}"}

        print("Connecting to local SQLite...")
        conn_local = sqlite3.connect(self.db_path)
        cursor_local = conn_local.cursor()

        stats = {"fetched": 0, "synced": 0, "errors": []}

        try:
            # 1. Fetch rows from WCHKSP
            print("Fetching records from tstkdp.WCHKSP...")
            cursor_db2.execute("SELECT * FROM tstkdp.WCHKSP")
            columns_wchksp = [col[0].upper() for col in cursor_db2.description]
            rows_wchksp = cursor_db2.fetchall()
            stats["fetched"] = len(rows_wchksp)

            for row in rows_wchksp:
                try:
                    data_wchksp = dict(zip(columns_wchksp, row))
                    
                    # BKCODE logic (Resilient to missing column)
                    if 'BKCODE' in columns_wchksp:
                        bkcode = data_wchksp.get('BKCODE')
                        bkcode = str(bkcode).strip() if bkcode and str(bkcode).strip() != "" else "J84P"
                    else:
                        bkcode = "J84P"
                    
                    # 2. Fetch enriched data from ameriben.bankfile
                    cursor_db2.execute("SELECT * FROM ameriben.bankfile WHERE BKCODE = ?", (bkcode,))
                    columns_bank = [col[0].upper() for col in cursor_db2.description]
                    bank_row = cursor_db2.fetchone()
                    
                    data_bank = dict(zip(columns_bank, bank_row)) if bank_row else {}

                    # --- Mapping & Transformation ---
                    
                    # Date (No leading zero on month)
                    y = str(data_wchksp.get('CKCKDY', '')).strip()
                    if len(y) == 2: y = "20" + y
                    m_raw = str(data_wchksp.get('CKCKDM', '')).strip()
                    try:
                        m = str(int(m_raw)) if m_raw else "MM"
                    except:
                        m = m_raw if m_raw else "MM"
                    d = str(data_wchksp.get('CKCKDD', '')).strip().zfill(2)
                    date_str = f"{m}/{d}/{y}"

                    payee_address = "\n".join([str(data_wchksp.get(f, '')).strip() for f in ['CKPYA1', 'CKPYA2', 'CKPYA3', 'CKPYA4', 'CKPYA5'] if str(data_wchksp.get(f, '')).strip()])

                    emp_name = str(data_bank.get('BKNAME', '')).strip()
                    emp_name2 = str(data_bank.get('BKNAM2', '')).strip()
                    employer_name = f"{emp_name}\n{emp_name2}" if emp_name2 else emp_name
                    if not employer_name.strip(): employer_name = "data not found - employer_name"

                    employer_street = str(data_bank.get('BKADR1', 'data not found - employer_street')).strip()
                    city_state_zip = f"{str(data_bank.get('BKADR2', '')).strip()} {str(data_bank.get('BKADR3', '')).strip()}".strip()
                    if not city_state_zip: city_state_zip = "data not found - employer_city_state_zip"

                    bank_info = f"{str(data_bank.get('BKBNAM', '')).strip()}\n{str(data_bank.get('BKBAD1', '')).strip()}\n{str(data_bank.get('BKBAD2', '')).strip()}\n{str(data_bank.get('BKBAD3', '')).strip()}".strip()
                    if not bank_info: bank_info = "data not found - bank_info"

                    amt_raw = data_wchksp.get('CKCLM$', 0)
                    amount = float(amt_raw) if amt_raw is not None else 0.0
                    amount_words = self.format_amount_words(amount)

                    void_days = int(data_bank.get('BKVOID', 90))

                    cursor_local.execute('''
                    INSERT OR REPLACE INTO cheques (
                        cheque_number, date, ssn, payee_name, payee_address, amount, amount_words,
                        claim_number, status, payment_mode, bkcode,
                        employer_name, employer_street, employer_city_state_zip,
                        bank_info, routing_number, micr_account_tail, void_days,
                        signature_path
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (
                        str(data_wchksp.get('CKCHK#', '')).strip(), date_str,
                        str(data_wchksp.get('CKMSSN', '')).strip(), str(data_wchksp.get('CKPYNM', '')).strip(), payee_address,
                        amount, amount_words, str(data_wchksp.get('CKCLM#', '')).strip(),
                        str(data_wchksp.get('CKSTAT', '')).strip(), str(data_wchksp.get('CKPMO', '')).strip(), bkcode,
                        employer_name, employer_street, city_state_zip, bank_info,
                        str(data_bank.get('BKTRAN', '')).strip(), str(data_bank.get('BKACCT', '')).strip(),
                        void_days, ""
                    ))
                    stats["synced"] += 1
                except Exception as inner_e:
                    stats["errors"].append(f"Row error: {str(inner_e)}")

            conn_local.commit()
            return {"success": True, "stats": stats}

        except Exception as e:
            return {"success": False, "error": f"Sync failed: {str(e)}"}
        finally:
            cursor_db2.close()
            conn_db2.close()
            conn_local.close()

if __name__ == "__main__":
    # Test as standalone script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "cheques.db")
    service = SyncService(db_path)
    result = service.run_sync()
    print(result)
