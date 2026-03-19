import sqlite3
import os

class SqliteService:
    def __init__(self, db_path):
        self.db_path = db_path

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_cheques(self, page=1, page_size=10, filters=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        offset = (page - 1) * page_size
        query = "SELECT * FROM cheques WHERE 1=1"
        params = []

        if filters:
            if filters.get('cheque_number'):
                query += " AND cheque_number LIKE ?"
                params.append(f"%{filters['cheque_number']}%")
            if filters.get('payee_name'):
                query += " AND payee_name COLLATE NOCASE LIKE ?"
                params.append(f"%{filters['payee_name']}%")
            if filters.get('ssn_last4'):
                query += " AND ssn LIKE ?"
                params.append(f"%{filters['ssn_last4']}")
            if filters.get('date'):
                query += " AND date LIKE ?"
                params.append(f"%{filters['date']}%")

        # Total count for pagination
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Fetch page
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Process rows (mask SSN)
        results = []
        for row in rows:
            d = dict(row)
            ssn = d.get('ssn', '')
            d['ssn_masked'] = "XXXXX" + ssn[-4:] if len(ssn) >= 4 else ssn
            d.pop('ssn', None) # Security: remove full SSN from API response
            results.append(d)

        conn.close()
        return results, total_count

    def get_full_data_by_ids(self, ids):
        """Used by the generator service to get FULL data including SSN"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        placeholders = ",".join(["?"] * len(ids))
        query = f"SELECT * FROM cheques WHERE id IN ({placeholders})"
        cursor.execute(query, ids)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
