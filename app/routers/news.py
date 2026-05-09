from flask import Blueprint, request, jsonify, g
from app.core.database import get_db
from app.dependencies.auth import registered_required
from app.models.models import NewsRaw, Category
from app.schemas.schemas import NewsSubmitRequest

bp = Blueprint("news", __name__)


# API 13: POST /news/submit
@bp.post("/submit")
@registered_required
def submit_news():
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = NewsSubmitRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422

    cat = db.query(Category).filter(Category.code == body.category_code, Category.is_active == 1).first()
    if not cat:
        return jsonify({"detail": "Invalid category_code"}), 422

    try:
        from langdetect import detect
        lang = detect(body.content)
    except Exception:
        lang = "en"

    raw = NewsRaw(
        source="manual",
        original_text=f"{body.title}\n\n{body.content}",
        original_lang=lang,
        image_url=body.image_url,
        category_id=cat.id,
        category_code=cat.code,
        state=body.state,
        district=body.district,
        city=body.city,
        status="pending",
        submitted_by=g.current_user.id,
    )
    db.add(raw)
    db.commit()
    db.refresh(raw)
    return jsonify({"id": raw.id, "message": "News submitted for review", "status": "pending"}), 201
