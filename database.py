import sqlite3

DATABASE_NAME = "tickets.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

#Ticket table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_type TEXT NOT NULL DEFAULT 'task',
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            reported_by TEXT,
            reported_to TEXT,
            assigned_to TEXT,
            visibility TEXT DEFAULT 'public',
            status TEXT DEFAULT 'pending',
            proof_required INTEGER DEFAULT 1,
            proof_type TEXT DEFAULT 'photo',
            proof_path TEXT,
            staff_note TEXT,
            manager_comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id)
        )
    """)

    conn.commit()
    conn.close()