"""
Article classification and tagging engine.
Uses keyword matching to classify articles into a hierarchical taxonomy
and extract entity tags (companies, technologies, people).
"""

import re
import logging
import sqlite3
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field

# ============================================================
# Taxonomy Definition
# ============================================================

TAXONOMY = {
    "ai": {
        "name": "人工智能",
        "description": "人工智能与机器学习领域的前沿进展",
        "icon": "brain-circuit",
        "keywords": ["大语言模型", "LLM", "GPT", "Claude", "transformer", "扩散模型",
                      "扩散", "生成式AI", "AIGC", "深度学习", "神经网络", "强化学习",
                      "RLHF", "多模态", "智能体", "agent", "agi", "通用人工智能"],
        "children": {
            "ai/llm": {
                "name": "大语言模型",
                "keywords": ["大语言模型", "LLM", "GPT", "Claude", "Gemini", "Llama",
                             "Qwen", "ChatGPT", "语言模型", "token", "上下文窗口",
                             "few-shot", "prompt", "预训练", "微调", "RLHF",
                             "scaling law", "MoE", "混合专家"]
            },
            "ai/cv": {
                "name": "计算机视觉",
                "keywords": ["计算机视觉", "CV", "图像识别", "目标检测", "分割",
                             "ViT", "vision transformer", "扩散模型", "SDXL",
                             "Stable Diffusion", "DALL-E", "Midjourney", "Sora",
                             "视频生成", "3D生成"]
            },
            "ai/nlp": {
                "name": "自然语言处理",
                "keywords": ["自然语言处理", "NLP", "文本生成", "机器翻译", "情感分析",
                             "命名实体", "文本理解", "embedding", "RAG", "检索增强",
                             "向量数据库"]
            },
            "ai/infra": {
                "name": "AI基础设施",
                "keywords": ["GPU", "TPU", "NPU", "芯片", "H100", "B200", "算力",
                             "训练集群", "推理优化", "量化", "蒸馏", "分布式训练",
                             "CUDA", "PyTorch", "JAX", "vLLM", "模型部署"]
            },
            "ai/safety": {
                "name": "AI安全与对齐",
                "keywords": ["AI安全", "对齐", "alignment", "可解释性", "explainability",
                             "红队", "red team", "越狱", "jailbreak", "幻觉",
                             "hallucination", "安全", "伦理", "bias", "公平性"]
            },
            "ai/app": {
                "name": "AI应用",
                "keywords": ["AI应用", "编程助手", "Copilot", "Cursor", "AI编程",
                             "AI搜索", "AI绘画", "AI写作", "AI教育", "AI医疗",
                             "AI金融", "AI法律", "AI客服", "code generation"]
            }
        }
    },

    "quantum": {
        "name": "量子科技",
        "keywords": ["量子计算", "量子", "qubit", "量子比特", "量子纠错", "量子霸权",
                      "quantum supremacy", "量子芯片", "量子通信", "量子密钥", "退火"],
        "children": {
            "quantum/computing": {
                "name": "量子计算",
                "keywords": ["量子计算", "量子处理器", "qubit", "量子纠错", "量子门",
                             "超导量子", "离子阱", "光量子", "拓扑量子", "量子优势",
                             "quantum processor", "sycamore", "willow"]
            },
            "quantum/comm": {
                "name": "量子通信",
                "keywords": ["量子通信", "量子密钥", "QKD", "量子网络", "量子中继",
                             "量子互联网", "纠缠分发", "量子隐形传态"]
            }
        }
    },

    "biotech": {
        "name": "生物科技",
        "keywords": ["基因编辑", "CRISPR", "蛋白质", "AlphaFold", "基因组", "DNA",
                      "RNA", "mRNA", "细胞", "生物", "合成生物学", "脑机接口"],
        "children": {
            "biotech/genome": {
                "name": "基因编辑与基因组学",
                "keywords": ["基因编辑", "CRISPR", "Cas9", "Cas12", "基因组",
                             "基因治疗", "碱基编辑", "prime editing", "表观遗传",
                             "基因组测序", "单细胞测序", "空间转录组"]
            },
            "biotech/protein": {
                "name": "蛋白质科学",
                "keywords": ["蛋白质", "AlphaFold", "RoseTTAFold", "ESMFold",
                             "蛋白质设计", "蛋白质工程", "蛋白质折叠", "结构预测",
                             "蛋白质相互作用", "酶设计", "抗体设计"]
            },
            "biotech/brain": {
                "name": "脑科学与脑机接口",
                "keywords": ["脑机接口", "BCI", "Neuralink", "脑科学", "神经科学",
                             "神经信号", "脑电", "EEG", "fMRI", "神经元", "突触",
                             "connectome", "全脑图谱"]
            },
            "biotech/synthetic": {
                "name": "合成生物学",
                "keywords": ["合成生物学", "合成生命", "人造细胞", "基因回路",
                             "代谢工程", "生物制造", "微生物组", "工程菌"]
            }
        }
    },

    "materials": {
        "name": "新材料",
        "keywords": ["材料", "半导体", "纳米", "超导", "石墨烯", "钙钛矿", "二维材料",
                      "拓扑材料", "电池材料", "薄膜"],
        "children": {
            "materials/chip": {
                "name": "半导体与芯片",
                "keywords": ["半导体", "芯片", "晶体管", "FinFET", "GAA", "EUV",
                             "光刻", "台积电", "TSMC", "英特尔", "intel", "AMD",
                             "NVIDIA", "高通", "三星", "3nm", "2nm", "chiplet",
                             "先进封装", "HBM", "DRAM", "NAND"]
            },
            "materials/nano": {
                "name": "纳米材料",
                "keywords": ["纳米材料", "石墨烯", "碳纳米管", "二维材料", "MXene",
                             "量子点", "纳米颗粒", "MOF", "COF", "气凝胶"]
            },
            "materials/superconductor": {
                "name": "超导材料",
                "keywords": ["超导", "室温超导", "LK-99", "超导体", "迈斯纳效应",
                             "铜氧化物", "铁基超导", "镍基超导", "高压超导"]
            }
        }
    },

    "computing": {
        "name": "计算科学与系统",
        "keywords": ["计算机", "性能", "分布式", "云", "安全", "漏洞", "编程",
                      "编译器", "操作系统", "数据库", "网络", "协议"],
        "children": {
            "computing/os": {
                "name": "开源与基础软件",
                "keywords": ["开源", "OpenAI", "Llama", "开源模型", "GitHub",
                             "Git", "Linux", "内核", "编译", "编程语言", "Rust",
                             "Zig", "Mojo", "WASM", "WebAssembly", "容器", "Kubernetes"]
            },
            "computing/security": {
                "name": "网络安全与密码学",
                "keywords": ["安全", "漏洞", "CVE", "攻击", "防御", "加密",
                             "密码", "零信任", "zero trust", "后量子密码",
                             "同态加密", "联邦学习", "隐私计算", "数据安全"]
            },
            "computing/cloud": {
                "name": "云计算与基础设施",
                "keywords": ["云", "AWS", "Azure", "GCP", "serverless", "Docker",
                             "Kubernetes", "微服务", "边缘计算", "数据中心", "液冷"]
            }
        }
    },

    "space": {
        "name": "航天与天文",
        "keywords": ["航天", "火箭", "SpaceX", "发射", "卫星", "空间站", "月球",
                      "火星", "天文", "望远镜", "系外行星", "黑洞", "引力波"],
        "children": {
            "space/launch": {
                "name": "航天发射与探索",
                "keywords": ["火箭", "发射", "SpaceX", "Starship", "Falcon",
                             "嫦娥", "天问", "Artemis", "载人", "空间站", "月球",
                             "火星", "NASA", "CNSA", "ESA", "ISRO"]
            },
            "space/astronomy": {
                "name": "天文观测",
                "keywords": ["望远镜", "JWST", "韦伯", "哈勃", "EHT", "FAST",
                             "系外行星", "黑洞", "暗物质", "暗能量", "宇宙学",
                             "引力波", "LIGO", "脉冲星", "超新星"]
            },
            "space/satellite": {
                "name": "卫星与遥感",
                "keywords": ["卫星", "Starlink", "低轨", "遥感", "导航", "北斗",
                             "GPS", "通信卫星", "遥感卫星", "立方星"]
            }
        }
    },

    "robotics": {
        "name": "机器人",
        "keywords": ["机器人", "robot", "自动驾驶", "无人", "人形", "机械臂",
                      "SLAM", "运动规划", "控制", "触觉", "传感器"],
        "children": {
            "robotics/humanoid": {
                "name": "人形机器人",
                "keywords": ["人形机器人", "Atlas", "Optimus", "Figure", "宇树",
                             "优必选", "波士顿动力", "灵巧手", "双足", "运动控制"]
            },
            "robotics/auto": {
                "name": "自动驾驶",
                "keywords": ["自动驾驶", "FSD", "Waymo", "Cruise", "激光雷达",
                             "LiDAR", "毫米波", "V2X", "车路协同", "ADAS"]
            }
        }
    },

    "energy": {
        "name": "能源与环境",
        "keywords": ["能源", "核聚变", "光伏", "电池", "储", "氢", "碳中和",
                      "气候", "新能源", "可持续"],
        "children": {
            "energy/fusion": {
                "name": "可控核聚变",
                "keywords": ["核聚变", "托卡马克", "ITER", "SPARC", "惯性约束",
                             "磁约束", "NIF", "等离子体", "stellarator", "EAST",
                             "CFS", "Helion"]
            },
            "energy/battery": {
                "name": "储能与电池",
                "keywords": ["电池", "固态电池", "锂电池", "钠离子", "储能",
                             "磷酸铁锂", "三元锂", "半固态", "全固态", "超级电容",
                             "液流电池", "氢储能", "燃料电池"]
            },
            "energy/renewable": {
                "name": "新能源技术",
                "keywords": ["光伏", "钙钛矿", "太阳能", "风电", "地热", "潮汐",
                             "氢能", "绿色氢", "碳捕集", "碳中和", "CCUS"]
            }
        }
    },

    "math": {
        "name": "数学与理论",
        "keywords": ["数学", "理论", "证明", "猜想", "算法", "优化", "统计",
                      "概率", "物理", "弦理论", "拓扑", "几何"],
        "children": {
            "math/physics": {
                "name": "理论物理",
                "keywords": ["物理", "理论物理", "弦理论", "量子力学", "相对论",
                             "粒子物理", "标准模型", "暗物质", "暗能量", "额外维度",
                             "全息原理", "黑洞热力学", "引力"]
            },
            "math/theory": {
                "name": "数学与算法理论",
                "keywords": ["数学", "黎曼猜想", "P≠NP", "算法", "复杂度",
                             "密码学", "信息论", "图论", "组合", "数论", "代数"]
            }
        }
    }
}


