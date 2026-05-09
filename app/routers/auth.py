import hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from jose import JWTError
from app.core.database import get_db
from app.core.security import create_access_token, decode_token, hash_token
from app.dependencies.auth import auth_required
from app.models.models import RefreshToken, User
from app.schemas.schemas import AdminLoginRequest, GuestLoginRequest, GoogleLoginRequest, RefreshTokenRequest, LogoutRequest
from app.services import auth_service

bp = Blueprint("auth", __name__)


# API 0: POST /auth/admin-login
@bp.post("/admin-login")
def admin_login():
    data = request.get_json(force=True) or {}
    try:
        body = AdminLoginRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422

    db = get_db()
    pw_hash = hashlib.sha256(body.password.encode()).hexdigest()
    user = db.query(User).filter(
        User.email == body.email.strip().lower(),
        User.password_hash == pw_hash,
        User.is_admin == 1,
        User.is_active == 1,
    ).first()
    if not user:
        return jsonify({"detail": "Invalid credentials or not an admin"}), 401

    user.last_login = datetime.utcnow()
    db.commit()
    token = create_access_token(user.id, user.user_type)
    return jsonify({"access_token": token, "token_type": "bearer",
                    "user_id": user.id, "name": user.name or user.email})


# API 1: POST /auth/guest
@bp.post("/guest")
def guest_login():
    data = request.get_json(force=True) or {}
    try:
        body = GuestLoginRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    if not body.device_id.startswith("GUEST-"):
        return jsonify({"detail": "Invalid device_id format"}), 422

    db = get_db()
    user, is_new = auth_service.get_or_create_guest(db, body.device_id, body.device_type, body.device_name)
    token = create_access_token(user.id, user.user_type)
    return jsonify({"access_token": token, "token_type": "bearer",
                    "user_id": user.id, "user_type": user.user_type, "is_new": is_new})


# API 2: POST /auth/google
@bp.post("/google")
def google_login():
    data = request.get_json(force=True) or {}
    try:
        body = GoogleLoginRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422

    db = get_db()
    try:
        payload = auth_service.verify_google_token(body.id_token)
    except Exception:
        return jsonify({"detail": "Invalid Google token"}), 401

    user, is_new = auth_service.upgrade_or_create_registered(
        db, payload["sub"], payload.get("email", ""),
        payload.get("name", ""), payload.get("picture", ""), body.device_id,
    )
    access = create_access_token(user.id, user.user_type)
    refresh = auth_service.store_refresh_token(db, user.id, user.user_type)
    return jsonify({
        "access_token": access, "refresh_token": refresh, "token_type": "bearer",
        "user_id": user.id, "user_type": user.user_type, "is_new_user": is_new,
        "name": user.name, "profile_pic": user.profile_pic,
    })


# API 3: POST /auth/refresh
@bp.post("/refresh")
def refresh_token():
    data = request.get_json(force=True) or {}
    token = data.get("refresh_token", "")
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError
        user_id = int(payload["sub"])
        user_type = payload["user_type"]
    except (JWTError, ValueError, KeyError):
        return jsonify({"detail": "Invalid refresh token"}), 401

    db = get_db()
    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_token(token),
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == 0,
    ).first()
    if not record or record.expires_at < datetime.utcnow():
        return jsonify({"detail": "Token revoked or expired"}), 401

    return jsonify({"access_token": create_access_token(user_id, user_type), "token_type": "bearer"})


# API 4: POST /auth/logout
@bp.post("/logout")
@auth_required
def logout():
    data = request.get_json(force=True) or {}
    db = get_db()
    auth_service.revoke_refresh_token(db, g.current_user.id, data.get("refresh_token", ""))
    return jsonify({"message": "Logged out successfully"})
