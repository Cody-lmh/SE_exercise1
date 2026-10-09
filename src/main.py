import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from postgrest.exceptions import APIError
from src.db import SupabaseConfigError, error_message
from src.routes.user import user_bp
from src.routes.note import note_bp
from src.routes.translate import translate_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app)

# register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(note_bp, url_prefix='/api')
app.register_blueprint(translate_bp, url_prefix='/api')

# Data lives in Supabase; the client is configured from the environment in
# src/db.py and the schema is created by supabase/migrations.
@app.errorhandler(SupabaseConfigError)
def handle_supabase_config_error(error):
    """Report missing Supabase credentials instead of a bare 500 page."""
    return jsonify({'error': str(error)}), 500

@app.errorhandler(APIError)
def handle_postgrest_error(error):
    """Return PostgREST failures as JSON so the UI can show the real message."""
    return jsonify({'error': error_message(error)}), 500

if not (os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_KEY')):
    print(
        'WARNING: SUPABASE_URL and/or SUPABASE_KEY are not set, so every API '
        'request will fail. Copy .env.example to .env and fill it in, then '
        'apply supabase/migrations (see README.md).',
        file=sys.stderr,
    )

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