# ============================================================
# Entity Tag Configurations
# ============================================================

COMPANY_TAGS = [
    # AI/ML companies
    "OpenAI", "Google DeepMind", "Anthropic", "Meta AI", "Microsoft Research",
    "xAI", "Stability AI", "Mistral", "Cohere", "Hugging Face", "Midjourney",
    "Runway", "Perplexity", "Character.ai", "Inflection", "Adept",
    # Tech companies
    "Apple", "Google", "Microsoft", "Meta", "Amazon", "NVIDIA", "AMD",
    "Intel", "Qualcomm", "Tesla", "台积电", "TSMC", "三星", "Samsung",
    "华为", "Huawei", "字节跳动", "ByteDance", "阿里巴巴", "Alibaba",
    "腾讯", "Tencent", "百度", "Baidu", "京东", "JD",
    # Robotics / Auto
    "Boston Dynamics", "Figure AI", "宇树科技", "Unitree", "Waymo",
    "Cruise", "优必选",
    # Space
    "SpaceX", "Blue Origin", "Rocket Lab", "ULA",
    # Quantum
    "IBM Quantum", "Rigetti", "IonQ", "Quantinuum", "D-Wave",
    # Bio
    "Moderna", "BioNTech", "Illumina", "CRISPR Therapeutics",
    # Energy
    "CFS", "Commonwealth Fusion", "Helion Energy", "TAE Technologies",
    # China tech
    "商汤", "旷视", "科大讯飞", "寒武纪", "地平线", "蔚来", "小鹏", "理想",
    "比亚迪", "大疆", "DJI",
]

