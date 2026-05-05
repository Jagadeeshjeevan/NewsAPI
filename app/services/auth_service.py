from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings
from app.core.security import hash_token, create_refresh_token
from app.models.models import User, UserFilter, RefreshToken


def verify_google_token(token: str) -> dict:
    return id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        settings.GOOGLE_CLIENT_ID,
    )


def get_or_create_guest(db: Session, device_id: str, device_type: str, device_name: str | None) -> tuple[User, bool]:
    user = db.query(User).filter(User.device_id == device_id).first()
    if user:
        user.last_seen = datetime.utcnow()
        db.commit()
        return user, False

    user = User(
        user_type="guest",
        device_id=device_id,
        preferred_lang="te",
        last_seen=datetime.utcnow(),
    )
    db.add(user)
    db.flush()

    db.add(UserFilter(user_id=user.id, default_window="today"))
    db.commit()
    db.refresh(user)
    return user, True


def upgrade_or_create_registered(db: Session, google_id: str, email: str, name: str, profile_pic: str, device_id: str) -> tuple[User, bool]:
    user = db.query(User).filter(User.google_id == google_id).first()
    if user:
        user.last_login = datetime.utcnow()
        user.last_seen = datetime.utcnow()
        db.commit()
        return user, False

    guest = db.query(User).filter(User.device_id == device_id, User.user_type == "guest").first()
    if guest:
        guest.user_type = "registered"
        guest.google_id = google_id
        guest.email = email
        guest.name = name
        guest.profile_pic = profile_pic
        guest.last_login = datetime.utcnow()
        guest.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(guest)
        return guest, False

    user = User(
        user_type="registered",
        device_id=device_id,
        google_id=google_id,
        email=email,
        name=name,
        profile_pic=profile_pic,
        last_login=datetime.utcnow(),
        last_seen=datetime.utcnow(),
    )
    db.add(user)
    db.flush()
    db.add(UserFilter(user_id=user.id, default_window="today"))
    db.commit()
    db.refresh(user)
    return user, True


def store_refresh_token(db: Session, user_id: int, user_type: str) -> str:
    token = create_refresh_token(user_id, user_type)
    expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user_id, token_hash=hash_token(token), expires_at=expires))
    db.commit()
    return token


def revoke_refresh_token(db: Session, user_id: int, token: str):
    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_token(token),
        RefreshToken.user_id == user_id,
    ).first()
    if record:
        record.is_revoked = 1
        db.commit()
