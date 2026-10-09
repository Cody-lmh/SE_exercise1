from flask import Blueprint, jsonify, request

from src.db import error_message
from src.models import user as user_repo

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_repo.list_users())

@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json(silent=True)
        if not data or 'username' not in data or 'email' not in data:
            return jsonify({'error': 'Username and email are required'}), 400

        user = user_repo.create_user(data['username'], data['email'])
        return jsonify(user), 201
    except Exception as e:
        return jsonify({'error': error_message(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = user_repo.get_user(user_id)
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user)
    except Exception as e:
        return jsonify({'error': error_message(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        user = user_repo.update_user(user_id, data)
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user)
    except Exception as e:
        return jsonify({'error': error_message(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        if not user_repo.delete_user(user_id):
            return jsonify({'error': 'User not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': error_message(e)}), 500
