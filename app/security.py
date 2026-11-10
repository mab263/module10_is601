"""Password hashing helpers using bcrypt."""

import bcrypt

# bcrypt only uses the first 72 bytes of a password, and bcrypt 5.x
# raises an error for anything longer, so longer passwords are rejected.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    """Return a salted bcrypt hash of the password, safe to store in the database.

    Raises:
        ValueError: if the password is empty or longer than 72 bytes.
    """
    if not password:
        raise ValueError("Password must not be empty")
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        raise ValueError("Password must be at most 72 bytes")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return True if plain_password matches the stored hash, otherwise False."""
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:  # LBYL: can't match a valid hash
        return False
    try:  # EAFP: a malformed stored hash raises, and that just means no match
        return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
    except ValueError:
        return False