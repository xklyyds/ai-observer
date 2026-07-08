const App = {
    state: {
        page: 1,
        limit: 24,
        activeCategory: null,
        activeTag: null,
        searchTerm: "",
        importance: "",
        language: "",
        totalArticles: 0,
        totalPages: 1,
    },
    _staticData: null,
    _isApiMode: false,

    CAT_ICONS: {
        "ai": "🧠", "quantum": "⚛️", "biotech": "🧬",
        "materials": "🔬", "computing": "💻", "space": "🚀",
        "robotics": "🤖", "energy": "⚡", "math": "📐"    },

    SOURCE_NAMES: {
        "arXiv": "arXiv预印本", "Nature": "Nature期刊", "Science": "Science期刊",
        "MIT Technology Review": "MIT科技评论", "bioRxiv": "bioRxiv预印本",
        "GitHub Trending": "GitHub热榜", "Hacker News": "HackerNews",
        "Google DeepMind": "DeepMind", "OpenAI": "OpenAI",
        "Google Quantum AI": "谷歌量子AI", "Neuralink": "Neuralink",
        "台积电": "台积电", "Microsoft": "微软", "NASA": "NASA",
        "Stability AI": "Stability AI", "Anthropic": "Anthropic",
    },

    async init() {
        await this._detectMode();
        this.loadCategories();
        this.loadStats();
        this.loadTrending();
        this.loadArticles();
        this.loadSubscriberCount();
    },

    // ============================================================
    // Mode detection: API vs Static (GitHub Pages)
    // ============================================================

    async _detectMode() {
        try {
            const res = await fetch("/api/stats", { method: "HEAD" });
            if (res.ok) {
                this._isApiMode = true;
                return;
            }
        } catch (e) { /* API not available */ }

        // Fall back to static knowledge.json
        try {
            const res = await fetch("data/knowledge.json");
            if (res.ok) {
                this._staticData = await res.json();
                this._isApiMode = false;
                console.log("Running in static mode (GitHub Pages)");
            } else {
                console.warn("knowledge.json not found");
            }
        } catch (e) {
            console.warn("Failed to load knowledge.json:", e);
        }
    },

    // ============================================================
    // Categories
    // ============================================================

    async loadCategories() {
        if (this._staticData) {
            this.renderCategoryTree(this._staticData.categories);
            return;
        }
        try {
            const res = await fetch("/api/categories");
            const data = await res.json();
            this.renderCategoryTree(data.categories);
        } catch (e) {
            console.error("Failed to load categories:", e);
        }
    },

    renderCategoryTree(categories) {
        const container = document.getElementById("categoryTree");
        let html = `<div class="cat-item">
            <a class="cat-link ${!this.state.activeCategory ? 'active' : ''}"
               onclick="App.selectCategory(null)">
                <span class="cat-icon">📡</span>
                <span class="cat-name">全部领域</span>
            </a>
        </div>`;
        for (const cat of categories) {
            html += this._renderCatItem(cat, 0);
        }
        container.innerHTML = html;
    },

    _renderCatItem(cat, depth) {
        const icon = this.CAT_ICONS[cat.slug] || "📄";
        const isActive = this.state.activeCategory === cat.slug;
        const hasChildren = cat.children && cat.children.length > 0;
        const isOpen = isActive || (this.state.activeCategory && this.state.activeCategory.startsWith(cat.slug));

        let html = `<div class="cat-item${isOpen ? ' open' : ''}">`;
        html += `<div class="cat-link${isActive ? ' active' : ''}" style="padding-left: ${8 + depth * 16}px">`;
        if (hasChildren) {
            html += `<span class="cat-expand" onclick="App.toggleCat(event, this.parentElement.parentElement)">${isOpen ? '▾' : '▸'}</span>`;
        } else {
            html += `<span style="width:16px;flex-shrink:0;"></span>`;
        }
        html += `<span class="cat-icon">${icon}</span>`;
        html += `<span class="cat-name" onclick="App.selectCategory('${cat.slug}')">${cat.name}</span>`;
        html += `</div>`;
        if (hasChildren) {
            html += `<div class="cat-children">`;
            for (const child of cat.children) {
                html += this._renderCatItem(child, depth + 1);
            }
            html += `</div>`;
        }
        html += `</div>`;
        return html;
    },

    toggleCat(e, item) {
        e.stopPropagation();
        item.classList.toggle("open");
        const arrow = item.querySelector(".cat-expand");
        if (arrow) arrow.textContent = item.classList.contains("open") ? "▾" : "▸";
    },

    selectCategory(slug) {
        this.state.activeCategory = slug;
        this.state.activeTag = null;
        this.state.page = 1;
        this.loadCategories();
        this.loadArticles();
        this.updateFilters();
    },

    // ============================================================
    // Articles
    // ============================================================

    async loadArticles() {
        const grid = document.getElementById("articleGrid");
        grid.innerHTML = '<div class="loading-state">加载中...</div>';

        if (this._staticData) {
            this._loadArticlesStatic();
            return;
        }

        try {
            const params = new URLSearchParams();
            if (this.state.activeCategory) params.set("category", this.state.activeCategory);
            if (this.state.activeTag) params.set("tag", this.state.activeTag);
            if (this.state.searchTerm) params.set("search", this.state.searchTerm);
            if (this.state.importance) params.set("importance", this.state.importance);
            if (this.state.language) params.set("language", this.state.language);
            params.set("page", this.state.page);
            params.set("limit", this.state.limit);
            params.set("order_by", "published_date");

            const res = await fetch("/api/articles?" + params.toString());
            const data = await res.json();

            this.state.totalArticles = data.total;
            this.state.totalPages = data.pages;
            this.renderArticles(data.articles);
            this.renderPagination();
        } catch (e) {
            grid.innerHTML = '<div class="loading-state">加载失败</div>';
        }
    },

    _loadArticlesStatic() {
        let articles = this._staticData.latest_articles || [];

        // Apply filters client-side
        if (this.state.activeCategory) {
            const slug = this.state.activeCategory;
            articles = articles.filter(a => a.categories && a.categories.some(c =>
                c.slug === slug || c.slug.startsWith(slug + '/')
            ));
        }
        if (this.state.activeTag) {
            articles = articles.filter(a => a.tags && a.tags.some(t => t.name === this.state.activeTag));
        }
        if (this.state.searchTerm) {
            const q = this.state.searchTerm.toLowerCase();
            articles = articles.filter(a =>
                (a.title && a.title.toLowerCase().includes(q)) ||
                (a.description && a.description.toLowerCase().includes(q))
            );
        }

        // Client-side pagination
        this.state.totalArticles = articles.length;
        this.state.totalPages = Math.max(1, Math.ceil(articles.length / this.state.limit));
        const start = (this.state.page - 1) * this.state.limit;
        const pageItems = articles.slice(start, start + this.state.limit);

        this.renderArticles(pageItems);
        this.renderPagination();
    },

    renderArticles(articles) {
        const grid = document.getElementById("articleGrid");
        if (!articles || articles.length === 0) {
            grid.innerHTML = `<div class="empty-state">
                <h3>暂无内容</h3>
                <p>${this.state.activeCategory ? "该领域下暂无文章" :
                  `运行 <code>python crawler.py</code> 采集数据后刷新页面`}</p>
            </div>`;
            return;
        }
        let html = "";
        for (const a of articles) html += this._renderArticle(a);
        grid.innerHTML = html;
    },

    _renderArticle(a) {
        const impClass = a.importance || "normal";
        const hasHighSource = a.quality_score >= 70;
        let catsHtml = "", tagsHtml = "";

        if (a.categories && a.categories.length) {
            for (const cat of a.categories) {
                catsHtml += `<span class="cat-badge" onclick="event.stopPropagation();App.selectCategory('${cat.slug}')">${cat.name}</span>`;
            }
        }
        if (a.tags && a.tags.length) {
            for (const tag of a.tags) {
                tagsHtml += `<span class="tag-pill ${tag.tag_type}" onclick="event.stopPropagation();App.selectTag('${tag.name}')">${tag.name}</span>`;
            }
        }

        return `<div class="article-card" onclick="window.open('${this._escapeAttr(a.url)}', '_blank')">
            <div class="card-header">
                <div class="importance-dot ${impClass}"></div>
                <div class="card-title">${this._escapeHtml(a.title)}</div>
            </div>
            ${a.description ? `<div class="card-description">${this._escapeHtml(a.description)}</div>` : ""}
            <div class="card-meta">
                <span class="source-badge${hasHighSource ? ' high' : ''}">${this._escapeHtml(this.SOURCE_NAMES[a.source_name] || a.source_name)}</span>
                <span class="card-date">${a.published_date || ""}</span>
            </div>
            ${catsHtml ? `<div class="card-categories">${catsHtml}</div>` : ""}
            ${tagsHtml ? `<div class="card-tags">${tagsHtml}</div>` : ""}
            <div class="card-footer">
                <a href="${this._escapeAttr(a.url)}" target="_blank" class="card-link" onclick="event.stopPropagation()">阅读原文 →</a>
            </div>
        </div>`;
    },

    selectTag(tagName) {
        this.state.activeTag = tagName;
        this.state.activeCategory = null;
        this.state.page = 1;
        this.loadCategories();
        this.loadArticles();
        this.updateFilters();
    },

    // ============================================================
    // Filters & Search
    // ============================================================

    search() {
        this.state.searchTerm = document.getElementById("searchInput").value.trim();
        this.state.page = 1;
        this.loadArticles();
        this.updateFilters();
    },

    filterChanged() {
        this.state.importance = document.getElementById("importanceFilter").value;
        this.state.language = document.getElementById("languageFilter").value;
        this.state.page = 1;
        this.loadArticles();
    },

    updateFilters() {
        const container = document.getElementById("activeFilters");
        let html = "";
        if (this.state.activeCategory) {
            html += `<span class="filter-pill category">📁 ${this.state.activeCategory} <span class="remove-filter" onclick="App.selectCategory(null)">✕</span></span>`;
        }
        if (this.state.activeTag) {
            html += `<span class="filter-pill tag"># ${this.state.activeTag} <span class="remove-filter" onclick="App.selectTag(null)">✕</span></span>`;
        }
        if (this.state.searchTerm) {
            html += `<span class="filter-pill category">🔍 "${this.state.searchTerm}" <span class="remove-filter" onclick="document.getElementById('searchInput').value='';App.search()">✕</span></span>`;
        }
        container.innerHTML = html;
    },

    navigateHome() {
        this.state = { page: 1, limit: 24, activeCategory: null, activeTag: null, searchTerm: "", importance: "", language: "", totalArticles: 0, totalPages: 1 };
        document.getElementById("searchInput").value = "";
        document.getElementById("importanceFilter").value = "";
        document.getElementById("languageFilter").value = "";
        this.loadCategories();
        this.loadArticles();
        this.updateFilters();
    },

    // ============================================================
    // Pagination
    // ============================================================

    renderPagination() {
        const container = document.getElementById("pagination");
        const { page, totalPages, totalArticles } = this.state;
        if (totalPages <= 1) {
            container.innerHTML = totalArticles > 0 ? `<span class="page-info">共 ${totalArticles} 条</span>` : "";
            return;
        }
        let html = "";
        html += `<button class="page-btn" onclick="App.goPage(${page - 1})" ${page <= 1 ? "disabled" : ""}>←</button>`;
        const start = Math.max(1, page - 2);
        const end = Math.min(totalPages, page + 2);
        if (start > 1) {
            html += `<button class="page-btn" onclick="App.goPage(1)">1</button>`;
            if (start > 2) html += `<span class="page-info">...</span>`;
        }
        for (let i = start; i <= end; i++) {
            html += `<button class="page-btn${i === page ? ' active' : ''}" onclick="App.goPage(${i})">${i}</button>`;
        }
        if (end < totalPages) {
            if (end < totalPages - 1) html += `<span class="page-info">...</span>`;
            html += `<button class="page-btn" onclick="App.goPage(${totalPages})">${totalPages}</button>`;
        }
        html += `<button class="page-btn" onclick="App.goPage(${page + 1})" ${page >= totalPages ? "disabled" : ""}>→</button>`;
        html += `<span class="page-info">共 ${totalArticles} 条</span>`;
        container.innerHTML = html;
    },

    goPage(p) {
        if (p < 1 || p > this.state.totalPages) return;
        this.state.page = p;
        this.loadArticles();
        document.getElementById("articleGrid").scrollIntoView({ behavior: "smooth", block: "start" });
    },

    // ============================================================
    // Trending & Stats
    // ============================================================

    async loadTrending() {
        if (this._staticData) {
            this.renderTrending(this._staticData.trending?.companies?.slice(0, 10));
            const allTagItems = [...(this._staticData.tags?.companies || []), ...(this._staticData.tags?.technologies || [])];
            this.renderTagCloud(allTagItems.slice(0, 15));
            return;
        }
        try {
            const [trendRes, tagRes] = await Promise.all([
                fetch("/api/trending?days=7"),
                fetch("/api/tags?limit=20")
            ]);
            const trending = await trendRes.json();
            const tags = await tagRes.json();
            this.renderTrending(trending.trending);
            this.renderTagCloud(tags.tags);
        } catch (e) { console.error("Failed to load trending:", e); }
    },

    renderTrending(items) {
        const container = document.getElementById("trendingList");
        if (!items || !items.length) {
            container.innerHTML = '<div style="color:var(--text-muted);font-size:12px;">暂无数据</div>';
            return;
        }
        let html = "";
        for (const item of items.slice(0, 10)) {
            html += `<div class="trend-item" onclick="App.selectCategory('${item.slug}')">
                <span class="trend-name">${item.name}</span>
                <span class="trend-count">${item.article_count}</span>
            </div>`;
        }
        container.innerHTML = html;
    },

    renderTagCloud(tags) {
        const container = document.getElementById("tagCloud");
        if (!tags || !tags.length) { container.innerHTML = ""; return; }
        let html = "";
        for (const tag of tags.slice(0, 15)) {
            html += `<span class="tag-chip" onclick="App.selectTag('${tag.name}')">${tag.name}</span>`;
        }
        container.innerHTML = html;
    },

    async loadStats() {
        if (this._staticData) {
            const s = this._staticData.stats || {};
            document.getElementById("statArticles").textContent = s.total_articles || 0;
            document.getElementById("statSources").textContent = s.active_sources || 0;
            return;
        }
        try {
            const res = await fetch("/api/stats");
            const data = await res.json();
            document.getElementById("statArticles").textContent = data.total_articles || 0;
            document.getElementById("statSources").textContent = data.active_sources || 0;
        } catch (e) { console.error("Failed to load stats:", e); }
    },

    // ============================================================
    // Subscription
    // ============================================================

    async subscribe() {
        const emailInput = document.getElementById("subscribeEmail");
        const msgDiv = document.getElementById("subscribeMsg");
        const btn = document.getElementById("subscribeBtn");
        const email = emailInput.value.trim().toLowerCase();

        if (!email || !email.includes("@") || !email.includes(".")) {
            this._showSubscribeMsg("请输入有效的邮箱地址", "error"); return;
        }
        btn.disabled = true; btn.textContent = "提交中...";

        try {
            const res = await fetch("/api/subscribe", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            });
            const data = await res.json();
            this._showSubscribeMsg(data.message || "订阅成功", "success");
            if (data.status === "success") {
                emailInput.value = "";
                setTimeout(() => { this.loadSubscriberCount(); }, 2000);
            }
        } catch (e) {
            this._showSubscribeMsg("订阅功能需要在本地服务器模式下使用", "error");
        } finally {
            btn.disabled = false; btn.textContent = "订阅";
        }
    },

    async loadSubscriberCount() {
        if (this._staticData) return;
        try {
            const res = await fetch("/api/stats");
            const data = await res.json();
            document.getElementById("statSubscribers").textContent = data.subscribers || 0;
        } catch (e) { /* non-critical */ }
    },

    _showSubscribeMsg(text, type) {
        const msgDiv = document.getElementById("subscribeMsg");
        msgDiv.textContent = text;
        msgDiv.className = "subscribe-msg " + type;
        setTimeout(() => { msgDiv.className = "subscribe-msg"; }, 6000);
    },

    // ============================================================
    // UI Helpers
    // ============================================================

    refresh() {
        this.loadCategories();
        this.loadArticles();
        this.loadStats();
        this.loadTrending();
        this.loadSubscriberCount();
    },

    toggleSidebar() {
        document.getElementById("sidebar").classList.toggle("open");
    },

    _escapeHtml(str) {
        if (!str) return "";
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    },

    _escapeAttr(str) {
        if (!str) return "";
        return str.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }
};

document.addEventListener("DOMContentLoaded", () => App.init());
