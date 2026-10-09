"""User persistence backed by the Supabase ``users`` table."""

from src.db import USERS_TABLE, get_client

FIELDS = ('id', 'username', 'email')


def _serialize(row: dict) -> dict:
    """Shape a stored row like the JSON payload the API returns."""
    return {field: row.get(field) for field in FIELDS}


def _rows(response) -> list:
    return response.data or []


def list_users() -> list:
    """Return every user."""
    response = get_client().table(USERS_TABLE).select('*').execute()
    return [_serialize(row) for row in _rows(response)]


def get_user(user_id: int):
    """Return a single user, or ``None`` when it does not exist."""
    response = (
        get_client()
        .table(USERS_TABLE)
        .select('*')
        .eq('id', user_id)
        .limit(1)
        .execute()
    )
    rows = _rows(response)
    return _serialize(rows[0]) if rows else None


def create_user(username: str, email: str) -> dict:
    """Insert a user and return the stored row."""
    response = (
        get_client()
        .table(USERS_TABLE)
        .insert({'username': username, 'email': email})
        .execute()
    )
    return _serialize(_rows(response)[0])


def update_user(user_id: int, data: dict):
    """Update the supplied fields, or ``None`` when the user is gone."""
    updates = {field: data[field] for field in ('username', 'email') if field in data}
    if not updates:
        return get_user(user_id)

    response = (
        get_client()
        .table(USERS_TABLE)
        .update(updates)
        .eq('id', user_id)
        .execute()
    )
    rows = _rows(response)
    return _serialize(rows[0]) if rows else None


def delete_user(user_id: int) -> bool:
    """Delete a user, reporting whether a row was removed."""
    response = (
        get_client()
        .table(USERS_TABLE)
        .delete()
        .eq('id', user_id)
        .execute()
    )
    return bool(_rows(response))
