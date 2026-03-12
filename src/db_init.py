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
        employer_street TEXT,
        employer_city_state_zip TEXT,
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
        signature_path TEXT,
        memo TEXT,
        gross_amt TEXT,
        fed_wh TEXT,
        hw_ins TEXT,
        voucher_id TEXT,
        routing_number TEXT,
        micr_serial TEXT
    )
    ''')
    
    # Sample data based on the image provided
    sample_data = [
        (
            "EMPLOYER - TEAMSTERS LOCAL NOS. 175 & 505\nPENSION TRUST FUND",
            "",
            "269 Staunton Ave SW Ste 200",
            "South Charleston WV 25303",
            "1/28/25",
            "782-23-8626",
            "UNITED BANK\nCHARLESTON, WEST VIRGINIA",
            "CARRIE LARCH",
            "5907 MELWOOD DR\nCHARLESTON, WV 25313",
            5949.00,
            "*** Five Thousand Nine Hundred Forty Nine Dollars And 00/100***",
            "01389587",
            "051900395",
            "04337",
            "https://drive.google.com/file/d/1ligjpsMQSSa5KTJEReBohw5d4fHapa3M/view?usp=sharing",
            "BP 4/24-01/25",
            "$7,626.90",
            "$1,677.90",
            "$.00",
            "J84",
            "051900395",
            "0452"
        )
    ]
    
    cursor.executemany('''
    INSERT INTO cheques (
        employer_name, employer_address, employer_street, employer_city_state_zip, 
        date, ssn, bank_info, payee_name, payee_address, amount, amount_words, 
        cheque_number, transit_number, account_number, signature_path,
        memo, gross_amt, fed_wh, hw_ins, voucher_id, routing_number, micr_serial
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', sample_data)
    
    conn.commit()
    conn.close()
    print("Database initialized with sample data.")

if __name__ == "__main__":
    init_db()
