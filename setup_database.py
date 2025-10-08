import sqlite3
import json

DB_PATH = "main_database.db"
KB_JSON_PATH = "kb.json"

def setup_kb_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop & recreate clean table
    cursor.execute("DROP TABLE IF EXISTS knowledge_base")

    # UPDATED: Added created_at and updated_at columns to match models.py
    cursor.execute("""
    CREATE TABLE knowledge_base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intent TEXT NOT NULL,
        entity_value TEXT,
        response_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(intent, entity_value)
    )
    """)

    # Load JSON
    with open(KB_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Insert rows
    for item in data:
        intent = item['intent']
        response = item['response']
        entities = item.get('entities', [])

        if not entities:
            cursor.execute("""
                INSERT OR IGNORE INTO knowledge_base (intent, entity_value, response_text)
                VALUES (?, ?, ?)
            """, (intent, None, response))
        else:
            for ent in entities:
                cursor.execute("""
                    INSERT OR IGNORE INTO knowledge_base (intent, entity_value, response_text)
                    VALUES (?, ?, ?)
                """, (intent, ent.lower().strip(), response))

    conn.commit()
    conn.close()
    print(f"✅ Knowledge base created and populated in '{DB_PATH}'.")

if __name__ == "__main__":
    setup_kb_table()