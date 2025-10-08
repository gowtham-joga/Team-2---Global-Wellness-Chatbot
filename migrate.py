import sqlite3

DB_PATH = "main_database.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add is_admin column if not exists
try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0;")
except sqlite3.OperationalError:
    print("Column 'is_admin' already exists.")

# Create knowledge_base table
cursor.execute("""
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent TEXT NOT NULL,
    entity_value TEXT,
    response_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Create feedback table
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    intent TEXT,
    entities TEXT,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    feedback INTEGER NOT NULL,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()
print("✅ Database migration completed!")
