from database import Database

def initialize_database():
    """Initialize the database and create tables."""
    print("Initializing database...")
    db = Database()
    db.create_tables()
    print("Database initialized successfully.")

if __name__ == "__main__":
    initialize_database()