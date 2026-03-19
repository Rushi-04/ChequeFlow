import sqlite3
import pyodbc
from num2words import num2words
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DB2 connection details (retrieved from environment)
host = os.getenv('DB2_HOST')
port = os.getenv('DB2_PORT')
database = os.getenv('DB2_DATABASE')
user = os.getenv('DB2_USER')
password = os.getenv('DB2_PASSWORD')

connection_string = (
    f"DRIVER={{iSeries Access ODBC Driver}};"
    f"SYSTEM={host};"
    f"PORT={port};"
    f"DATABASE={database};"
    f"UID={user};"
    f"PWD={password};"
    f"PROTOCOL=TCPIP;"
)

def format_amount_words(amount_val):
    try:
        amt_float = float(amount_val)
        dollars = int(amt_float)
        cents = int(round((amt_float - dollars) * 100))
        words = num2words(dollars, lang='en').title()
        words = words.replace(',', '').replace('-', ' ').replace(' And ', ' ')
        return f"*** {words} Dollars And {cents:02d}/100***"
    except Exception:
        return "*** Zero Dollars And 00/100***"

def sync():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "cheques.db")
    print(f"DEBUG: Connecting to local SQLite at {db_path}")
    
    print(f"Connecting to DB2...")
    try:
        conn_db2 = pyodbc.connect(connection_string, autocommit=True)
        cursor_db2 = conn_db2.cursor()
    except Exception as e:
        print(f"Failed to connect to DB2: {e}")
        return

    print("Connecting to local SQLite...")
    conn_local = sqlite3.connect(db_path)
    cursor_local = conn_local.cursor()

    try:
        # 1. Fetch rows from WCHKSP
        print("Fetching records from tstkdp.WCHKSP...")
        # cursor_db2.execute("SELECT * FROM tstkdp.WCHKSP")
        cursor_db2.execute("SELECT * FROM tstkdp.WCHKSP FETCH FIRST 10 ROWS ONLY")
        columns_wchksp = [col[0].upper() for col in cursor_db2.description]
        rows_wchksp = cursor_db2.fetchall()

        for row in rows_wchksp:
            data_wchksp = dict(zip(columns_wchksp, row))
            
            # BKCODE logic (Robustly handle missing column or empty values)
            if 'BKCODE' in columns_wchksp:
                bkcode = data_wchksp.get('BKCODE')
                if not bkcode or str(bkcode).strip() == "":
                    bkcode = "J84P"
                else:
                    bkcode = str(bkcode).strip()
            else:
                # Column doesn't exist yet in DB2
                bkcode = "J84P"
            
            # 2. Fetch enriched data from ameriben.bankfile
            print(f"Enriching cheque {data_wchksp.get('CKCHK#')} with BKCODE {bkcode}...")
            cursor_db2.execute("SELECT * FROM ameriben.bankfile WHERE BKCODE = ?", (bkcode,))
            columns_bank = [col[0].upper() for col in cursor_db2.description]
            bank_row = cursor_db2.fetchone()
            
            data_bank = dict(zip(columns_bank, bank_row)) if bank_row else {}

            # --- Mapping Logic ---
            
            # Date Construction (MM/DD/YYYY)
            y = str(data_wchksp.get('CKCKDY', '')).strip()
            if len(y) == 2: y = "20" + y
            m_raw = str(data_wchksp.get('CKCKDM', '')).strip()
            try:
                m = str(int(m_raw)) if m_raw else "MM"
            except ValueError:
                m = m_raw if m_raw else "MM"
                
            d = str(data_wchksp.get('CKCKDD', '')).strip().zfill(2)
            if not d: d = "DD"
            date_str = f"{m}/{d}/{y}"

            # Payee Address
            addr_fields = ['CKPYA1', 'CKPYA2', 'CKPYA3', 'CKPYA4', 'CKPYA5']
            addr_parts = [str(data_wchksp.get(f, '')).strip() for f in addr_fields]
            payee_address = "\n".join([p for p in addr_parts if p])

            # Employer Name
            emp_name = str(data_bank.get('BKNAME', '')).strip()
            emp_name2 = str(data_bank.get('BKNAM2', '')).strip()
            employer_name = f"{emp_name}\n{emp_name2}" if emp_name2 else emp_name
            if not employer_name.strip(): employer_name = "data not found - employer_name"

            # Employer Address
            employer_street = str(data_bank.get('BKADR1', 'data not found - employer_street')).strip()
            city_state_zip = f"{str(data_bank.get('BKADR2', '')).strip()} {str(data_bank.get('BKADR3', '')).strip()}".strip()
            if not city_state_zip: city_state_zip = "data not found - employer_city_state_zip"

            # Bank Info
            bank_name = str(data_bank.get('BKBNAM', '')).strip()
            bank_addr = f"{str(data_bank.get('BKBAD1', '')).strip()}\n{str(data_bank.get('BKBAD2', '')).strip()}\n{str(data_bank.get('BKBAD3', '')).strip()}".strip()
            bank_info = f"{bank_name}\n{bank_addr}".strip()
            if not bank_info: bank_info = "data not found - bank_info"

            # Amount
            try:
                amt_raw = data_wchksp.get('CKCLM$', 0)
                amount = float(amt_raw) if amt_raw is not None else 0.0
            except:
                amount = 0.0
            amount_words = format_amount_words(amount)

            # Void Days
            try:
                void_days = int(data_bank.get('BKVOID', 90))
            except:
                void_days = 90

            # MICR Components
            routing_number = str(data_bank.get('BKTRAN', '')).strip()
            micr_account_tail = str(data_bank.get('BKACCT', '')).strip()

            # 3. UPSERT into local SQLite
            cursor_local.execute('''
            INSERT OR REPLACE INTO cheques (
                cheque_number, date, ssn, payee_name, payee_address, amount, amount_words,
                claim_number, status, payment_mode, bkcode,
                employer_name, employer_street, employer_city_state_zip,
                bank_info, routing_number, micr_account_tail, void_days,
                signature_path
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                str(data_wchksp.get('CKCHK#', '')).strip(),
                date_str,
                str(data_wchksp.get('CKMSSN', '')).strip(),
                str(data_wchksp.get('CKPYNM', '')).strip(),
                payee_address,
                amount,
                amount_words,
                str(data_wchksp.get('CKCLM#', '')).strip(),
                str(data_wchksp.get('CKSTAT', '')).strip(),
                str(data_wchksp.get('CKPMO', '')).strip(),
                bkcode,
                employer_name,
                employer_street,
                city_state_zip,
                bank_info,
                routing_number,
                micr_account_tail,
                void_days,
                "" # Signature path blank per rule
            ))

        conn_local.commit()
        print("Synchronization complete.")

    except Exception as e:
        print(f"Error during synchronization: {e}")
    finally:
        cursor_db2.close()
        conn_db2.close()
        conn_local.close()

if __name__ == "__main__":
    sync()
