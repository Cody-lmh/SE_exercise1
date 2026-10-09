"""Translation helper with an OpenRouter backend and a MyMemory fallback.

OpenRouter (https://openrouter.ai/) is preferred whenever ``OPENROUTER_API_KEY``
is set, because a large language model handles arbitrary note content and mixed
source languages better than a sentence-based translation memory.  Without the
key - or when an OpenRouter request fails - the helper falls back to the free
MyMemory API (https://mymemory.translated.net/doc/spec.php), which requires no
credentials and accepts an ``Autodetect`` source language.  A single MyMemory
query is limited to 500 characters, so its input is split into chunks and
reassembled.
"""

import html
import json
import os
import urllib.error
import urllib.parse
import urllib.request

MYMEMORY_ENDPOINT = 'https://api.mymemory.translated.net/get'
OPENROUTER_ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
# Used when OPENROUTER_API_KEY is set but OPENROUTER_MODEL is not.
DEFAULT_OPENROUTER_MODEL = 'nvidia/nemotron-3-ultra-550b-a55b:free'
# MyMemory rejects queries longer than 500 characters; stay comfortably below.
MAX_QUERY_CHARS = 450
REQUEST_TIMEOUT = 15
# A language model can take much longer to answer than a lookup API.
OPENROUTER_TIMEOUT = 60
USER_AGENT = 'NoteTaker/1.0'

SUPPORTED_TARGET_LANGS = {
    'zh-CN': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)',
    'en': 'English',
}
DEFAULT_TARGET_LANG = 'zh-CN'

# MyMemory reports the source language already equals the target with this text.
_SAME_LANGUAGE_MESSAGE = 'PLEASE SELECT TWO DISTINCT LANGUAGES'


class TranslationError(RuntimeError):
    """Raised when the translation service cannot fulfil a request."""


def translate_text(text, target_lang=DEFAULT_TARGET_LANG):
    """Translate ``text`` into ``target_lang`` and return the translated string.

    OpenRouter is tried first when it is configured; any failure there falls
    back to MyMemory so a rate limit or an outage never breaks translation.
    """
    if not text or not text.strip():
        return ''
    if target_lang not in SUPPORTED_TARGET_LANGS:
        raise ValueError(f'Unsupported target language: {target_lang}')

    if _openrouter_credentials():
        try:
            return _translate_with_openrouter(text, target_lang)
        except TranslationError as openrouter_error:
            try:
                return _translate_with_mymemory(text, target_lang)
            except TranslationError as fallback_error:
                raise TranslationError(
                    f'{openrouter_error} (MyMemory fallback also failed: {fallback_error})'
                ) from fallback_error

    return _translate_with_mymemory(text, target_lang)


def _openrouter_credentials():
    """Return ``(api_key, model)`` for OpenRouter, or ``None`` when unconfigured."""
    api_key = (os.environ.get('OPENROUTER_API_KEY') or '').strip()
    if not api_key:
        return None
    model = (os.environ.get('OPENROUTER_MODEL') or '').strip() or DEFAULT_OPENROUTER_MODEL
    return api_key, model


def _translate_with_mymemory(text, target_lang):
    """Translate ``text`` through MyMemory, splitting it across the query limit."""
    return ''.join(_translate_chunk(chunk, target_lang) for chunk in _split_text(text))


def _translate_with_openrouter(text, target_lang):
    """Translate ``text`` in a single OpenRouter chat completion."""
    api_key, model = _openrouter_credentials()
    instruction = (
        f'Translate the text into {SUPPORTED_TARGET_LANGS[target_lang]}. '
        'Reply with the translation only, without explanations or surrounding '
        'quotes, and keep the original line breaks and formatting.'
    )
    body = json.dumps({
        'model': model,
        'messages': [
            {'role': 'system', 'content': instruction},
            {'role': 'user', 'content': text},
        ],
        'temperature': 0,
    }).encode('utf-8')

    payload = _fetch_json(
        OPENROUTER_ENDPOINT,
        data=body,
        timeout=OPENROUTER_TIMEOUT,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'X-Title': USER_AGENT,
        },
    )

    if payload.get('error'):
        raise TranslationError(_error_text(payload['error']))

    choices = payload.get('choices') or []
    message = (choices[0].get('message') or {}) if choices else {}
    translated = str(message.get('content') or '').strip()
    if not translated:
        raise TranslationError('OpenRouter returned an empty response')

    return translated


def _split_text(text, max_len=MAX_QUERY_CHARS):
    """Split ``text`` into chunks of at most ``max_len`` characters.

    Boundaries follow newlines first and then spaces so words and paragraphs
    stay intact.  The delimiter stays attached to the preceding chunk, which
    lets the translated pieces be concatenated without losing spacing.
    """
    chunks = []
    for line in text.splitlines(keepends=True):
        while len(line) > max_len:
            window = line[:max_len]
            split_at = window.rfind('\n')
            if split_at <= 0:
                split_at = window.rfind(' ')
            if split_at <= 0:
                split_at = max_len
            else:
                split_at += 1  # keep the newline/space with the current chunk
            chunks.append(line[:split_at])
            line = line[split_at:]

        if chunks and len(chunks[-1]) + len(line) <= max_len:
            chunks[-1] += line
        else:
            chunks.append(line)

    return [chunk for chunk in chunks if chunk]


def _translate_chunk(chunk, target_lang):
    """Translate a single chunk that already fits within the API query limit."""
    params = urllib.parse.urlencode({
        'q': chunk,
        'langpair': f'Autodetect|{target_lang}',
    })
    payload = _fetch_json(f'{MYMEMORY_ENDPOINT}?{params}')

    details = str(payload.get('responseDetails') or '')
    status = str(payload.get('responseStatus') or '')
    translated = html.unescape(str((payload.get('responseData') or {}).get('translatedText') or ''))

    if _SAME_LANGUAGE_MESSAGE in details.upper() or _SAME_LANGUAGE_MESSAGE in translated.upper():
        return chunk  # Content is already in the target language.

    if status != '200':
        raise TranslationError(details or 'Translation service request failed')

    if not translated:
        raise TranslationError('Translation service returned an empty response')

    if translated.upper().startswith('MYMEMORY WARNING') or 'QUERY LENGTH LIMIT EXCEEDED' in translated.upper():
        raise TranslationError(translated)

    return translated


def _fetch_json(url, data=None, headers=None, timeout=REQUEST_TIMEOUT):
    request_headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json',
    }
    request_headers.update(headers or {})
    request = urllib.request.Request(url, data=data, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or 'utf-8'
            return json.loads(response.read().decode(charset))
    except urllib.error.HTTPError as exc:
        raise TranslationError(_http_error_message(exc)) from exc
    except urllib.error.URLError as exc:
        raise TranslationError('Could not reach the translation service') from exc
    except (TimeoutError, OSError) as exc:
        raise TranslationError('Could not reach the translation service') from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise TranslationError('Translation service returned an invalid response') from exc


def _http_error_message(exc):
    """Report an HTTP failure, keeping the service's own explanation when sent."""
    detail = ''
    try:
        body = json.loads(exc.read().decode('utf-8'))
    except (ValueError, UnicodeDecodeError, OSError):
        body = None
    if isinstance(body, dict):
        detail = _error_text(body.get('error'))
    message = f'Translation service returned HTTP {exc.code}'
    return f'{message}: {detail}' if detail else message


def _error_text(error):
    """Render a service error payload (string or object) as one readable message."""
    if isinstance(error, dict):
        error = error.get('message') or error.get('code') or ''
    return str(error).strip()
