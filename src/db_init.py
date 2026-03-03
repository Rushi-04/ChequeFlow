import sqlite3
import os

def init_db():
    db_path = "cheques.db"
    
    # Remove existing DB if it exists for fresh start
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cheques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employer_name TEXT,
        employer_address TEXT,
        date TEXT,
        ssn TEXT,
        bank_info TEXT,
        payee_name TEXT,
        payee_address TEXT,
        amount REAL,
        amount_words TEXT,
        cheque_number TEXT,
        transit_number TEXT,
        account_number TEXT,
        micr_line TEXT,
        signature_path TEXT
    )
    ''')
    
    # Sample data based on the image provided
    sample_data = [
        (
            "EMPLOYER - TEAMSTERS LOCAL NOS. 175 & 505\nPENSION TRUST FUND",
            "",
            "1/28/25",
            "782-23-8626",
            "UNITED BANK\nCHARLESTON, WEST VIRGINIA",
            "CARRIE LARCH",
            "5907 MELWOOD DR\nCHARLESTON, WV 25313",
            5949.00,
            "*** Five Thousand Nine Hundred Forty Nine Dollars And 00/100***",
            "01389587",
            "051900395",
            "043370452",
            "01389587 051900395 043370452", # Example MICR structure
            "assets/signatures/sample_sig.png"
        )
    ]
    
    cursor.executemany('''
    INSERT INTO cheques (
        employer_name, employer_address, date, ssn, bank_info, 
        payee_name, payee_address, amount, amount_words, 
        cheque_number, transit_number, account_number, micr_line, signature_path
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', sample_data)
    
    conn.commit()
    conn.close()
    print("Database initialized with sample data.")

if __name__ == "__main__":
    init_db()
