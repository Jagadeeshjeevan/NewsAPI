from flask import Blueprint, jsonify, request, abort
from models.news import NewsArticle
from datetime import datetime

bp = Blueprint("news", __name__, url_prefix="/news")

SAMPLE_ARTICLES = [
    NewsArticle(
        id=1,
        title="Flutter 4.0 Released with Major Performance Improvements",
        description="Google announces Flutter 4.0 with significantly improved rendering and new widget APIs.",
        content="Flutter 4.0 brings a host of improvements including a new Impeller rendering engine...",
        author="Jane Doe",
        category="technology",
        image_url="https://picsum.photos/seed/flutter/800/400",
        source="TechCrunch",
        published_at=datetime(2026, 5, 1, 10, 0, 0),
        url="https://example.com/flutter-4",
    ),
    NewsArticle(
        id=2,
        title="AI Dominates Global Tech Landscape in 2026",
        description="Artificial intelligence continues to reshape industries worldwide.",
        content="From healthcare to finance, AI adoption has accelerated dramatically...",
        author="John Smith",
        category="technology",
        image_url="https://picsum.photos/seed/ai/800/400",
        source="BBC Technology",
        published_at=datetime(2026, 5, 2, 8, 30, 0),
        url="https://example.com/ai-2026",
    ),
    NewsArticle(
        id=3,
        title="Global Markets Reach Record Highs Amid Economic Recovery",
        description="Stock markets around the world hit all-time highs as economies stabilize.",
        content="Investors are optimistic as GDP growth figures exceed expectations...",
        author="Alice Johnson",
        category="business",
        image_url="https://picsum.photos/seed/market/800/400",
        source="Financial Times",
        published_at=datetime(2026, 5, 3, 9, 0, 0),
        url="https://example.com/markets",
    ),
    NewsArticle(
        id=4,
        title="Climate Summit Reaches Historic Agreement",
        description="World leaders agree on binding emissions targets at the 2026 Climate Summit.",
        content="Over 190 nations signed the landmark agreement committing to net-zero emissions by 2045...",
        author="Bob Lee",
        category="world",
        image_url="https://picsum.photos/seed/climate/800/400",
        source="Reuters",
        published_at=datetime(2026, 5, 4, 7, 0, 0),
        url="https://example.com/climate",
    ),
]


@bp.route("/")
def get_news():
    category = request.args.get("category")
    limit = min(max(int(request.args.get("limit", 10)), 1), 100)
    offset = max(int(request.args.get("offset", 0)), 0)

    articles = SAMPLE_ARTICLES
    if category:
        articles = [a for a in articles if a.category == category]

    paginated = articles[offset : offset + limit]
    return jsonify({
        "status": "ok",
        "total": len(articles),
        "articles": [a.model_dump(mode="json") for a in paginated],
    })


@bp.route("/categories/list")
def get_categories():
    categories = sorted({a.category for a in SAMPLE_ARTICLES})
    return jsonify({"categories": categories})


@bp.route("/<int:article_id>")
def get_article(article_id):
    article = next((a for a in SAMPLE_ARTICLES if a.id == article_id), None)
    if not article:
        abort(404, description="Article not found")
    return jsonify(article.model_dump(mode="json"))
