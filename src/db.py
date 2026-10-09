"""Supabase wiring shared by the models.

The application stores everything in a Supabase project, so every data-access
module goes through the client returned by :func:`get_client`. Credentials come
from the environment (``SUPABASE_URL`` and ``SUPABASE_KEY``); locally they are
read from a ``.env`` file at the repository root.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

# Only used for local development; deployments provide real environment
# variables, in which case there is no .env file and this call is a no-op.
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

NOTES_TABLE = 'notes'
USERS_TABLE = 'users'


class SupabaseConfigError(RuntimeError):
    """Raised when the Supabase credentials are not configured."""


def error_message(error: Exception) -> str:
    """Turn a Supabase/PostgREST error into one readable sentence.

    ``str()`` on a PostgREST ``APIError`` yields the whole JSON payload, which is
    hard to read; prefer its ``message`` field and keep the error code.
    """
    message = getattr(error, 'message', None)
    if not message:
        return str(error)
    code = getattr(error, 'code', None)
    return f'{message} ({code})' if code else message


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Return the process-wide Supabase client, creating it on first use."""
    url = (os.environ.get('SUPABASE_URL') or '').strip()
    key = (os.environ.get('SUPABASE_KEY') or '').strip()
    if not url or not key:
        raise SupabaseConfigError(
            'SUPABASE_URL and SUPABASE_KEY must be set; see .env.example.'
        )
    return create_client(url, key)
