"""
Frontier Science & Tech Crawler
Continuous collection pipeline: fetches from all sources, classifies, stores.
Replaces the old daily report generation workflow.
"""

import os
import sys
import json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
os.chdir(SCRIPT_DIR)

from config import DATA_SOURCES_CONFIG, EMAIL_CONFIG, SERVER_CONFIG
from data_sources import get_all_data_sources
from classifier import seed_taxonomy, classify_and_store_article
from knowledge_store import init_knowledge_store, get_stats, get_articles, get_category_tree, get_tags
from subscription_manager import init_db as init_subscriptions_db
from utils.logger import setup_logger
from utils.config_loader import load_env_file

load_env_file()
logger = setup_logger("Crawler")


def crawl_all_sources() -> dict:
    """Fetch from all data sources, classify, and store articles."""
    init_knowledge_store()
    init_subscriptions_db()
    seed_taxonomy()

    data_sources = get_all_data_sources()
    total_fetched = 0
    total_stored = 0

    for source in data_sources:
        try:
            logger.info(f"Fetching from {source.name}...")
            news_items = source.fetch()
            fetched = len(news_items)
            total_fetched += fetched

            stored = 0
            for item in news_items:
                article_id = classify_and_store_article(
                    title=item.title,
                    url=item.url,
                    source_name=item.source or source.name,
                    description=item.description or "",
                    author=item.author or "",
                    published_date=item.date_published or datetime.now().strftime("%Y-%m-%d"),
                    language="zh" if any('\u4e00' <= c <= '\u9fff' for c in item.title) else "en"
                )
                if article_id:
                    stored += 1

            total_stored += stored
            logger.info(f"  {source.name}: {fetched} fetched, {stored} stored")

        except Exception as e:
            logger.error(f"Error fetching from {source.name}: {str(e)}")

    logger.info(f"Total: {total_fetched} fetched, {total_stored} stored")
    return {"fetched": total_fetched, "stored": total_stored}


def generate_frontend_data():
    """Generate JSON data for the frontend: categories, trending, latest articles."""
    web_data_dir = os.path.join(SCRIPT_DIR, "web", "data")
    os.makedirs(web_data_dir, exist_ok=True)

    category_tree = get_category_tree()
    articles = get_articles(limit=100, order_by="published_date")
    stats = get_stats()
    tags = get_tags(limit=50)

    # Generate trending tags
    company_tags = get_tags(tag_type="company", limit=20)
    tech_tags = get_tags(tag_type="technology", limit=30)
    all_tags = get_tags(limit=100)
  
    output = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stats": stats,
        "categories": category_tree,
        "latest_articles": articles,
        "tags": {
            "all": all_tags,
            "companies": company_tags,
            "technologies": tech_tags
        },
        "trending": {
            "companies": company_tags,
            "technologies": tech_tags
        }
    }

    output_path = os.path.join(web_data_dir, "knowledge.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"Frontend data generated: {output_path}")
    return output


def send_topic_notifications():
    """Send notifications to subscribers about new content in their topics."""
    from subscription_manager import get_connection as sub_conn
    
    conn = sub_conn()
    try:
        # Get all distinct subscribers with their topic preferences
        cursor = conn.execute("""
            SELECT DISTINCT email, category_id, tag_id, frequency
            FROM topic_subscriptions WHERE verified = 1
        """)
        subscriptions = [dict(row) for row in cursor.fetchall()]
    except Exception:
        subscriptions = []
    finally:
        conn.close()

    if not subscriptions:
        logger.info("No subscriptions to notify")
        return

    # For now, topic-based notification comes through the daily email flow
    # which now sends to all subscribers via the EmailDistributor
    logger.info(f"Found {len(subscriptions)} topic subscriptions")


def main():
    logger.info("=" * 60)
    logger.info("Frontier Science & Tech Crawler")
    logger.info("=" * 60)

    try:
        crawl_all_sources()
        generate_frontend_data()
        send_topic_notifications()
        logger.info("Crawl complete")
    except Exception as e:
        logger.error(f"Crawl failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()


