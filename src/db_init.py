import sqlite3
import os

def init_db():
    # Define absolute path for the database in the project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "cheques.db")
    print(f"DEBUG: Initializing database at {db_path}")
    
    # Optional: Keep existing data or start fresh?
    # For sync purposes, we want the schema to be consistent.
    # User said "store all processed/enriched rows into your local table first"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # We'll drop and recreate to ensure schema matches the new requirements perfectly
    cursor.execute('DROP TABLE IF EXISTS cheques')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cheques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cheque_number TEXT UNIQUE,
        date TEXT,
        ssn TEXT,
        payee_name TEXT,
        payee_address TEXT,
        amount REAL,
        amount_words TEXT,
        
        claim_number TEXT,
        status TEXT,
        payment_mode TEXT,
        bkcode TEXT,
        
        employer_name TEXT,
        employer_street TEXT,
        employer_city_state_zip TEXT,
        bank_info TEXT,
        routing_number TEXT,
        micr_account_tail TEXT,
        void_days INTEGER DEFAULT 90,
        
        signature_path TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Local database schema initialized for enriched data.")

if __name__ == "__main__":
    init_db()
