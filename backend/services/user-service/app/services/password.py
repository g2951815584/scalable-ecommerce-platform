"""argon2id password hashing and strength validation."""

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError
from common.errors import AppError

from app.core.config import get_settings

# Duck-typed so tests can inject a cheap hasher without spinning up argon2 memory.
_password_hasher: PasswordHasher | None = None


def _hasher() -> PasswordHasher:
    global _password_hasher
    if _password_hasher is None:
        settings = get_settings()
        _password_hasher = PasswordHasher(
            time_cost=settings.argon2_time_cost,
            memory_cost=settings.argon2_memory_cost_kib,
            parallelism=settings.argon2_parallelism,
            type=Type.ID,
        )
    return _password_hasher


def hash_password(password: str) -> str:
    return _hasher().hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher().verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:  # malformed hash
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher().check_needs_rehash(password_hash)
    except Exception:
        return False


def validate_strength(password: str) -> None:
    settings = get_settings()
    if len(password) < settings.password_min_length or len(password) > settings.password_max_length:
        raise AppError("USER-1004", "密码强度不足", 400)
    if any(char.isspace() for char in password):
        raise AppError("USER-1004", "密码强度不足", 400)
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise AppError("USER-1004", "密码强度不足", 400)