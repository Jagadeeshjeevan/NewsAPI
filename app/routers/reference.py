from flask import Blueprint, jsonify
from app.core.database import get_db
from app.core import redis as cache_store
from app.models.models import Language, Category

bp = Blueprint("reference", __name__)


# API 47: GET /languages
@bp.get("/languages")
def get_languages():
    cached = cache_store.cache_get("ref:languages")
    if cached:
        return jsonify(cached)
    db = get_db()
    rows = db.query(Language).filter(Language.is_active == 1).order_by(Language.sort_order).all()
    data = {"data": [{"id": l.id, "code": l.code, "name_english": l.name_english,
                      "name_native": l.name_native, "flag_emoji": l.flag_emoji} for l in rows]}
    cache_store.cache_set("ref:languages", data, 3600)
    return jsonify(data)


# API 48: GET /categories
@bp.get("/categories")
def get_categories():
    cached = cache_store.cache_get("ref:categories")
    if cached:
        return jsonify(cached)
    db = get_db()
    rows = db.query(Category).filter(Category.is_active == 1).order_by(Category.sort_order).all()
    data = {"data": [{"id": c.id, "code": c.code, "name_english": c.name_english,
                      "icon_emoji": c.icon_emoji, "color_hex": c.color_hex} for c in rows]}
    cache_store.cache_set("ref:categories", data, 3600)
    return jsonify(data)
