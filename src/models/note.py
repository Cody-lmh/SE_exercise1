"""Note persistence backed by the Supabase ``notes`` table."""

from datetime import datetime, timezone

from src.db import NOTES_TABLE, get_client

FIELDS = ('id', 'title', 'content', 'created_at', 'updated_at')


def _serialize(row: dict) -> dict:
    """Shape a stored row like the JSON payload the API returns."""
    return {
        field: row[field].isoformat()
        if isinstance(row.get(field), datetime)
        else row.get(field)
        for field in FIELDS
    }


def _escape_like(value: str) -> str:
    """Escape LIKE metacharacters so the search term matches literally."""
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def _quote(value: str) -> str:
    r"""Quote a filter value, escaping PostgREST reserved characters.

    Values containing ``,``, ``.``, ``:`` or ``()`` have to be wrapped in
    double quotes, and inside those quotes a backslash escapes ``"`` and ``\``.
    """
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _rows(response) -> list:
    return response.data or []


def list_notes() -> list:
    """Return every note, most recently updated first."""
    response = (
        get_client()
        .table(NOTES_TABLE)
        .select('*')
        .order('updated_at', desc=True)
        .execute()
    )
    return [_serialize(row) for row in _rows(response)]


def get_note(note_id: int):
    """Return a single note, or ``None`` when it does not exist."""
    response = (
        get_client()
        .table(NOTES_TABLE)
        .select('*')
        .eq('id', note_id)
        .limit(1)
        .execute()
    )
    rows = _rows(response)
    return _serialize(rows[0]) if rows else None


def create_note(title: str, content: str) -> dict:
    """Insert a note and return the stored row."""
    response = (
        get_client()
        .table(NOTES_TABLE)
        .insert({'title': title, 'content': content})
        .execute()
    )
    return _serialize(_rows(response)[0])


def update_note(note_id: int, data: dict):
    """Update the supplied fields, or ``None`` when the note is gone.

    ``updated_at`` is set here as well as by a database trigger so that
    "recently updated" ordering stays correct even if the trigger is absent.
    """
    updates = {field: data[field] for field in ('title', 'content') if field in data}
    if not updates:
        return get_note(note_id)

    updates['updated_at'] = datetime.now(timezone.utc).isoformat()
    response = (
        get_client()
        .table(NOTES_TABLE)
        .update(updates)
        .eq('id', note_id)
        .execute()
    )
    rows = _rows(response)
    return _serialize(rows[0]) if rows else None


def delete_note(note_id: int) -> bool:
    """Delete a note, reporting whether a row was removed."""
    response = (
        get_client()
        .table(NOTES_TABLE)
        .delete()
        .eq('id', note_id)
        .execute()
    )
    return bool(_rows(response))


def search_notes(query: str) -> list:
    """Case-insensitively match notes whose title or content contains query."""
    pattern = _quote(f'%{_escape_like(query)}%')
    response = (
        get_client()
        .table(NOTES_TABLE)
        .select('*')
        .or_(f'title.ilike.{pattern},content.ilike.{pattern}')
        .order('updated_at', desc=True)
        .execute()
    )
    return [_serialize(row) for row in _rows(response)]

