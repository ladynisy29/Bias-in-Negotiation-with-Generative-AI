import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

from users_api.models import UserProfile, UserSessionToken


def hash_user_password(raw_password: str) -> str:
    return make_password(raw_password, hasher="bcrypt_sha256")


def verify_user_password(raw_password: str, password_hash: str) -> bool:
    if not raw_password or not password_hash:
        return False
    return check_password(raw_password, password_hash)


def create_access_token(user: UserProfile, ttl_hours: int | None = None) -> tuple[str, UserSessionToken]:
    token_ttl = ttl_hours if ttl_hours is not None else int(getattr(settings, "ACCESS_TOKEN_TTL_HOURS", 12))
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token = UserSessionToken.objects.create(
        user=user,
        token_prefix=raw_token[:16],
        token_hash=token_hash,
        expires_at=timezone.now() + timedelta(hours=token_ttl),
    )
    return raw_token, token


def revoke_access_token(raw_token: str) -> None:
    if not raw_token:
        return
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    UserSessionToken.objects.filter(token_hash=token_hash, revoked_at__isnull=True).update(revoked_at=timezone.now())


def get_authenticated_user(request) -> UserProfile:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise NotAuthenticated("Missing Bearer token.")

    raw_token = auth_header.removeprefix("Bearer ").strip()
    if not raw_token:
        raise NotAuthenticated("Missing Bearer token.")

    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token = UserSessionToken.objects.select_related("user").filter(token_hash=token_hash).first()
    if token is None:
        raise AuthenticationFailed("Invalid token.")

    if token.revoked_at is not None:
        raise AuthenticationFailed("Token has been revoked.")

    if token.expires_at <= timezone.now():
        raise AuthenticationFailed("Token has expired.")

    token.last_used_at = timezone.now()
    token.save(update_fields=["last_used_at"])
    return token.user
