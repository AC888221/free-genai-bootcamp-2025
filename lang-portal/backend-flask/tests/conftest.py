# Jiantizi adaption for Bootcamp Week 1:
# Configure pytest for Flask testing

import os
import tempfile
import pytest
from app import create_app
from lib.db import Db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary database file path
    db_fd, db_path = tempfile.mkstemp()
    
    # Create the app with the test config
    test_app = create_app({
        'TESTING': True,
        'DATABASE': db_path
    })

    # Setup the database schema
    with test_app.app_context():
        cursor = test_app.db.cursor()
        # Create necessary tables for testing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                jiantizi TEXT NOT NULL,
                pinyin TEXT NOT NULL,
                english TEXT NOT NULL
            )
        ''')
        test_app.db.commit()

    yield test_app

    # Clean up the temporary file
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner() 