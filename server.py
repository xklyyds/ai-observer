import os
import sys
import json
import smtplib
from email.message import EmailMessage
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
os.chdir(SCRIPT_DIR)

try:
    from flask import Flask, request, jsonify, send_from_directory
except ImportError:
    print("Flask is not installed. Run: pip install flask")
    sys.exit(1)

from config import EMAIL_CONFIG, SERVER_CONFIG
from subscription_manager import (
    init_db, add_subscriber, verify_subscriber,
    remove_subscriber, get_verified_subscribers
)
from knowledge_store import (
    init_knowledge_store, get_articles, get_article_count,
    get_category_tree, get_tags, get_stats
)
from classifier import seed_taxonomy
from utils.logger import setup_logger
from utils.config_loader import load_env_file

load_env_file()
logger = setup_logger("Server")

app = Flask(__name__, static_folder="web", static_url_path="")
app.secret_key = SERVER_CONFIG.get("secret_key", "change-this")


# === Initialization ===
init_knowledge_store()
init_db()
seed_taxonomy()


# === Email Helpers ===

def send_verification_email(recipient_email: str, token: str) -> bool:
    if not EMAIL_CONFIG.get("sender_email") or not EMAIL_CONFIG.get("sender_password"):
        logger.warning("Email not configured")
        return False

    domain = SERVER_CONFIG.get("domain", "http://localhost:5000")
    verify_link = f"{domain}/api/verify?email={recipient_email}&token={token}"

    msg = EmailMessage()
    msg["Subject"] = "订阅确认 - 前沿科技观察"
    msg["From"] = EMAIL_CONFIG["sender_email"]
    msg["To"] = recipient_email
    msg.set_content(f"感谢订阅！请点击链接确认：{verify_link}")
    msg.add_alternative(
        f"""<html><body style="font-family:Arial;max-width:600px;margin:0 auto;padding:20px;">
        <h2 style="color:#00D4FF;">前沿科技观察 - 订阅确认</h2>
        <p>您可以选择关注的领域，我们会按您的偏好推送最新的前沿科技动态。</p>
        <p style="text-align:center;margin:30px 0;">
            <a href="{verify_link}" style="background:#00D4FF;color:#fff;padding:12px 30px;
            text-decoration:none;border-radius:8px;font-size:16px;">确认订阅</a></p>
        <hr><p style="color:#999;font-size:12px;">如未订阅请忽略此邮件</p></body></html>""",
        subtype="html"
    )

    try:
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.send_message(msg)
        logger.info(f"Verification email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Send failed: {e}")
        return False


# === API: Knowledge Browsing ===

@app.route("/api/articles")
def api_articles():
    category = request.args.get("category", "").strip()
    tag = request.args.get("tag", "").strip()
    source_id = request.args.get("source_id", type=int)
    language = request.args.get("language", "").strip()
    importance = request.args.get("importance", "").strip()
    search = request.args.get("search", "").strip()
    order_by = request.args.get("order_by", "published_date").strip()
    page = request.args.get("page", 1, type=int)
    limit = min(request.args.get("limit", 30, type=int), 100)
    offset = (page - 1) * limit

    articles = get_articles(
        category_slug=category or None,
        tag_name=tag or None,
        source_id=source_id,
        language=language or None,
        importance=importance or None,
        search=search or None,
        limit=limit, offset=offset,
        order_by=order_by
    )
    total = get_article_count(
        category_slug=category or None,
        tag_name=tag or None,
        source_id=source_id,
        language=language or None,
        importance=importance or None,
        search=search or None
    )

    return jsonify({
        "articles": articles,
        "total": total,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit)
    })


@app.route("/api/categories")
def api_categories():
    tree = get_category_tree()
    return jsonify({"categories": tree})


@app.route("/api/tags")
def api_tags():
    tag_type = request.args.get("type", "").strip()
    limit = min(request.args.get("limit", 100, type=int), 200)
    tags = get_tags(tag_type=tag_type or None, limit=limit)
    return jsonify({"tags": tags})


@app.route("/api/trending")
def api_trending():
    days = request.args.get("days", 7, type=int)
    from knowledge_store import get_trending_categories
    trending = get_trending_categories(days=days, limit=15)
    return jsonify({"trending": trending})


@app.route("/api/stats")
def api_stats():
    stats = get_stats()
    stats["subscriberCount"] = len(get_verified_subscribers())
    return jsonify(stats)


# === API: Subscription ===

@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(silent=True)
    if not data or "email" not in data:
        return jsonify({"status": "error", "message": "请输入邮箱地址"}), 400

    email = data["email"].strip().lower()
    if not email or "@" not in email or "." not in email:
        return jsonify({"status": "error", "message": "请输入有效的邮箱地址"}), 400

    result = add_subscriber(email)

    if result["status"] == "already_subscribed":
        return jsonify({"status": "success", "message": "您已经订阅过了"})
    elif result["status"] in ("success", "pending"):
        token = result.get("verification_token", "")
        email_sent = send_verification_email(email, token)
        return jsonify({
            "status": "success",
            "message": "请查收验证邮件并点击确认链接" if email_sent
                       else "订阅成功，但邮件发送失败"
        })
    else:
        return jsonify({"status": "error", "message": result.get("message", "订阅失败")}), 500


@app.route("/api/verify")
def verify():
    email = request.args.get("email", "").strip().lower()
    token = request.args.get("token", "").strip()
    if not email or not token:
        return _verify_page(False, "缺少验证参数")

    success = verify_subscriber(email, token)
    return _verify_page(success, "验证成功" if success else "验证失败，链接可能已过期")


def _verify_page(success: bool, msg: str):
    icon = "✓" if success else "✗"
    color = "#00D4FF" if success else "#FF4444"
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>验证 - 前沿科技观察</title>
    <style>body{{font-family:Arial;display:flex;justify-content:center;align-items:center;
    height:100vh;margin:0;background:#0A1628;color:#fff}}
    .card{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
    border-radius:16px;padding:40px;text-align:center;max-width:420px}}
    .icon{{font-size:64px;color:{color};margin-bottom:20px}}h2{{margin:0 0 12px}}
    p{{color:#8899AA;line-height:1.6}}a{{color:#00D4FF;text-decoration:none}}
    </style></head><body><div class="card"><div class="icon">{icon}</div>
    <h2>{"验证成功" if success else "验证失败"}</h2><p>{msg}</p>
    <p><a href="/">返回首页</a></p></div></body></html>"""
    return html, 200 if success else 400, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/api/unsubscribe", methods=["POST"])
def unsubscribe():
    data = request.get_json(silent=True)
    if not data or "email" not in data:
        return jsonify({"status": "error", "message": "请输入邮箱地址"}), 400
    email = data["email"].strip().lower()
    remove_subscriber(email)
    return jsonify({"status": "success", "message": "已取消订阅"})


# === Static Serving ===

@app.route("/")
def serve_index():
    return send_from_directory(os.path.join(SCRIPT_DIR, "web"), "index.html")


@app.route("/<path:path>")
def serve_static(path):
    file_path = os.path.join(SCRIPT_DIR, "web", path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(os.path.join(SCRIPT_DIR, "web"), path)
    return send_from_directory(os.path.join(SCRIPT_DIR, "web"), "index.html")


if __name__ == "__main__":
    host = SERVER_CONFIG.get("host", "0.0.0.0")
    port = SERVER_CONFIG.get("port", 5000)
    logger.info(f"Server at http://localhost:{port}")
    print(f"Knowledge explorer at http://localhost:{port}")
    app.run(host=host, port=port, debug=True)
