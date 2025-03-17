from database import Database
import argparse
import os

def initialize_database(reset: bool = False):
    """Initialize the database and create tables."""
    db_path = "songs.db"
    
    if reset and os.path.exists(db_path):
        print(f"Removing existing database at {db_path}")
        os.remove(db_path)
    
    print("Initializing database...")
    db = Database()
    db.create_tables()
    print("Database initialized successfully.")
    
    # Test connection
    try:
        history = db.get_song_history()
        print(f"Database connection test successful. Found {len(history)} existing entries.")
    except Exception as e:
        print(f"Database connection test failed: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initialize the SongWords database')
    parser.add_argument('--reset', action='store_true', help='Reset the database (delete existing)')
    args = parser.parse_args()
    
    initialize_database(args.reset)