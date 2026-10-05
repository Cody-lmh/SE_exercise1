from flask import Blueprint, jsonify, request

from src.services.translator import (
    DEFAULT_TARGET_LANG,
    SUPPORTED_TARGET_LANGS,
    TranslationError,
    translate_text,
)

translate_bp = Blueprint('translate', __name__)


@translate_bp.route('/translate', methods=['POST'])
def translate():
    """Translate arbitrary text into one of the supported target languages."""
    data = request.get_json(silent=True) or {}
    content = str(data.get('content') or '').strip()
    target_lang = str(data.get('target_lang') or DEFAULT_TARGET_LANG).strip()

    if not content:
        return jsonify({'error': 'Content is required'}), 400
    if target_lang not in SUPPORTED_TARGET_LANGS:
        return jsonify({'error': f'Unsupported target language: {target_lang}'}), 400

    try:
        translated = translate_text(content, target_lang)
        return jsonify({
            'source_content': content,
            'translated_content': translated,
            'target_lang': target_lang,
        })
    except TranslationError as e:
        return jsonify({'error': str(e)}), 502
    except Exception as e:
        return jsonify({'error': str(e)}), 500
