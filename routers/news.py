from fastapi import APIRouter, HTTPException, Query
from models.news import NewsArticle, NewsResponse
from datetime import datetime

router = APIRouter(prefix="/news", tags=["news"])

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


@router.get("/", response_model=NewsResponse)
def get_news(
    category: str = Query(default=None, description="Filter by category"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    articles = SAMPLE_ARTICLES
    if category:
        articles = [a for a in articles if a.category == category]
    paginated = articles[offset : offset + limit]
    return NewsResponse(status="ok", total=len(articles), articles=paginated)


@router.get("/{article_id}", response_model=NewsArticle)
def get_article(article_id: int):
    article = next((a for a in SAMPLE_ARTICLES if a.id == article_id), None)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("/categories/list")
def get_categories():
    categories = list({a.category for a in SAMPLE_ARTICLES})
    return {"categories": sorted(categories)}
