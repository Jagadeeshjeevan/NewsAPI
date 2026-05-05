from datetime import datetime
from flask import Blueprint, request, jsonify, g
from app.core.database import get_db
from app.dependencies.auth import auth_required, registered_required
from app.models.models import UserFilter, UserDeviceToken, UserReadHistory, News, Category
from app.schemas.schemas import UserUpdateRequest, OnboardingRequest, DeviceTokenRequest, DeviceTokenSettingsRequest, FiltersUpdateRequest

bp = Blueprint("users", __name__)


def _user_out(user, db):
    row = db.query(UserFilter).filter(UserFilter.user_id == user.id).first()
    return {
        "id": user.id, "user_type": user.user_type, "name": user.name,
        "email": user.email, "profile_pic": user.profile_pic,
        "preferred_lang": user.preferred_lang, "state": user.state,
        "district": user.district, "city": user.city, "is_admin": bool(user.is_admin),
        "filters": {
            "categories": row.categories or [], "languages": row.languages or [],
            "locations": row.locations or [], "default_window": row.default_window,
        } if row else {},
        "created_at": user.created_at,
    }


# API 5: GET /users/me
@bp.get("/me")
@auth_required
def get_me():
    db = get_db()
    return jsonify(_user_out(g.current_user, db))


# API 6: PATCH /users/me
@bp.patch("/me")
@auth_required
def update_me():
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = UserUpdateRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(g.current_user, field, val)
    db.commit()
    db.refresh(g.current_user)
    return jsonify(_user_out(g.current_user, db))


# API 7: POST /users/onboarding
@bp.post("/onboarding")
@auth_required
def onboarding():
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = OnboardingRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422

    u = g.current_user
    u.preferred_lang = body.preferred_lang
    u.state = body.state
    u.district = body.district
    u.city = body.city
    u.lat = body.lat
    u.lng = body.lng
    u.anchor_time = datetime.utcnow()
    db.commit()

    row = db.query(UserFilter).filter(UserFilter.user_id == u.id).first()
    if row:
        row.categories = body.categories or []
        row.default_window = "today"
    else:
        db.add(UserFilter(user_id=u.id, categories=body.categories or [], default_window="today"))
    db.commit()
    return jsonify({"message": "Onboarding complete", "user_id": u.id})


# API 8: POST /users/device-token
@bp.post("/device-token")
@auth_required
def register_device():
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = DeviceTokenRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422

    existing = db.query(UserDeviceToken).filter(
        UserDeviceToken.user_id == g.current_user.id,
        UserDeviceToken.fcm_token == body.fcm_token,
    ).first()
    if existing:
        existing.last_active = datetime.utcnow()
        db.commit()
        return jsonify({"id": existing.id, "message": "Device registered for notifications"}), 201

    device = UserDeviceToken(
        user_id=g.current_user.id, fcm_token=body.fcm_token,
        device_type=body.device_type, device_name=body.device_name,
        last_active=datetime.utcnow(),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return jsonify({"id": device.id, "message": "Device registered for notifications"}), 201


# API 9: DELETE /users/device-token/<token_id>
@bp.delete("/device-token/<int:token_id>")
@auth_required
def delete_device(token_id):
    db = get_db()
    device = db.query(UserDeviceToken).filter(UserDeviceToken.id == token_id).first()
    if not device:
        return jsonify({"detail": "Device token not found"}), 404
    if device.user_id != g.current_user.id:
        return jsonify({"detail": "Forbidden"}), 403
    db.delete(device)
    db.commit()
    return jsonify({"message": "Device token removed"})


# API 10: PATCH /users/device-token/<token_id>/settings
@bp.patch("/device-token/<int:token_id>/settings")
@auth_required
def update_device_settings(token_id):
    db = get_db()
    device = db.query(UserDeviceToken).filter(UserDeviceToken.id == token_id).first()
    if not device:
        return jsonify({"detail": "Device token not found"}), 404
    if device.user_id != g.current_user.id:
        return jsonify({"detail": "Forbidden"}), 403
    data = request.get_json(force=True) or {}
    try:
        body = DeviceTokenSettingsRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(device, field, val)
    db.commit()
    return jsonify({"id": device.id, "notifications_enabled": bool(device.notifications_enabled),
                    "notify_breaking": bool(device.notify_breaking),
                    "notify_location": bool(device.notify_location),
                    "notify_category": bool(device.notify_category),
                    "quiet_hours_enabled": bool(device.quiet_hours_enabled)})


# API 11: GET /users/filters
@bp.get("/filters")
@auth_required
def get_filters():
    db = get_db()
    row = db.query(UserFilter).filter(UserFilter.user_id == g.current_user.id).first()
    if not row:
        return jsonify({"categories": [], "languages": [], "locations": [], "default_window": "today"})
    return jsonify({"categories": row.categories or [], "languages": row.languages or [],
                    "locations": row.locations or [], "default_window": row.default_window})


# API 12: PATCH /users/filters
@bp.patch("/filters")
@auth_required
def update_filters():
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = FiltersUpdateRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    row = db.query(UserFilter).filter(UserFilter.user_id == g.current_user.id).first()
    if not row:
        row = UserFilter(user_id=g.current_user.id)
        db.add(row)
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(row, field, val)
    db.commit()
    return jsonify({"categories": row.categories or [], "languages": row.languages or [],
                    "locations": row.locations or [], "default_window": row.default_window})


# API 38: GET /users/history
@bp.get("/history")
@auth_required
def get_history():
    db = get_db()
    language = request.args.get("language")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    q = db.query(UserReadHistory, News).join(
        News, UserReadHistory.news_id == News.id
    ).filter(UserReadHistory.user_id == g.current_user.id)
    if language:
        q = q.filter(News.language_code == language)
    total = q.count()
    rows = q.order_by(UserReadHistory.read_at.desc()).offset((page - 1) * limit).limit(limit).all()
    data = [{"read_at": h.read_at, "news": {"id": n.id, "title": n.title,
             "language_code": n.language_code, "published_at": n.published_at}} for h, n in rows]
    return jsonify({"total": total, "page": page, "data": data})


# API 39: DELETE /users/history
@bp.delete("/history")
@registered_required
def clear_history():
    db = get_db()
    db.query(UserReadHistory).filter(UserReadHistory.user_id == g.current_user.id).delete()
    db.commit()
    return jsonify({"message": "Reading history cleared"})
