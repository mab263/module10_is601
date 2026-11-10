import pytest

from app.security import MAX_PASSWORD_BYTES, hash_password, verify_password


def test_hash_is_not_the_plain_password():
    password_hash = hash_password("secret123")
    assert password_hash != "secret123"
    assert password_hash.startswith("$2")  # bcrypt prefix


def test_correct_password_verifies():
    assert verify_password("secret123", hash_password("secret123")) is True


@pytest.mark.parametrize("attempt", ["wrong", "Secret123", "secret123 ", ""])
def test_wrong_password_does_not_verify(attempt):
    assert verify_password(attempt, hash_password("secret123")) is False


def test_same_password_gets_different_hashes_that_both_verify():
    first = hash_password("secret123")
    second = hash_password("secret123")
    assert first != second  # each hash has its own random salt
    assert verify_password("secret123", first)
    assert verify_password("secret123", second)


def test_unicode_password_round_trip():
    password = "pässwörd-密码"
    assert verify_password(password, hash_password(password))


def test_password_at_the_byte_limit_is_accepted():
    password = "a" * MAX_PASSWORD_BYTES
    assert verify_password(password, hash_password(password))


def test_password_over_the_byte_limit_is_rejected():
    with pytest.raises(ValueError, match="72 bytes"):
        hash_password("a" * (MAX_PASSWORD_BYTES + 1))


def test_limit_counts_bytes_not_characters():
    with pytest.raises(ValueError):
        hash_password("密" * 25)  # 25 characters, but 75 bytes


def test_empty_password_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        hash_password("")


def test_over_long_attempt_never_verifies():
    assert verify_password("a" * 100, hash_password("secret123")) is False


@pytest.mark.parametrize("bad_hash", ["", "not-a-hash", "$2b$12$tooshort"])
def test_malformed_stored_hash_does_not_verify(bad_hash):
    assert verify_password("secret123", bad_hash) is False