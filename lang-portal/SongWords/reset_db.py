from database import Database
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Reset the database with the new schema."""
    db_path = "songs.db"
    
    # Remove existing database
    if os.path.exists(db_path):
        logger.info(f"Removing existing database at {db_path}")
        os.remove(db_path)
    
    # Create new database with updated schema
    logger.info("Creating new database with updated schema...")
    db = Database()
    db.create_tables()
    logger.info("Database reset successfully with new schema.")
    
    # Test connection
    try:
        history = db.get_song_history()
        logger.info(f"Database connection test successful. Found {len(history)} entries.")
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()