from functools import wraps
from flask import request, g, jsonify
from jose import JWTError
from app.core.security import decode_token
from app.core.database import get_db
from app.models.models import User


def _get_current_user():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, (jsonify({"detail": "Not authenticated"}), 401)
    token = auth[7:]
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        return None, (jsonify({"detail": "Invalid or expired token"}), 401)

    db = get_db()
    user = db.query(User).filter(User.id == user_id, User.is_active == 1).first()
    if not user:
        return None, (jsonify({"detail": "User not found"}), 401)
    return user, None


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, err = _get_current_user()
        if err:
            return err
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def registered_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, err = _get_current_user()
        if err:
            return err
        if user.user_type != "registered":
            return jsonify({"detail": "Login required"}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, err = _get_current_user()
        if err:
            return err
        if not user.is_admin:
            return jsonify({"detail": "Admin access required"}), 403
        g.current_user = user
        return f(*args, **kwargs)
    return decorated
