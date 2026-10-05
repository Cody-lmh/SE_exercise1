"""Translation helper backed by the free MyMemory API.

MyMemory (https://mymemory.translated.net/doc/spec.php) requires no API key and
accepts an ``Autodetect`` source language, which makes it a good fit for
translating arbitrary note content.  A single query is limited to 500
characters, so longer notes are split into chunks and reassembled.
"""

import html
import json
import urllib.error
import urllib.parse
import urllib.request

MYMEMORY_ENDPOINT = 'https://api.mymemory.translated.net/get'
# MyMemory rejects queries longer than 500 characters; stay comfortably below.
MAX_QUERY_CHARS = 450
REQUEST_TIMEOUT = 15
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
    """Translate ``text`` into ``target_lang`` and return the translated string."""
    if not text or not text.strip():
        return ''
    if target_lang not in SUPPORTED_TARGET_LANGS:
        raise ValueError(f'Unsupported target language: {target_lang}')

    return ''.join(_translate_chunk(chunk, target_lang) for chunk in _split_text(text))


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


def _fetch_json(url):
    request = urllib.request.Request(url, headers={
        'User-Agent': USER_AGENT,
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            charset = response.headers.get_content_charset() or 'utf-8'
            return json.loads(response.read().decode(charset))
    except urllib.error.HTTPError as exc:
        raise TranslationError(f'Translation service returned HTTP {exc.code}') from exc
    except urllib.error.URLError as exc:
        raise TranslationError('Could not reach the translation service') from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise TranslationError('Translation service returned an invalid response') from exc
