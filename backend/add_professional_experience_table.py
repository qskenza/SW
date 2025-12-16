"""
Quick script to add professional_experience table
"""
import sqlite3
import os

def add_professional_experience_table():
    db_path = "careconnect.db"

    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Please make sure you're in the backend directory")
        return

    print("🔄 Adding professional_experience table...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the professional_experience table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS professional_experience (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER NOT NULL,
                position VARCHAR(200) NOT NULL,
                institution VARCHAR(200) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                description TEXT,
                is_current BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        """)

        conn.commit()
        print("✅ Table created successfully!")

        # Verify it was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professional_experience'")
        if cursor.fetchone():
            print("✅ Verified: professional_experience table exists")
        else:
            print("⚠️  Warning: Table might not have been created")

        conn.close()

        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your backend server")
        print("2. Doctors can now add professional experience in their dashboard")
        print("3. Students will see the experience when viewing doctor profiles")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nIf the table already exists, you can ignore this error.")

if __name__ == "__main__":
    add_professional_experience_table()