TECHNOLOGY_TAGS = [
    "Transformer", "Attention", "Diffusion Model", "GAN", "VAE",
    "Reinforcement Learning", "Self-Supervised", "Transfer Learning",
    "CRISPR", "Cas9", "AlphaFold", "mRNA", "CAR-T",
    "Quantum Annealing", "Superconducting Qubit", "Quantum Error Correction",
    "Graphene", "Perovskite", "MXene", "Topological Insulator",
    "Nuclear Fusion", "Tokamak", "Stellarator", "Solid-State Battery",
    "Brain-Computer Interface", "Neural Decoding", "Optogenetics",
    "CRISPR Prime Editing", "Base Editing", "Protein Design",
    "3nm Process", "EUV Lithography", "GAA Transistor", "Chiplet",
    "RISC-V", "ARM", "x86", "CUDA", "PyTorch", "JAX",
    "Kubernetes", "Docker", "WebAssembly", "Rust",
    "LiDAR", "SLAM", "RAG", "Vector Database", "Knowledge Graph",
    "Homomorphic Encryption", "Zero-Knowledge Proof", "Federated Learning",
]


# ============================================================
# Seed Data Initialization
# ============================================================

def seed_taxonomy():
    """Initialize the categorization taxonomy and entity tags."""
    from knowledge_store import get_connection, init_knowledge_store
    
    init_knowledge_store()
    conn = get_connection()
    
    _seed_categories(conn, TAXONOMY)
    _seed_tags(conn)
    
    conn.commit()
    conn.close()
    logging.getLogger("Classifier").info("Taxonomy seeded")


