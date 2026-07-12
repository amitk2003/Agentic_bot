import sqlite3

def main():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT 10")
    for row in c.fetchall():
        print(f"Role: {row[0]}, Content Length: {len(row[1]) if row[1] else 0}")
        print(f"Content Prefix: {row[1][:100] if row[1] else 'None'}")
        print("-" * 40)

if __name__ == "__main__":
    main()
