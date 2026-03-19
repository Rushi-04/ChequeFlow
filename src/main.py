import sqlite3
import os
from cheque_generator import ChequeGenerator

def run_system():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "cheques.db")
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found. Please run src/db_init.py and src/sync_db2.py first.")
        return

    # Initialize generator
    generator = ChequeGenerator(output_dir="outputs")

    # Connect to local SQLite database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    try:
        print("Fetching enriched records from local SQLite...")
        cursor.execute("SELECT * FROM cheques")
        rows = cursor.fetchall()
        
        if not rows:
            print("No records found in the local database. Please run src/sync_db2.py.")
            return

        print(f"Found {len(rows)} enriched records. Starting PDF generation...")

        for row in rows:
            # Convert sqlite3.Row to dictionary
            data = dict(row)
            
            # Generate the cheque PDF
            try:
                # The data dictionary now contains all enriched fields:
                # employer_name, employer_street, employer_city_state_zip, bank_info,
                # routing_number, micr_account_tail, void_days, etc.
                pdf_path = generator.generate(data)
                print(f"Successfully generated: {pdf_path}")
            except Exception as e:
                print(f"Failed to generate cheque for {data.get('cheque_number', 'unknown')}: {e}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

    print("Generation complete. Check the 'outputs' folder.")

if __name__ == "__main__":
    run_system()