def _seed_categories(conn: sqlite3.Connection, taxonomy: dict, parent_id: int = None):
    for slug, data in taxonomy.items():
        # Check if exists
        cursor = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,))
        existing = cursor.fetchone()
        
        if existing:
            cat_id = existing["id"]
            conn.execute(
                "UPDATE categories SET name=?, description=?, parent_id=? WHERE id=?",
                (data["name"], data.get("description", ""), parent_id, cat_id)
            )
        else:
            cursor = conn.execute(
                "INSERT INTO categories (name, slug, parent_id, description) VALUES (?, ?, ?, ?)",
                (data["name"], slug, parent_id, data.get("description", ""))
            )
            cat_id = cursor.lastrowid
        
        if "children" in data:
            _seed_categories(conn, data["children"], cat_id)


def _seed_tags(conn: sqlite3.Connection):
    for company in COMPANY_TAGS:
        conn.execute(
            "INSERT OR IGNORE INTO tags (name, tag_type, description) VALUES (?, 'company', ?)",
            (company, f"公司/组织: {company}")
        )
    
    for tech in TECHNOLOGY_TAGS:
        conn.execute(
            "INSERT OR IGNORE INTO tags (name, tag_type, description) VALUES (?, 'technology', ?)",
            (tech, f"技术/概念: {tech}")
        )


# ============================================================
# Classification Engine
# ============================================================

@dataclass
class ClassificationResult:
    categories: List[Dict] = field(default_factory=list)
    tags: List[Dict] = field(default_factory=list)
    importance: str = "normal"
    quality_score: int = 0


