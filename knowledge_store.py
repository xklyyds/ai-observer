"""
Frontier Science & Tech Knowledge Store
SQLite-based article storage with rich classification and tagging.
"""

import sqlite3
import hashlib
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger("KnowledgeStore")

DEFAULT_DB_PATH = str(Path(__file__).parent / "knowledge.db")

def get_db_path() -> str:
    try:
        from config import SERVER_CONFIG
        return SERVER_CONFIG.get("db_path") or DEFAULT_DB_PATH
    except (ImportError, KeyError):
        return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_knowledge_store():
    conn = get_connection()
    
    # Categories - hierarchical taxonomy
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            parent_id INTEGER,
            description TEXT,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
    """)
    
    # Sources
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            source_type TEXT NOT NULL,
            url TEXT,
            language TEXT DEFAULT 'zh',
            active INTEGER DEFAULT 1
        )
    """)
    
    # Articles - the core entity
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            source_id INTEGER,
            source_name TEXT,
            description TEXT,
            content_snippet TEXT,
            author TEXT,
            published_date TEXT,
            fetched_date TEXT DEFAULT (datetime('now')),
            language TEXT DEFAULT 'zh',
            quality_score INTEGER DEFAULT 0,
            importance TEXT DEFAULT 'normal',
            url_hash TEXT UNIQUE NOT NULL,
            FOREIGN KEY (source_id) REFERENCES sources(id)
        )
    """)
    
    # Tags - extracted entities and concepts
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            tag_type TEXT NOT NULL,
            description TEXT
        )
    """)
    
    # Article-Category many-to-many
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_categories (
            article_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            confidence REAL DEFAULT 1.0,
            PRIMARY KEY (article_id, category_id),
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    
    # Article-Tag many-to-many
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_tags (
            article_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (article_id, tag_id),
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    """)
    
    # Subscriptions - per user, per topic
    conn.execute("""
        CREATE TABLE IF NOT EXISTS topic_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            category_id INTEGER,
            tag_id INTEGER,
            frequency TEXT DEFAULT 'daily',
            verified INTEGER DEFAULT 0,
            token TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    """)
    
    # Indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_date DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_quality ON articles(quality_score)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_lang ON articles(language)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_article_cats_cat ON article_categories(category_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_article_tags_tag ON article_tags(tag_id)")
    
    conn.commit()
    conn.close()
    logger.info("Knowledge store initialized")


# ============================================================
# Article CRUD
# ============================================================

def insert_article(title: str, url: str, source_name: str, description: str = "",
                   author: str = "", published_date: str = "", language: str = "zh",
                   content_snippet: str = "", quality_score: int = 0,
                   importance: str = "normal") -> Optional[int]:
    url_hash = hashlib.md5(url.encode()).hexdigest()
    conn = get_connection()
    try:
        # Upsert pattern: if url exists, update; else insert
        conn.execute("""
            INSERT INTO articles
                (title, url, source_name, description, author, published_date,
                 language, content_snippet, quality_score, importance, url_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url_hash) DO UPDATE SET
                title=excluded.title, description=excluded.description,
                author=excluded.author, quality_score=excluded.quality_score,
                importance=excluded.importance, fetched_date=datetime('now')
        """, (title, url, source_name, description, author, published_date,
              language, content_snippet, quality_score, importance, url_hash))
        conn.commit()
        cursor = conn.execute("SELECT id FROM articles WHERE url_hash = ?", (url_hash,))
        row = cursor.fetchone()
        return row["id"] if row else None
    except Exception as e:
        logger.error(f"Failed to insert article '{title}': {e}")
        return None
    finally:
        conn.close()


def get_articles(category_slug: str = None, tag_name: str = None,
                 source_id: int = None, language: str = None,
                 importance: str = None, search: str = None,
                 limit: int = 50, offset: int = 0,
                 order_by: str = "published_date") -> List[Dict]:
    conn = get_connection()
    try:
        query = "SELECT DISTINCT a.* FROM articles a"
        params = []
        conditions = []

        if category_slug:
            query += " JOIN article_categories ac ON a.id = ac.article_id"
            query += " JOIN categories c ON ac.category_id = c.id"
            if '/' in category_slug:
                # Include subcategories
                conditions.append("(c.slug = ? OR c.slug LIKE ?)")
                params.extend([category_slug, category_slug + '/%'])
            else:
                conditions.append("c.slug = ?")
                params.append(category_slug)

        if tag_name:
            query += " JOIN article_tags at ON a.id = at.article_id"
            query += " JOIN tags t ON at.tag_id = t.id"
            conditions.append("t.name = ?")
            params.append(tag_name)

        if source_id is not None:
            conditions.append("a.source_id = ?")
            params.append(source_id)

        if language is not None:
            conditions.append("a.language = ?")
            params.append(language)

        if importance is not None:
            conditions.append("a.importance = ?")
            params.append(importance)

        if search:
            conditions.append("(a.title LIKE ? OR a.description LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        order_map = {
            "published_date": "a.published_date DESC, a.quality_score DESC",
            "quality": "a.quality_score DESC, a.published_date DESC",
            "fetched": "a.fetched_date DESC"
        }
        query += f" ORDER BY {order_map.get(order_by, order_map['published_date'])} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        articles = []
        for row in cursor.fetchall():
            article = dict(row)
            article["categories"] = _get_article_categories(conn, article["id"])
            article["tags"] = _get_article_tags(conn, article["id"])
            articles.append(article)

        return articles
    except Exception as e:
        logger.error(f"Failed to query articles: {e}")
        return []
    finally:
        conn.close()


def get_article_count(category_slug: str = None, tag_name: str = None,
                      source_id: int = None, language: str = None,
                      importance: str = None, search: str = None) -> int:
    conn = get_connection()
    try:
        query = "SELECT COUNT(DISTINCT a.id) FROM articles a"
        params = []
        conditions = []

        if category_slug:
            query += " JOIN article_categories ac ON a.id = ac.article_id"
            query += " JOIN categories c ON ac.category_id = c.id"
            if '/' in category_slug:
                conditions.append("(c.slug = ? OR c.slug LIKE ?)")
                params.extend([category_slug, category_slug + '/%'])
            else:
                conditions.append("c.slug = ?")
                params.append(category_slug)

        if tag_name:
            query += " JOIN article_tags at ON a.id = at.article_id"
            query += " JOIN tags t ON at.tag_id = t.id"
            conditions.append("t.name = ?")
            params.append(tag_name)

        if source_id is not None:
            conditions.append("a.source_id = ?")
            params.append(source_id)

        if language is not None:
            conditions.append("a.language = ?")
            params.append(language)

        if importance is not None:
            conditions.append("a.importance = ?")
            params.append(importance)

        if search:
            conditions.append("(a.title LIKE ? OR a.description LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor = conn.execute(query, params)
        return cursor.fetchone()[0]
    except Exception:
        return 0
    finally:
        conn.close()


def get_trending_categories(days: int = 7, limit: int = 10) -> List[Dict]:
    conn = get_connection()
    try:
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor = conn.execute("""
            SELECT c.id, c.name, c.slug, COUNT(ac.article_id) as article_count
            FROM categories c
            JOIN article_categories ac ON c.id = ac.category_id
            JOIN articles a ON ac.article_id = a.id
            WHERE a.published_date >= ?
            GROUP BY c.id
            ORDER BY article_count DESC
            LIMIT ?
        """, (cutoff, limit))
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Failed to get trending: {e}")
        return []
    finally:
        conn.close()


# ============================================================
# Category CRUD
# ============================================================

def get_category_tree() -> List[Dict]:
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM categories ORDER BY sort_order, name")
        rows = [dict(row) for row in cursor.fetchall()]
        return _build_tree(rows)
    except Exception:
        return []
    finally:
        conn.close()


def _build_tree(rows: List[Dict], parent_id: int = None) -> List[Dict]:
    tree = []
    for row in rows:
        if row.get("parent_id") == parent_id:
            node = dict(row)
            children = _build_tree(rows, row["id"])
            if children:
                node["children"] = children
            tree.append(node)
    return tree


# ============================================================
# Tag CRUD
# ============================================================

def get_tags(tag_type: str = None, limit: int = 100) -> List[Dict]:
    conn = get_connection()
    try:
        if tag_type:
            cursor = conn.execute(
                "SELECT t.*, COUNT(at.article_id) as article_count "
                "FROM tags t LEFT JOIN article_tags at ON t.id = at.tag_id "
                "WHERE t.tag_type = ? GROUP BY t.id ORDER BY article_count DESC LIMIT ?",
                (tag_type, limit)
            )
        else:
            cursor = conn.execute(
                "SELECT t.*, COUNT(at.article_id) as article_count "
                "FROM tags t LEFT JOIN article_tags at ON t.id = at.tag_id "
                "GROUP BY t.id ORDER BY article_count DESC LIMIT ?",
                (limit,)
            )
        return [dict(row) for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


# ============================================================
# Helpers
# ============================================================

def _get_article_categories(conn: sqlite3.Connection, article_id: int) -> List[Dict]:
    cursor = conn.execute("""
        SELECT c.id, c.name, c.slug, ac.confidence
        FROM article_categories ac JOIN categories c ON ac.category_id = c.id
        WHERE ac.article_id = ?
    """, (article_id,))
    return [dict(row) for row in cursor.fetchall()]


def _get_article_tags(conn: sqlite3.Connection, article_id: int) -> List[Dict]:
    cursor = conn.execute("""
        SELECT t.id, t.name, t.tag_type
        FROM article_tags at JOIN tags t ON at.tag_id = t.id
        WHERE at.article_id = ?
    """, (article_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_stats() -> Dict:
    conn = get_connection()
    try:
        stats = {}
        cursor = conn.execute("SELECT COUNT(*) FROM articles")
        stats["total_articles"] = cursor.fetchone()[0]
        cursor = conn.execute("SELECT COUNT(*) FROM categories")
        stats["total_categories"] = cursor.fetchone()[0]
        cursor = conn.execute("SELECT COUNT(*) FROM tags")
        stats["total_tags"] = cursor.fetchone()[0]
          cursor = conn.execute("SELECT COUNT(DISTINCT source_name) FROM articles")
          stats["active_sources"] = cursor.fetchone()[0] or 0
        cursor = conn.execute(
            "SELECT COUNT(DISTINCT email) FROM topic_subscriptions WHERE verified = 1"
        )
        stats["subscribers"] = cursor.fetchone()[0]
        cursor = conn.execute(
            "SELECT MAX(published_date) FROM articles"
        )
        row = cursor.fetchone()
        stats["latest_update"] = row[0] if row and row[0] else None
        return stats
    except Exception:
        return {}
    finally:
        conn.close()
