from flask import Blueprint, jsonify, make_response

bp = Blueprint("docs", __name__)

OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "DigiNews API",
        "version": "1.0.0",
        "description": "Multilingual news platform API",
    },
    "servers": [{"url": "https://diginews.cortigatech.com", "description": "Production"}],
    "components": {
        "securitySchemes": {
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        },
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {"detail": {"type": "string"}}
            },
            "NewsCard": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "language_code": {"type": "string"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "audio_url": {"type": "string", "nullable": True},
                    "audio_duration": {"type": "integer", "nullable": True},
                    "image_url": {"type": "string", "nullable": True},
                    "category_code": {"type": "string", "nullable": True},
                    "category_name": {"type": "string", "nullable": True},
                    "category_icon": {"type": "string", "nullable": True},
                    "category_color": {"type": "string", "nullable": True},
                    "state": {"type": "string", "nullable": True},
                    "city": {"type": "string", "nullable": True},
                    "is_breaking": {"type": "boolean"},
                    "view_count": {"type": "integer"},
                    "like_count": {"type": "integer"},
                    "dislike_count": {"type": "integer"},
                    "published_at": {"type": "string", "format": "date-time"},
                }
            },
            "FeedResponse": {
                "type": "object",
                "properties": {
                    "window": {"type": "string"},
                    "window_start": {"type": "string"},
                    "window_end": {"type": "string"},
                    "next_cursor": {"type": "integer", "nullable": True},
                    "has_more": {"type": "boolean"},
                    "count": {"type": "integer"},
                    "data": {"type": "array", "items": {"$ref": "#/components/schemas/NewsCard"}},
                }
            },
        }
    },
    "paths": {
        # ── AUTH ──────────────────────────────────────────────
        "/auth/guest": {
            "post": {
                "tags": ["Auth"],
                "summary": "Guest login",
                "description": "Create or retrieve a guest user by device_id.",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["device_id", "device_type"],
                        "properties": {
                            "device_id": {"type": "string", "example": "GUEST-abc123"},
                            "device_type": {"type": "string", "enum": ["android", "ios", "web"]},
                            "device_name": {"type": "string", "example": "Samsung Galaxy"},
                        }
                    }}}
                },
                "responses": {
                    "200": {"description": "Token issued", "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "access_token": {"type": "string"},
                            "token_type": {"type": "string"},
                            "user_id": {"type": "integer"},
                            "user_type": {"type": "string"},
                            "is_new": {"type": "boolean"},
                        }
                    }}}},
                    "422": {"description": "Validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                }
            }
        },
        "/auth/google": {
            "post": {
                "tags": ["Auth"],
                "summary": "Google login / register",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["id_token"],
                        "properties": {
                            "id_token": {"type": "string"},
                            "device_id": {"type": "string"},
                        }
                    }}}
                },
                "responses": {
                    "200": {"description": "Tokens issued"},
                    "401": {"description": "Invalid Google token"},
                }
            }
        },
        "/auth/refresh": {
            "post": {
                "tags": ["Auth"],
                "summary": "Refresh access token",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["refresh_token"],
                        "properties": {"refresh_token": {"type": "string"}}
                    }}}
                },
                "responses": {
                    "200": {"description": "New access token"},
                    "401": {"description": "Invalid or expired refresh token"},
                }
            }
        },
        "/auth/logout": {
            "post": {
                "tags": ["Auth"],
                "summary": "Logout (revoke refresh token)",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {"refresh_token": {"type": "string"}}
                    }}}
                },
                "responses": {
                    "200": {"description": "Logged out"},
                    "401": {"description": "Not authenticated"},
                }
            }
        },

        # ── USERS ─────────────────────────────────────────────
        "/users/me": {
            "get": {
                "tags": ["Users"],
                "summary": "Get current user profile",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "User profile"}, "401": {"description": "Not authenticated"}}
            },
            "patch": {
                "tags": ["Users"],
                "summary": "Update profile (name, preferred_lang, state, city…)",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "preferred_lang": {"type": "string", "example": "te"},
                            "state": {"type": "string"},
                            "district": {"type": "string"},
                            "city": {"type": "string"},
                        }
                    }}}
                },
                "responses": {"200": {"description": "Updated profile"}, "401": {"description": "Not authenticated"}}
            }
        },
        "/users/onboarding": {
            "post": {
                "tags": ["Users"],
                "summary": "Complete onboarding (set language, location, categories)",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["preferred_lang"],
                        "properties": {
                            "preferred_lang": {"type": "string", "example": "te"},
                            "state": {"type": "string"},
                            "district": {"type": "string"},
                            "city": {"type": "string"},
                            "lat": {"type": "number"},
                            "lng": {"type": "number"},
                            "categories": {"type": "array", "items": {"type": "string"}},
                        }
                    }}}
                },
                "responses": {"200": {"description": "Onboarding complete"}, "401": {"description": "Not authenticated"}}
            }
        },
        "/users/device-token": {
            "post": {
                "tags": ["Users"],
                "summary": "Register FCM device token",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["fcm_token", "device_type"],
                        "properties": {
                            "fcm_token": {"type": "string"},
                            "device_type": {"type": "string", "enum": ["android", "ios", "web"]},
                            "device_name": {"type": "string"},
                        }
                    }}}
                },
                "responses": {"201": {"description": "Device registered"}, "401": {"description": "Not authenticated"}}
            }
        },
        "/users/device-token/{token_id}": {
            "delete": {
                "tags": ["Users"],
                "summary": "Remove device token",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "token_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Token removed"}, "404": {"description": "Not found"}}
            }
        },
        "/users/device-token/{token_id}/settings": {
            "patch": {
                "tags": ["Users"],
                "summary": "Update notification settings for a device",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "token_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "notifications_enabled": {"type": "boolean"},
                            "notify_breaking": {"type": "boolean"},
                            "notify_location": {"type": "boolean"},
                            "notify_category": {"type": "boolean"},
                            "quiet_hours_enabled": {"type": "boolean"},
                            "quiet_start": {"type": "string", "example": "22:00"},
                            "quiet_end": {"type": "string", "example": "07:00"},
                        }
                    }}}
                },
                "responses": {"200": {"description": "Settings updated"}}
            }
        },
        "/users/filters": {
            "get": {
                "tags": ["Users"],
                "summary": "Get user feed filters",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "Current filters"}}
            },
            "patch": {
                "tags": ["Users"],
                "summary": "Update feed filters",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "categories": {"type": "array", "items": {"type": "string"}},
                            "languages": {"type": "array", "items": {"type": "string"}},
                            "locations": {"type": "array", "items": {"type": "string"}},
                            "default_window": {"type": "string", "enum": ["latest", "today", "yesterday", "older"]},
                        }
                    }}}
                },
                "responses": {"200": {"description": "Updated filters"}}
            }
        },
        "/users/history": {
            "get": {
                "tags": ["Users"],
                "summary": "Get reading history",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "language", "in": "query", "schema": {"type": "string"}},
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                ],
                "responses": {"200": {"description": "History list"}}
            },
            "delete": {
                "tags": ["Users"],
                "summary": "Clear reading history (registered users only)",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "History cleared"}}
            }
        },

        # ── FEEDS ─────────────────────────────────────────────
        "/feeds/": {
            "get": {
                "tags": ["Feeds"],
                "summary": "Get news feed (public)",
                "parameters": [
                    {"name": "language", "in": "query", "required": True, "schema": {"type": "string", "example": "te"}},
                    {"name": "window", "in": "query", "schema": {"type": "string", "enum": ["latest", "today", "yesterday", "older"], "default": "today"}},
                    {"name": "category", "in": "query", "schema": {"type": "string"}},
                    {"name": "city", "in": "query", "schema": {"type": "string"}},
                    {"name": "district", "in": "query", "schema": {"type": "string"}},
                    {"name": "state", "in": "query", "schema": {"type": "string"}},
                    {"name": "national", "in": "query", "schema": {"type": "boolean"}},
                    {"name": "breaking", "in": "query", "schema": {"type": "boolean"}},
                    {"name": "last_id", "in": "query", "schema": {"type": "integer"}},
                    {"name": "after_id", "in": "query", "schema": {"type": "integer"}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20, "maximum": 50}},
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                ],
                "responses": {
                    "200": {"description": "Feed", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/FeedResponse"}}}},
                    "422": {"description": "language is required"},
                }
            }
        },
        "/feeds/trending": {
            "get": {
                "tags": ["Feeds"],
                "summary": "Get trending news (public)",
                "parameters": [
                    {"name": "language", "in": "query", "required": True, "schema": {"type": "string"}},
                    {"name": "city", "in": "query", "schema": {"type": "string"}},
                    {"name": "hours", "in": "query", "schema": {"type": "integer", "default": 24}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 10}},
                ],
                "responses": {"200": {"description": "Trending list"}, "422": {"description": "language is required"}}
            }
        },
        "/feeds/breaking": {
            "get": {
                "tags": ["Feeds"],
                "summary": "Get breaking news (public)",
                "parameters": [
                    {"name": "language", "in": "query", "required": True, "schema": {"type": "string"}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 5}},
                ],
                "responses": {"200": {"description": "Breaking news list"}, "422": {"description": "language is required"}}
            }
        },
        "/feeds/search": {
            "get": {
                "tags": ["Feeds"],
                "summary": "Full-text search news (public)",
                "parameters": [
                    {"name": "q", "in": "query", "required": True, "schema": {"type": "string"}},
                    {"name": "language", "in": "query", "required": True, "schema": {"type": "string"}},
                    {"name": "category", "in": "query", "schema": {"type": "string"}},
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                ],
                "responses": {"200": {"description": "Search results"}}
            }
        },
        "/feeds/bookmarks": {
            "get": {
                "tags": ["Feeds"],
                "summary": "Get bookmarks (registered users only)",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "language", "in": "query", "schema": {"type": "string"}},
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                ],
                "responses": {"200": {"description": "Bookmarks list"}, "401": {"description": "Not authenticated"}}
            }
        },
        "/feeds/{news_id}": {
            "get": {
                "tags": ["Feeds"],
                "summary": "Get article detail (public; tracks read history if logged in)",
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Article detail"}, "404": {"description": "Not found"}}
            }
        },
        "/feeds/{news_id}/read": {
            "post": {
                "tags": ["Feeds"],
                "summary": "Mark article as read / increment view count (public)",
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Marked as read"}}
            }
        },
        "/feeds/{news_id}/share": {
            "post": {
                "tags": ["Feeds"],
                "summary": "Increment share count (public)",
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Share count updated"}}
            }
        },
        "/feeds/{news_id}/react": {
            "post": {
                "tags": ["Feeds"],
                "summary": "React to article — like/dislike (registered users only)",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["reaction"],
                        "properties": {"reaction": {"type": "string", "enum": ["like", "dislike"]}}
                    }}}
                },
                "responses": {"200": {"description": "Reaction result"}, "401": {"description": "Not authenticated"}, "404": {"description": "Not found"}}
            }
        },
        "/feeds/{news_id}/reactions": {
            "get": {
                "tags": ["Feeds"],
                "summary": "Get reaction counts (public; my_reaction included if logged in)",
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Reaction counts and my_reaction"}, "404": {"description": "Not found"}}
            }
        },
        "/feeds/{news_id}/bookmark": {
            "post": {
                "tags": ["Feeds"],
                "summary": "Bookmark article (registered users only)",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"201": {"description": "Bookmarked"}, "401": {"description": "Not authenticated"}}
            },
            "delete": {
                "tags": ["Feeds"],
                "summary": "Remove bookmark (registered users only)",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Bookmark removed"}, "401": {"description": "Not authenticated"}}
            }
        },

        # ── AUDIO ─────────────────────────────────────────────
        "/audio/meta/{news_id}": {
            "get": {
                "tags": ["Audio"],
                "summary": "Get audio metadata",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {
                    "200": {"description": "Audio metadata"},
                    "404": {"description": "Audio not found"},
                }
            }
        },
        "/audio/stream/{news_id}": {
            "get": {
                "tags": ["Audio"],
                "summary": "Stream audio file (supports Range header)",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "Range", "in": "header", "schema": {"type": "string", "example": "bytes=0-"}},
                ],
                "responses": {
                    "200": {"description": "Full audio stream"},
                    "206": {"description": "Partial audio content"},
                    "404": {"description": "Audio not found"},
                }
            }
        },
        "/audio/play/{news_id}": {
            "post": {
                "tags": ["Audio"],
                "summary": "Increment audio play count",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Updated play count"}}
            }
        },

        # ── SUBSCRIPTIONS ─────────────────────────────────────
        "/subscriptions/": {
            "get": {
                "tags": ["Subscriptions"],
                "summary": "List active subscriptions (registered users only)",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "Subscription list"}, "401": {"description": "Not authenticated"}}
            },
            "post": {
                "tags": ["Subscriptions"],
                "summary": "Create subscription (registered users only)",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["type", "language"],
                        "properties": {
                            "type": {"type": "string", "enum": ["location", "category", "keyword"]},
                            "language": {"type": "string", "example": "te"},
                            "state": {"type": "string"},
                            "district": {"type": "string"},
                            "city": {"type": "string"},
                            "category": {"type": "string"},
                            "keyword": {"type": "string"},
                        }
                    }}}
                },
                "responses": {"201": {"description": "Subscribed"}, "409": {"description": "Already exists"}}
            }
        },
        "/subscriptions/{sub_id}": {
            "patch": {
                "tags": ["Subscriptions"],
                "summary": "Pause or resume a subscription (registered users only)",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "sub_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["is_active"],
                        "properties": {"is_active": {"type": "boolean"}}
                    }}}
                },
                "responses": {"200": {"description": "Updated"}, "404": {"description": "Not found"}}
            },
            "delete": {
                "tags": ["Subscriptions"],
                "summary": "Cancel subscription (registered users only)",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "sub_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Cancelled"}, "404": {"description": "Not found"}}
            }
        },

        # ── REFERENCE ─────────────────────────────────────────
        "/languages": {
            "get": {
                "tags": ["Reference"],
                "summary": "List active languages (public)",
                "responses": {"200": {"description": "Languages list"}}
            }
        },
        "/categories": {
            "get": {
                "tags": ["Reference"],
                "summary": "List active categories (public)",
                "responses": {"200": {"description": "Categories list"}}
            }
        },

        # ── ADMIN ─────────────────────────────────────────────
        "/admin/queue": {
            "get": {
                "tags": ["Admin"],
                "summary": "List pending news queue",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "category_code", "in": "query", "schema": {"type": "string"}},
                    {"name": "source", "in": "query", "schema": {"type": "string"}},
                    {"name": "min_score", "in": "query", "schema": {"type": "number"}},
                    {"name": "max_score", "in": "query", "schema": {"type": "number"}},
                ],
                "responses": {"200": {"description": "Queue list"}, "403": {"description": "Admin only"}}
            }
        },
        "/admin/queue/{raw_id}": {
            "get": {
                "tags": ["Admin"],
                "summary": "Get queue item detail",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "raw_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Queue item"}, "404": {"description": "Not found"}}
            },
            "patch": {
                "tags": ["Admin"],
                "summary": "Edit pending queue item",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "raw_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "ai_rewritten": {"type": "string"},
                            "ai_summary": {"type": "string"},
                            "category_code": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                        }
                    }}}
                },
                "responses": {"200": {"description": "Updated"}, "404": {"description": "Not found"}}
            }
        },
        "/admin/queue/{raw_id}/approve": {
            "post": {
                "tags": ["Admin"],
                "summary": "Approve article (triggers translation + TTS)",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "raw_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "is_breaking": {"type": "boolean", "default": False},
                            "use_ai_rewrite": {"type": "boolean", "default": True},
                        }
                    }}}
                },
                "responses": {"200": {"description": "Approved, processing started"}, "404": {"description": "Not found"}}
            }
        },
        "/admin/queue/{raw_id}/reject": {
            "post": {
                "tags": ["Admin"],
                "summary": "Reject article",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "raw_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {"reason": {"type": "string"}}
                    }}}
                },
                "responses": {"200": {"description": "Rejected"}, "404": {"description": "Not found"}}
            }
        },
        "/admin/queue/{raw_id}/breaking": {
            "patch": {
                "tags": ["Admin"],
                "summary": "Toggle breaking flag on queue item",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "raw_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["is_breaking"],
                        "properties": {"is_breaking": {"type": "boolean"}}
                    }}}
                },
                "responses": {"200": {"description": "Updated"}}
            }
        },
        "/admin/published": {
            "get": {
                "tags": ["Admin"],
                "summary": "List published articles",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "language_code", "in": "query", "schema": {"type": "string"}},
                    {"name": "category_code", "in": "query", "schema": {"type": "string"}},
                    {"name": "city", "in": "query", "schema": {"type": "string"}},
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                ],
                "responses": {"200": {"description": "Published list"}}
            }
        },
        "/admin/published/{news_id}": {
            "patch": {
                "tags": ["Admin"],
                "summary": "Edit published article",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "is_breaking": {"type": "boolean"},
                        }
                    }}}
                },
                "responses": {"200": {"description": "Updated"}, "404": {"description": "Not found"}}
            },
            "delete": {
                "tags": ["Admin"],
                "summary": "Unpublish / delete article",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Deleted"}, "404": {"description": "Not found"}}
            }
        },
        "/admin/analytics": {
            "get": {
                "tags": ["Admin"],
                "summary": "Platform analytics (users, news, engagement)",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "Analytics data"}}
            }
        },
        "/admin/users": {
            "get": {
                "tags": ["Admin"],
                "summary": "List all users",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "user_type", "in": "query", "schema": {"type": "string", "enum": ["guest", "registered"]}},
                    {"name": "search", "in": "query", "schema": {"type": "string"}},
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 50}},
                ],
                "responses": {"200": {"description": "Users list"}}
            }
        },
        "/admin/push": {
            "post": {
                "tags": ["Admin"],
                "summary": "Send push notification blast",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["title", "body", "language_code"],
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                            "language_code": {"type": "string"},
                            "state": {"type": "string", "nullable": True},
                            "city": {"type": "string", "nullable": True},
                            "news_id": {"type": "integer", "nullable": True},
                        }
                    }}}
                },
                "responses": {"200": {"description": "Push sent"}}
            }
        },
        "/admin/languages": {
            "post": {
                "tags": ["Admin"],
                "summary": "Add a new language",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["code", "name_english"],
                        "properties": {
                            "code": {"type": "string", "example": "hi"},
                            "name_english": {"type": "string", "example": "Hindi"},
                            "name_native": {"type": "string", "example": "हिन्दी"},
                            "flag_emoji": {"type": "string", "example": "🇮🇳"},
                        }
                    }}}
                },
                "responses": {"201": {"description": "Language created"}, "409": {"description": "Already exists"}}
            }
        },
        "/admin/languages/{lang_id}": {
            "patch": {
                "tags": ["Admin"],
                "summary": "Update a language",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "lang_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "name_english": {"type": "string"},
                            "name_native": {"type": "string"},
                            "flag_emoji": {"type": "string"},
                            "is_active": {"type": "boolean"},
                        }
                    }}}
                },
                "responses": {"200": {"description": "Updated"}, "404": {"description": "Not found"}}
            }
        },
        "/admin/categories": {
            "post": {
                "tags": ["Admin"],
                "summary": "Add a new category",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["code", "name_english"],
                        "properties": {
                            "code": {"type": "string", "example": "politics"},
                            "name_english": {"type": "string", "example": "Politics"},
                            "icon_emoji": {"type": "string", "example": "🏛️"},
                            "color_hex": {"type": "string", "example": "#FF5733"},
                        }
                    }}}
                },
                "responses": {"201": {"description": "Category created"}, "409": {"description": "Already exists"}}
            }
        },
        "/admin/categories/{cat_id}": {
            "patch": {
                "tags": ["Admin"],
                "summary": "Update a category",
                "security": [{"bearerAuth": []}],
                "parameters": [{"name": "cat_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "name_english": {"type": "string"},
                            "icon_emoji": {"type": "string"},
                            "color_hex": {"type": "string"},
                            "is_active": {"type": "boolean"},
                        }
                    }}}
                },
                "responses": {"200": {"description": "Updated"}, "404": {"description": "Not found"}}
            }
        },
    },
    "tags": [
        {"name": "Auth", "description": "Authentication — guest, Google OAuth, token refresh, logout"},
        {"name": "Users", "description": "User profile, onboarding, device tokens, filters, history"},
        {"name": "Feeds", "description": "News feed, search, reactions, bookmarks — most endpoints are public"},
        {"name": "Audio", "description": "Audio streaming and play tracking"},
        {"name": "Subscriptions", "description": "Location / category / keyword subscriptions"},
        {"name": "Reference", "description": "Static reference data — languages and categories"},
        {"name": "Admin", "description": "Admin-only — queue management, publishing, analytics, push"},
    ],
}

SWAGGER_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>DigiNews API Docs</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  SwaggerUIBundle({
    url: "/openapi.json",
    dom_id: '#swagger-ui',
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
    layout: "BaseLayout",
    deepLinking: true,
    persistAuthorization: true,
  })
</script>
</body>
</html>"""


@bp.get("/docs")
def swagger_ui():
    resp = make_response(SWAGGER_HTML)
    resp.content_type = "text/html"
    return resp


@bp.get("/openapi.json")
def openapi_spec():
    return jsonify(OPENAPI_SPEC)
