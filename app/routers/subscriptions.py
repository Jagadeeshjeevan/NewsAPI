from flask import Blueprint, request, jsonify, g
from app.core.database import get_db
from app.dependencies.auth import registered_required
from app.models.models import Subscription, Category
from app.schemas.schemas import SubscriptionCreate, SubscriptionPatch

bp = Blueprint("subscriptions", __name__)


# API 43: GET /subscriptions/
@bp.get("/")
@registered_required
def list_subscriptions():
    db = get_db()
    rows = db.query(Subscription).filter(
        Subscription.user_id == g.current_user.id, Subscription.is_active == 1
    ).order_by(Subscription.created_at.desc()).all()
    return jsonify({"total": len(rows), "data": [
        {"id": s.id, "type": s.type, "language": s.language, "city": s.city,
         "state": s.state, "category": s.category, "keyword": s.keyword,
         "is_active": bool(s.is_active), "created_at": s.created_at} for s in rows
    ]})


# API 44: POST /subscriptions/
@bp.post("/")
@registered_required
def create_subscription():
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = SubscriptionCreate(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422

    if body.type == "location" and not any([body.state, body.district, body.city]):
        return jsonify({"detail": "At least one location field required"}), 422
    if body.type == "category":
        if not body.category:
            return jsonify({"detail": "category required"}), 422
        if not db.query(Category).filter(Category.code == body.category).first():
            return jsonify({"detail": "Invalid category"}), 422
    if body.type == "keyword" and (not body.keyword or len(body.keyword) < 3):
        return jsonify({"detail": "keyword must be at least 3 characters"}), 422

    existing = db.query(Subscription).filter(
        Subscription.user_id == g.current_user.id,
        Subscription.type == body.type,
        Subscription.language == body.language,
        Subscription.city == body.city,
        Subscription.category == body.category,
        Subscription.keyword == body.keyword,
    ).first()
    if existing:
        return jsonify({"detail": "Subscription already exists"}), 409

    sub = Subscription(user_id=g.current_user.id, **body.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return jsonify({"id": sub.id, "type": sub.type, "language": sub.language,
                    "city": sub.city, "message": "Subscribed successfully"}), 201


# API 45: PATCH /subscriptions/<id>
@bp.patch("/<int:sub_id>")
@registered_required
def toggle_subscription(sub_id):
    db = get_db()
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        return jsonify({"detail": "Subscription not found"}), 404
    if sub.user_id != g.current_user.id:
        return jsonify({"detail": "Forbidden"}), 403
    data = request.get_json(force=True) or {}
    try:
        body = SubscriptionPatch(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    sub.is_active = 1 if body.is_active else 0
    db.commit()
    msg = "Subscription resumed" if body.is_active else "Subscription paused"
    return jsonify({"id": sub.id, "is_active": body.is_active, "message": msg})


# API 46: DELETE /subscriptions/<id>
@bp.delete("/<int:sub_id>")
@registered_required
def delete_subscription(sub_id):
    db = get_db()
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        return jsonify({"detail": "Subscription not found"}), 404
    if sub.user_id != g.current_user.id:
        return jsonify({"detail": "Forbidden"}), 403
    db.delete(sub)
    db.commit()
    return jsonify({"message": "Subscription cancelled"})
