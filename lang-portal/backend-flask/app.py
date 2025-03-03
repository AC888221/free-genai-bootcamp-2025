import logging
from flask import Flask, g, jsonify
from flask_cors import CORS
from lib.db import Db
import routes.words
import routes.groups
import routes.study_sessions
import routes.dashboard
from routes.study_activities import study_activities_bp  # Import the Blueprint
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_allowed_origins(app):
    try:
        cursor = app.db.cursor()
        cursor.execute('SELECT url FROM study_activities')
        urls = cursor.fetchall()
        origins = set()
        for url in urls:
            try:
                parsed = urlparse(url['url'])
                origin = f"{parsed.scheme}://{parsed.netloc}"
                origins.add(origin)
            except Exception as e:
                logger.error(f"Error parsing URL {url}: {e}")
                continue
        return list(origins) if origins else ["*"]
    except Exception as e:
        logger.error(f"Error fetching allowed origins: {e}")
        return ["*"]

def create_app(test_config=None):
    app = Flask(__name__)
    
    app.config.from_mapping(DATABASE='words.db')

    if test_config is not None:
        if 'DATABASE' not in test_config:
            test_config['DATABASE'] = ':memory:'
        app.config.update(test_config)

    app.db = Db(database=app.config['DATABASE'])
    
    with app.app_context():
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

    @app.errorhandler(404)
    def not_found(error):
        logger.error(f"404 error: {error}")
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

    if not app.config.get('TESTING', False):
        from routes import study_sessions, groups, words, dashboard
        study_sessions.load(app)
        groups.load(app)
        words.load(app)
        dashboard.load(app)
        app.register_blueprint(study_activities_bp)  # Register the Blueprint
    else:
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