class ArticleClassifier:
    
    # Source prestige scores (higher = more authoritative)
    SOURCE_QUALITY = {
        "Nature": 95, "Science": 95, "Cell": 93, "PNAS": 90, "NEJM": 92,
        "arXiv": 70, "bioRxiv": 65, "medRxiv": 65,
        "MIT Technology Review": 80, "IEEE Spectrum": 80,
        "Communications of the ACM": 82,
        "Google DeepMind": 85, "OpenAI": 80, "Anthropic": 80,
        "Hacker News": 50, "GitHub": 60, "知乎": 40,
        "Wired": 55, "Ars Technica": 60, "The Verge": 50,
        "TechCrunch": 55, "InfoQ": 55, "量子位": 50, "机器之心": 55,
    }

    def __init__(self):
        self._load_taxonomy()

    def _load_taxonomy(self):
        """Load taxonomy from database into memory for matching."""
        from knowledge_store import get_connection
        conn = get_connection()
        try:
            cursor = conn.execute("SELECT * FROM categories")
            self._categories = {row["slug"]: dict(row) for row in cursor.fetchall()}
            cursor = conn.execute("SELECT * FROM tags")
            self._tags = {row["name"]: dict(row) for row in cursor.fetchall()}
        finally:
            conn.close()

    def classify(self, title: str, description: str, source_name: str,
                 author: str = "") -> ClassificationResult:
        text = (title + " " + description).lower()
        result = ClassificationResult()

        # Classify into categories
        result.categories = self._match_categories(text)
        
        # Extract entity tags
        result.tags = self._match_tags(text, source_name)
        
        # Compute importance and quality
        result.importance = self._compute_importance(text, source_name, result.categories)
        result.quality_score = self._compute_quality(source_name, description, author)

        return result

    def _match_categories(self, text: str) -> List[Dict]:
        """Match article text against taxonomy keywords."""
        matches = {}
        
        for slug, data in TAXONOMY.items():
            score = self._score_keywords(text, data.get("keywords", []))
            if score > 0:
                matches[slug] = {"slug": slug, "name": data["name"], "confidence": score}
            
            # Check subcategories
            for child_slug, child_data in data.get("children", {}).items():
                child_score = self._score_keywords(text, child_data.get("keywords", []))
                if child_score > 0:
                    confidence = child_score * 1.5  # Exact match boost
                    matches[child_slug] = {
                        "slug": child_slug,
                        "name": child_data["name"],
                        "confidence": min(confidence, 1.0)
                    }
        
        # Return top matches (max 3 categories)
        return sorted(matches.values(), key=lambda x: x["confidence"], reverse=True)[:3]

    def _score_keywords(self, text: str, keywords: List[str]) -> float:
        """Simple keyword matching with case-insensitive overlap."""
        hits = 0
        for kw in keywords:
            if kw.lower() in text:
                hits += 1
        if not keywords:
            return 0.0
        return hits / len(keywords)

    def _match_tags(self, text: str, source_name: str) -> List[Dict]:
        """Match entity tags (companies, technologies)."""
        matched = []
        text_lower = text.lower()
        
        for company in COMPANY_TAGS:
            if company.lower() in text_lower or company.lower() in source_name.lower():
                matched.append({"name": company, "tag_type": "company"})
        
        for tech in TECHNOLOGY_TAGS:
            if tech.lower() in text_lower:
                matched.append({"name": tech, "tag_type": "technology"})
        
        return matched[:8]  # Cap at 8 tags

    def _compute_importance(self, text: str, source_name: str,
                            categories: List[Dict]) -> str:
        """Determine if this is a major breakthrough or routine update."""
        breakthrough_keywords = [
            "突破", "首次", "里程碑", "历史性", "革命性", "开创性",
            "breakthrough", "first-ever", "milestone", "landmark",
            "revolutionary", "groundbreaking", "major advance",
            "创造世界纪录", "刷新纪录", "超越人类"
        ]
        
        urgent_keywords = [
            "发布", "发布了", "宣布", "推出", "开源",
            "launched", "announced", "released", "published",
            "open source", "open-sourced"
        ]
        
        for kw in breakthrough_keywords:
            if kw.lower() in text:
                return "breakthrough"
        
        for kw in urgent_keywords:
            if kw.lower() in text:
                return "important"
        
        # High-prestige source articles are at least "important"
        if self.SOURCE_QUALITY.get(source_name, 0) >= 80:
            return "important"
        
        return "normal"

    def _compute_quality(self, source_name: str, description: str, author: str) -> int:
        """Compute a quality score (0-100)."""
        base = self.SOURCE_QUALITY.get(source_name, 40)
        
        # Bonus for detailed description
        if len(description) > 200:
            base += 10
        elif len(description) > 100:
            base += 5
        
        # Bonus for having an author
        if author and len(author) > 2:
            base += 5
        
        return min(base, 100)


# ============================================================
# Article Processing Pipeline
# ============================================================

def classify_and_store_article(title: str, url: str, source_name: str,
                                description: str = "", author: str = "",
                                published_date: str = "", language: str = "zh",
                                content_snippet: str = "") -> Optional[int]:
    """Classify an article and store it in the knowledge store."""
    from knowledge_store import insert_article, get_connection
    
    classifier = ArticleClassifier()
    result = classifier.classify(title, description, source_name, author)
    
    article_id = insert_article(
        title=title, url=url, source_name=source_name,
        description=description, author=author,
        published_date=published_date, language=language,
        content_snippet=content_snippet,
        quality_score=result.quality_score,
        importance=result.importance
    )
    
    if not article_id:
        return None
    
    # Attach categories and tags
    conn = get_connection()
    try:
        for cat in result.categories:
            slug = cat.get("slug", "")
            if slug:
                cursor = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,))
                row = cursor.fetchone()
                if row:
                    conn.execute(
                        "INSERT OR IGNORE INTO article_categories (article_id, category_id, confidence) VALUES (?, ?, ?)",
                        (article_id, row["id"], cat.get("confidence", 1.0))
                    )
                    # Also attach parent categories
                    cursor2 = conn.execute("SELECT parent_id FROM categories WHERE id = ?", (row["id"],))
                    parent = cursor2.fetchone()
                    if parent and parent["parent_id"]:
                        conn.execute(
                            "INSERT OR IGNORE INTO article_categories (article_id, category_id, confidence) VALUES (?, ?, ?)",
                            (article_id, parent["parent_id"], cat.get("confidence", 1.0) * 0.8)
                        )
        
        for tag in result.tags:
            cursor = conn.execute("SELECT id FROM tags WHERE name = ?", (tag["name"],))
            row = cursor.fetchone()
            if row:
                conn.execute(
                    "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
                    (article_id, row["id"])
                )
        
        conn.commit()
    except Exception as e:
        logging.getLogger("Classifier").error(f"Failed to attach metadata: {e}")
    finally:
        conn.close()
    
    return article_id
