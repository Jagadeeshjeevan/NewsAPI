from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import UserDeviceToken, User

_firebase_initialized = False


def _init_firebase():
    global _firebase_initialized
    if not settings.FIREBASE_ENABLED or _firebase_initialized:
        return
    try:
        import firebase_admin
        from firebase_admin import credentials
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
    except Exception:
        pass


def _is_quiet_hours(device: UserDeviceToken) -> bool:
    if not device.quiet_hours_enabled:
        return False
    now_time = datetime.utcnow().time()
    start = device.quiet_start
    end = device.quiet_end
    if start <= end:
        return start <= now_time <= end
    return now_time >= start or now_time <= end


def send_push_to_devices(tokens: list[str], title: str, body: str, data: dict = None) -> tuple[int, int]:
    if not settings.FIREBASE_ENABLED or not tokens:
        return 0, 0
    _init_firebase()
    if not _firebase_initialized:
        return 0, 0

    from firebase_admin import messaging
    sent = 0
    for i in range(0, len(tokens), 500):
        batch = tokens[i:i + 500]
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            tokens=batch,
        )
        try:
            result = messaging.send_each_for_multicast(message)
            sent += result.success_count
        except Exception:
            pass

    return len(tokens), sent


def send_admin_blast(db: Session, title: str, body: str, language_code: str,
                     state: str | None, city: str | None, news_id: int | None) -> dict:
    if not settings.FIREBASE_ENABLED:
        return {"message": "Push notifications disabled", "devices_targeted": 0, "devices_sent": 0}

    q = db.query(UserDeviceToken).join(User, UserDeviceToken.user_id == User.id).filter(
        UserDeviceToken.notifications_enabled == 1,
        User.preferred_lang == language_code,
    )
    if state:
        q = q.filter(User.state == state)
    if city:
        q = q.filter(User.city == city)

    devices = q.all()
    tokens = [d.fcm_token for d in devices if not _is_quiet_hours(d)]
    targeted, sent = send_push_to_devices(tokens, title, body, {"news_id": str(news_id or "")})
    return {"message": "Push notification sent", "devices_targeted": targeted, "devices_sent": sent}
