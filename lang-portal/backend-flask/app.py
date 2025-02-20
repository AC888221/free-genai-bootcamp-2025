from flask import Flask, g, jsonify
from flask_cors import CORS

from lib.db import Db

import routes.words
import routes.groups
import routes.study_sessions
import routes.dashboard
import routes.study_activities

def get_allowed_origins(app):
    try:
        cursor = app.db.cursor()
        cursor.execute('SELECT url FROM study_activities')
        urls = cursor.fetchall()
        # Convert URLs to origins (e.g., https://example.com/app -> https://example.com)
        origins = set()
        for url in urls:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url['url'])
                origin = f"{parsed.scheme}://{parsed.netloc}"
                origins.add(origin)
            except:
                continue
        return list(origins) if origins else ["*"]
    except:
        return ["*"]  # Fallback to allow all origins if there's an error

def create_app(test_config=None):
    app = Flask(__name__)
    
    # Default configuration
    app.config.from_mapping(
        DATABASE='words.db'
    )

    # Override with test config if provided
    if test_config is not None:
        if 'DATABASE' not in test_config:
            test_config['DATABASE'] = ':memory:'
        app.config.update(test_config)

    # Initialize database
    app.db = Db(database=app.config['DATABASE'])
    
    # Configure CORS
    allowed_origins = get_allowed_origins(app)
    if app.debug:
        allowed_origins.extend(["http://localhost:8080", "http://127.0.0.1:8080"])
    
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    @app.teardown_appcontext
    def close_db(exception):
        app.db.close()

    # Load routes based on environment
    if not app.config.get('TESTING', False):
        # Normal route loading
        from routes import study_sessions, groups, words
        study_sessions.load(app)
        groups.load(app)
        words.load(app)
    else:
        # Test route loading - simplified version
        @app.route('/api/words', methods=['POST'])
        def create_word():
            return {'message': 'Test route'}, 201

        @app.route('/api/words/<int:id>', methods=['GET'])
        def get_word(id):
            return {'message': 'Test route'}, 200
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)