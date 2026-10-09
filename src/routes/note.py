from flask import Blueprint, jsonify, request

from src.db import error_message
from src.models import note as note_repo

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    return jsonify(note_repo.list_notes())

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.get_json(silent=True)
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400

        note = note_repo.create_note(data['title'], data['content'])
        return jsonify(note), 201
    except Exception as e:
        return jsonify({'error': error_message(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    try:
        note = note_repo.get_note(note_id)
        if note is None:
            return jsonify({'error': 'Note not found'}), 404
        return jsonify(note)
    except Exception as e:
        return jsonify({'error': error_message(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        note = note_repo.update_note(note_id, data)
        if note is None:
            return jsonify({'error': 'Note not found'}), 404
        return jsonify(note)
    except Exception as e:
        return jsonify({'error': error_message(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        if not note_repo.delete_note(note_id):
            return jsonify({'error': 'Note not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': error_message(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    try:
        return jsonify(note_repo.search_notes(query))
    except Exception as e:
        return jsonify({'error': error_message(e)}), 500

