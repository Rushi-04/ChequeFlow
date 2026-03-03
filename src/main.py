import sqlite3
import os
from cheque_generator import ChequeGenerator

def run_system():
    db_path = "cheques.db"
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found. Please run src/db_init.py first.")
        return

    # Initialize generator
    generator = ChequeGenerator(output_dir="outputs")

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM cheques")
        rows = cursor.fetchall()
        
        if not rows:
            print("No records found in the database.")
            return

        print(f"Found {len(rows)} records. Starting PDF generation...")

        for row in rows:
            # Convert row to dictionary
            data = dict(row)
            
            # Generate the cheque PDF
            try:
                pdf_path = generator.generate(data)
                print(f"Successfully generated: {pdf_path}")
            except Exception as e:
                print(f"Failed to generate cheque for ID {data['id']}: {e}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

    print("Generation complete. Check the 'outputs' folder.")

if __name__ == "__main__":
    run_system()
