from flask import Flask
from flask_cors import CORS
from routers import news

app = Flask(__name__)
CORS(app)

app.register_blueprint(news.bp, url_prefix="/api/v1")


@app.route("/")
def root():
    return {"message": "DigiNews API is running"}


@app.route("/health")
def health():
    return {"status": "ok"}
