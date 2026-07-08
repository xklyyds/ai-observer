const App = {
    data: null,
    supabase: null,
    deletedItems: { reports: [], news: {} },
    filters: {
        search: '',
        category: '',
        source: ''
    },
    activeCategory: '',
    currentPage: 1,
    pageSize: 10,
    
    initSupabase() {
        const supabaseUrl = 'https://spgmbocskmtaorgbiawl.supabase.co';
        const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwZ21ib2Nza210YW9yZ2JpYXdsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NzQwNzMsImV4cCI6MjA5OTA1MDA3M30.MyhNCGnWDhDCgOln1sxHXMBAikQZKjvYaBsVQUrYdeY';
        
        if (supabaseUrl.includes('your-project-url') || supabaseKey.includes('your-anon-key')) {
            console.warn('Supabase not configured - using localStorage fallback');
            this.loadDeletedItemsFromLocal();
            return;
        }
        
        this.supabase = window.createClient(supabaseUrl, supabaseKey);
        this.loadDeletedItems();
    },
    
    async loadDeletedItems() {
        try {
            const [reportsRes, newsRes] = await Promise.all([
                this.supabase.from('deleted_reports').select('date'),
                this.supabase.from('deleted_news').select('report_date, news_id')
            ]);
            
            this.deletedItems = {
                reports: reportsRes.data?.map(r => r.date) || [],
                news: {}
            };
            
            newsRes.data?.forEach(item => {
                const key = `${item.report_date}_${item.news_id}`;
                this.deletedItems.news[key] = true;
            });
            
            this.cacheDeletedItems();
        } catch (e) {
            console.error('Failed to load deleted items from Supabase:', e);
            this.loadDeletedItemsFromLocal();
        }
    },
    
    loadDeletedItemsFromLocal() {
        try {
            const stored = localStorage.getItem('aiobserver_deleted');
            this.deletedItems = stored ? JSON.parse(stored) : { reports: [], news: {} };
        } catch {
            this.deletedItems = { reports: [], news: {} };
        }
    },
    
    cacheDeletedItems() {
        localStorage.setItem('aiobserver_deleted', JSON.stringify(this.deletedItems));
    },
    
    async deleteReport(date) {
        if (this.deletedItems.reports.includes(date)) {
            return;
        }
        
        this.deletedItems.reports.push(date);
        this.cacheDeletedItems();
        
        if (this.supabase) {
            try {
                await this.supabase.from('deleted_reports').upsert({ date });
            } catch (e) {
                console.error('Failed to delete report:', e);
            }
        }
        
        this.refreshData();
    },
    
    async deleteNews(date, newsId) {
        const key = `${date}_${newsId}`;
        if (this.deletedItems.news[key]) {
            return;
        }
        
        this.deletedItems.news[key] = true;
        this.cacheDeletedItems();
        
        if (this.supabase) {
            try {
                await this.supabase.from('deleted_news').upsert({ report_date: date, news_id: newsId });
            } catch (e) {
                console.error('Failed to delete news:', e);
            }
        }
        
        this.refreshData();
    },
    
    async restoreReport(date) {
        this.deletedItems.reports = this.deletedItems.reports.filter(d => d !== date);
        this.cacheDeletedItems();
        
        if (this.supabase) {
            try {
                await this.supabase.from('deleted_reports').delete().eq('date', date);
            } catch (e) {
                console.error('Failed to restore report:', e);
            }
        }
        
        this.refreshData();
    },
    
    async restoreNews(date, newsId) {
        const key = `${date}_${newsId}`;
        delete this.deletedItems.news[key];
        this.cacheDeletedItems();
        
        if (this.supabase) {
            try {
                await this.supabase.from('deleted_news').delete()
                    .eq('report_date', date)
                    .eq('news_id', newsId);
            } catch (e) {
                console.error('Failed to restore news:', e);
            }
        }
        
        this.refreshData();
    },
    
    async clearAllDeleted() {
        this.deletedItems = { reports: [], news: {} };
        localStorage.removeItem('aiobserver_deleted');
        
        if (this.supabase) {
            try {
                await this.supabase.from('deleted_reports').delete();
                await this.supabase.from('deleted_news').delete();
            } catch (e) {
                console.error('Failed to clear deleted:', e);
            }
        }
        
        this.refreshData();
    },
    
    getFilteredReports() {
        return (this.data?.reports || []).filter(report => {
            if (this.deletedItems.reports.includes(report.date)) return false;
            report.news = report.news.filter(news => {
                const key = `${report.date}_${news.id}`;
                return this.deletedItems.news[key] !== true;
            });
            report.newsCount = report.news.length;
            return report.news.length > 0;
        });
    },
    
    async init() {
        this.initSupabase();
        await this.loadData();
        this.updateSidebarStats();
        this.setupSidebarToggle();
        this.setupRouter();
        this.handleRoute();
        window.addEventListener('hashchange', () => this.handleRoute());
    },
    
    async loadData() {
        try {
            const response = await fetch(`data/reports.json?_t=${Date.now()}`);
            if (response.ok) {
                this.data = await response.json();
            }
        } catch (e) {
            console.error('Failed to load data:', e);
            this.data = { stats: { totalReports: 0, totalNews: 0, latestDate: '', sources: [], categories: [], tags: [] }, reports: [] };
        }
    },
    
    async refreshData() {
        await this.loadData();
        this.updateSidebarStats();
        this.handleRoute();
    },
    
    updateSidebarStats() {
        const filteredReports = this.getFilteredReports();
        const totalNews = filteredReports.reduce((acc, r) => acc + r.newsCount, 0);
        const latestDate = filteredReports[0]?.displayDate || '';
        
        document.getElementById('totalReports').textContent = filteredReports.length || 0;
        document.getElementById('totalNews').textContent = totalNews || 0;
        document.getElementById('lastUpdate').textContent = latestDate ? `更新于 ${latestDate}` : '暂无数据';
    },
    
    setupSidebarToggle() {
        const toggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('mainContent');
        
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-hidden');
        });
        
        sidebar.addEventListener('click', (e) => {
            if (e.target.classList.contains('sidebar')) {
                sidebar.classList.add('collapsed');
                mainContent.classList.remove('sidebar-hidden');
            }
        });
    },
    
    setupRouter() {
        document.querySelectorAll('[data-route]').forEach(link => {
            link.addEventListener('click', (e) => {
                const route = link.dataset.route;
                if (window.location.hash !== `#${route}`) {
                    window.location.hash = route;
                }
            });
        });
    },
    
    handleRoute() {
        const hash = window.location.hash.slice(1) || '/';
        const app = document.getElementById('app');
        
        this.updateActiveNav(hash);
        this.updatePageTitle(hash);
        
        if (hash === '/' || hash === '') {
            app.innerHTML = this.renderDashboard();
        } else if (hash === '/reports') {
            app.innerHTML = this.renderReportsList();
        } else if (hash === '/search') {
            app.innerHTML = this.renderSearch();
        } else if (hash.startsWith('/reports/')) {
            const date = hash.split('/')[2];
            app.innerHTML = this.renderReportDetail(date);
        } else {
            app.innerHTML = this.renderNotFound();
        }
        
        window.scrollTo(0, 0);
        this.setupSearchEvents();
        this.setupCategoryFilters();
        this.setupCollapsibleCards();
    },
    
    updateActiveNav(hash) {
        document.querySelectorAll('[data-route]').forEach(link => {
            const route = link.dataset.route;
            if (route === hash || (hash === '' && route === '/')) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    },
    
    updatePageTitle(hash) {
        const title = document.getElementById('pageTitle');
        const titles = {
            '/': '仪表盘',
            '/reports': '日报列表',
            '/search': '搜索新闻'
        };
        
        if (hash.startsWith('/reports/')) {
            const date = hash.split('/')[2];
            title.textContent = `${date} 日报`;
        } else {
            title.textContent = titles[hash] || 'AI前沿观察者';
        }
    },
    
    setupSearchEvents() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filters.search = e.target.value.toLowerCase();
                this.applyFilters();
            });
        }
    },
    
    setupCategoryFilters() {
        document.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                const type = chip.dataset.filterType;
                const value = chip.dataset.filterValue;
                
                document.querySelectorAll(`.filter-chip[data-filter-type="${type}"]`).forEach(c => c.classList.remove('active'));
                
                if (this.filters[type] === value) {
                    this.filters[type] = '';
                } else {
                    this.filters[type] = value;
                    chip.classList.add('active');
                }
                
                this.applyFilters();
            });
        });
        
        document.querySelectorAll('.category-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const category = tab.dataset.category;
                this.activeCategory = category;
                
                document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                this.applyCategoryFilter(category);
            });
        });
    },
    
    setupCollapsibleCards() {
        document.querySelectorAll('.collapsible-header').forEach(header => {
            header.addEventListener('click', () => {
                const card = header.parentElement;
                card.classList.toggle('expanded');
            });
        });
    },
    
    applyFilters() {
        const newsCards = document.querySelectorAll('.news-card, .collapsible-card');
        newsCards.forEach((card, index) => {
            const title = card.querySelector('.news-title, .collapsible-title')?.textContent || '';
            const summary = card.querySelector('.news-summary, .collapsible-summary')?.textContent || '';
            const category = card.dataset.category || '';
            const source = card.dataset.source || '';
            
            const matchSearch = !this.filters.search || 
                title.toLowerCase().includes(this.filters.search) || 
                summary.toLowerCase().includes(this.filters.search);
            const matchCategory = !this.filters.category || category === this.filters.category;
            const matchSource = !this.filters.source || source === this.filters.source;
            
            if (matchSearch && matchCategory && matchSource) {
                card.style.display = 'block';
                card.style.opacity = '0';
                card.style.transform = 'translateY(10px)';
                setTimeout(() => {
                    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 50);
                
                this.highlightText(card, this.filters.search);
            } else {
                card.style.display = 'none';
            }
        });
    },
    
    highlightText(card, searchTerm) {
        const titleEl = card.querySelector('.news-title, .collapsible-title');
        const summaryEl = card.querySelector('.news-summary, .collapsible-summary');
        
        if (!searchTerm) {
            if (titleEl) titleEl.innerHTML = titleEl.textContent;
            if (summaryEl) summaryEl.innerHTML = summaryEl.textContent;
            return;
        }
        
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        
        if (titleEl) {
            titleEl.innerHTML = titleEl.textContent.replace(regex, '<mark>$1</mark>');
        }
        if (summaryEl) {
            summaryEl.innerHTML = summaryEl.textContent.replace(regex, '<mark>$1</mark>');
        }
    },
    
    applyCategoryFilter(category) {
        const newsCards = document.querySelectorAll('.news-card, .collapsible-card');
        newsCards.forEach(card => {
            const cardCategory = card.dataset.category || '';
            card.style.display = !category || cardCategory === category ? 'block' : 'none';
        });
    },
    
    renderDashboard() {
        const filteredReports = this.getFilteredReports();
        const latestReport = filteredReports[0] || null;
        
        const totalNews = filteredReports.reduce((acc, r) => acc + r.newsCount, 0);
        const categoryCounts = {};
        const sourcesSet = new Set();
        const categoriesSet = new Set();
        
        filteredReports.forEach(report => {
            report.news.forEach(news => {
                categoryCounts[news.category] = (categoryCounts[news.category] || 0) + 1;
                sourcesSet.add(news.source);
                categoriesSet.add(news.category);
            });
        });
        
        const sortedCategories = Object.entries(categoryCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 6);
        
        const maxCount = Math.max(...sortedCategories.map(([, count]) => count), 1);
        
        return `
            <div class="dashboard-grid">
                <div class="stat-card">
                    <div class="stat-card-header">
                        <svg class="stat-card-icon blue" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                    </div>
                    <div class="stat-card-value">${filteredReports.length}</div>
                    <div class="stat-card-label">日报总数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-header">
                        <svg class="stat-card-icon purple" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                    </div>
                    <div class="stat-card-value">${totalNews}</div>
                    <div class="stat-card-label">新闻条目</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-header">
                        <svg class="stat-card-icon green" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="7" height="7"></rect>
                            <rect x="14" y="3" width="7" height="7"></rect>
                            <rect x="14" y="14" width="7" height="7"></rect>
                            <rect x="3" y="14" width="7" height="7"></rect>
                        </svg>
                    </div>
                    <div class="stat-card-value">${categoriesSet.size}</div>
                    <div class="stat-card-label">话题分类</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-header">
                        <svg class="stat-card-icon orange" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="10" r="3"></circle>
                            <path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"></path>
                        </svg>
                    </div>
                    <div class="stat-card-value">${sourcesSet.size}</div>
                    <div class="stat-card-label">数据源</div>
                </div>
            </div>
            
            <div class="section-card">
                <div class="section-header">
                    <h2 class="section-title">今日要闻</h2>
                    <a href="#/reports/${latestReport?.date}" class="section-link">查看完整报告 →</a>
                </div>
                <div class="news-list">
                    ${latestReport ? latestReport.news.slice(0, 5).map(news => this.renderNewsCard(news)).join('') : `
                        <p style="text-align:center;color:var(--text-secondary);padding:20px;">暂无数据</p>
                    `}
                </div>
            </div>
            
            <div class="dashboard-row">
                <div class="section-card chart-section">
                    <div class="section-header">
                        <h2 class="section-title">分类分布</h2>
                    </div>
                    <div class="bar-chart">
                        ${sortedCategories.map(([name, count]) => `
                            <div class="bar-chart-item">
                                <span class="bar-label">${name}</span>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width: ${(count / maxCount) * 100}%;"></div>
                                </div>
                                <span class="bar-value">${count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="section-card tag-section">
                    <div class="section-header">
                        <h2 class="section-title">热门标签</h2>
                        <a href="#/search" class="section-link">搜索 →</a>
                    </div>
                    <div class="tags-cloud">
                        ${Object.keys(categoryCounts).slice(0, 15).map(tag => {
                            const count = categoryCounts[tag] || 1;
                            const weight = Math.min(count / 3, 1);
                            const fontSize = 13 + weight * 6;
                            return `
                                <span class="tag-cloud-item" onclick="App.navigateToSearch('${tag}')" style="font-size: ${fontSize}px;">
                                    #${tag}
                                </span>
                            `;
                        }).join('')}
                    </div>
                </div>
            </div>
            
            <div class="section-card">
                <div class="section-header">
                    <h2 class="section-title">数据源分布</h2>
                </div>
                <div class="source-stats">
                    ${Array.from(sourcesSet).slice(0, 6).map(source => `
                        <div class="source-stat-item">
                            <span class="source-dot"></span>
                            <span class="source-name">${source}</span>
                            <span class="source-count">${this.getSourceCount(source)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    },
    
    getSourceCount(source) {
        let count = 0;
        const filteredReports = this.getFilteredReports();
        filteredReports.forEach(report => {
            report.news.forEach(news => {
                if (news.source === source) count++;
            });
        });
        return count;
    },
    
    navigateToSearch(tag) {
        this.filters.search = tag;
        window.location.hash = '#/search';
    },
    
    renderNewsCard(news) {
        const tagsHtml = news.tags && news.tags.length > 0 ? 
            `<div class="news-tags">${news.tags.map(tag => `<span class="news-tag">#${tag}</span>`).join('')}</div>` : '';
        const date = news.reportDate || (this.data?.reports?.[0]?.date || '');
        
        return `
            <div class="news-card" data-category="${news.category || ''}" data-source="${news.source || ''}">
                <div class="news-card-header">
                    <h3 class="news-title">${news.title}</h3>
                    <span class="news-source">${news.source}</span>
                </div>
                <p class="news-summary">${news.summary}</p>
                <div class="news-meta">
                    <span class="news-category">${news.category || '未分类'}</span>
                    ${tagsHtml}
                </div>
                <div class="news-actions">
                    ${news.link ? `<a href="${news.link}" target="_blank" class="news-link">阅读原文 ↗</a>` : ''}
                    <button class="delete-btn" onclick="App.deleteNews('${date}', ${news.id})" title="删除这条新闻">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
            </div>
        `;
    },
    
    renderReportsList() {
        const reports = this.getFilteredReports();
        const stats = this.data?.stats || { totalReports: 0, totalNews: 0, latestDate: '', sources: [], categories: [], tags: [] };
        
        return `
            <div class="reports-page">
                <div class="dashboard-grid" style="margin-bottom:24px;">
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <span class="stat-card-icon blue">📰</span>
                        </div>
                        <div class="stat-card-value">${reports.length}</div>
                        <div class="stat-card-label">日报总数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <span class="stat-card-icon purple">🔍</span>
                        </div>
                        <div class="stat-card-value">${reports.reduce((acc, r) => acc + r.newsCount, 0)}</div>
                        <div class="stat-card-label">累计新闻</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <span class="stat-card-icon green">📅</span>
                        </div>
                        <div class="stat-card-value">${Math.round(reports.reduce((acc, r) => acc + r.newsCount, 0) / (reports.length || 1))}</div>
                        <div class="stat-card-label">日均新闻</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <span class="stat-card-icon orange">🏷️</span>
                        </div>
                        <div class="stat-card-value">${stats.categories?.length || 0}</div>
                        <div class="stat-card-label">话题分类</div>
                    </div>
                </div>
                
                ${reports.length > 0 ? `
                    <div class="timeline">
                        ${reports.map(report => `
                            <div class="timeline-item">
                                <div class="timeline-dot"></div>
                                <div class="timeline-card">
                                    <a href="#/reports/${report.date}" class="timeline-link">
                                        <div class="timeline-date">${report.displayDate}</div>
                                        <div class="timeline-meta">
                                            <span>📰 ${report.newsCount} 条新闻</span>
                                            <span>🕐 ${report.generatedAt}</span>
                                        </div>
                                        <div class="timeline-preview">
                                            ${report.news.slice(0, 2).map(n => n.title).join(' · ')}
                                        </div>
                                    </a>
                                    <button class="delete-btn" onclick="App.deleteReport('${report.date}')" title="删除整个日报">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <div class="section-card">
                        <p style="text-align:center;color:var(--text-secondary);padding:40px;">暂无报告数据</p>
                        <p style="text-align:center;color:var(--text-secondary);padding-bottom:40px;">您可以点击下面按钮恢复已删除的日报</p>
                        <div style="text-align:center;">
                            <button class="btn btn-secondary" onclick="App.clearAllDeleted()">恢复所有已删除内容</button>
                        </div>
                    </div>
                `}
            </div>
        `;
    },
    
    renderSearch() {
        const stats = this.data?.stats || { categories: [], sources: [], tags: [] };
        const reports = this.getFilteredReports();
        const allNews = [];
        reports.forEach(report => {
            report.news.forEach(news => {
                allNews.push({ ...news, reportDate: report.date });
            });
        });
        
        const filteredNews = allNews.filter(news => {
            const matchSearch = !this.filters.search || 
                news.title.toLowerCase().includes(this.filters.search) || 
                news.summary.toLowerCase().includes(this.filters.search);
            const matchCategory = !this.filters.category || news.category === this.filters.category;
            const matchSource = !this.filters.source || news.source === this.filters.source;
            return matchSearch && matchCategory && matchSource;
        });
        
        const totalPages = Math.ceil(filteredNews.length / this.pageSize);
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const paginatedNews = filteredNews.slice(startIndex, startIndex + this.pageSize);
        
        const tagCounts = {};
        allNews.forEach(news => {
            news.tags?.forEach(tag => {
                tagCounts[tag] = (tagCounts[tag] || 0) + 1;
            });
        });
        
        const sortedTags = Object.entries(tagCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 20);
        
        return `
            <div class="search-page">
                <div class="search-bar">
                    <div class="search-input-wrapper">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                        <input type="text" id="searchInput" placeholder="输入关键词搜索..." value="${this.filters.search || ''}" />
                    </div>
                </div>
                
                <div class="filter-section">
                    <div class="filter-group">
                        <h4>热门标签</h4>
                        <div class="filter-chips">
                            ${sortedTags.map(([tag, count]) => {
                                const weight = Math.min(count / 5, 1);
                                const fontSize = 13 + weight * 4;
                                return `
                                    <span class="filter-chip ${this.filters.search === tag ? 'active' : ''}" 
                                          data-filter-type="search" 
                                          data-filter-value="${tag}"
                                          style="font-size: ${fontSize}px; opacity: ${0.7 + weight * 0.3};">
                                        #${tag} <span class="tag-count">${count}</span>
                                    </span>
                                `;
                            }).join('')}
                        </div>
                    </div>
                    <div class="filter-group">
                        <h4>话题分类</h4>
                        <div class="filter-chips">
                            <span class="filter-chip ${!this.filters.category ? 'active' : ''}" data-filter-type="category" data-filter-value="">全部</span>
                            ${stats.categories.map(cat => `
                                <span class="filter-chip ${this.filters.category === cat ? 'active' : ''}" data-filter-type="category" data-filter-value="${cat}">${cat}</span>
                            `).join('')}
                        </div>
                    </div>
                    <div class="filter-group">
                        <h4>来源</h4>
                        <div class="filter-chips">
                            <span class="filter-chip ${!this.filters.source ? 'active' : ''}" data-filter-type="source" data-filter-value="">全部</span>
                            ${stats.sources.map(src => `
                                <span class="filter-chip ${this.filters.source === src ? 'active' : ''}" data-filter-type="source" data-filter-value="${src}">${src}</span>
                            `).join('')}
                        </div>
                    </div>
                </div>
                
                <div class="search-results">
                    <div class="results-header">
                        <span>共找到 ${filteredNews.length} 条新闻</span>
                    </div>
                    <div class="news-list">
                        ${paginatedNews.map((news, index) => `
                            ${this.renderNewsCard(news)}
                        `).join('')}
                    </div>
                    ${totalPages > 1 ? `
                        <div class="pagination">
                            <button class="pagination-btn ${this.currentPage === 1 ? 'disabled' : ''}" onclick="App.setPage(${this.currentPage - 1})">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;">
                                    <polyline points="15 18 9 12 15 6"></polyline>
                                </svg>
                            </button>
                            ${Array.from({ length: totalPages }, (_, i) => i + 1).map(page => `
                                <button class="pagination-btn ${this.currentPage === page ? 'active' : ''}" onclick="App.setPage(${page})">${page}</button>
                            `).join('')}
                            <button class="pagination-btn ${this.currentPage === totalPages ? 'disabled' : ''}" onclick="App.setPage(${this.currentPage + 1})">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;">
                                    <polyline points="9 18 15 12 9 6"></polyline>
                                </svg>
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    },
    
    setPage(page) {
        this.currentPage = page;
        this.renderSearch();
        this.applyFilters();
        window.scrollTo(0, 0);
    },
    
    renderReportDetail(date) {
        const deleted = this.getDeletedItems();
        if (deleted.reports.includes(date)) {
            return `
                <div class="report-detail">
                    <a href="#/reports" class="back-link">
                        <span>←</span>
                        <span>返回日报列表</span>
                    </a>
                    <div class="section-card">
                        <p style="text-align:center;color:var(--text-secondary);padding:40px;">该日报已被删除</p>
                        <div style="text-align:center;">
                            <button class="btn btn-secondary" onclick="App.restoreReport('${date}')">恢复此日报</button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        const report = this.data?.reports?.find(r => r.date === date);
        
        if (!report) {
            return this.renderNotFound();
        }
        
        report.news = report.news.filter(news => {
            const key = `${date}_${news.id}`;
            return deleted.news[key] !== true;
        });
        
        const categories = [...new Set(report.news.map(n => n.category))].filter(c => c);
        
        return `
            <div class="report-detail">
                <a href="#/reports" class="back-link">
                    <span>←</span>
                    <span>返回日报列表</span>
                </a>
                
                <div class="detail-header">
                    <h1 class="detail-title">${report.displayDate} 日报</h1>
                    <div class="detail-meta">
                        <span>📅 ${report.displayDate}</span>
                        <span>🕐 生成于 ${report.generatedAt}</span>
                        <span>📰 共 ${report.news.length} 条新闻</span>
                    </div>
                    <button class="delete-btn delete-report-btn" onclick="App.deleteReport('${date}')" title="删除整个日报">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        <span>删除日报</span>
                    </button>
                </div>
                
                ${report.trends && report.trends.topCategories.length > 0 ? this.renderDetailTrends(report.trends) : ''}
                
                ${categories.length > 0 ? `
                    <div class="category-tabs">
                        <button class="category-tab ${!this.activeCategory ? 'active' : ''}" data-category="">全部</button>
                        ${categories.map(cat => `
                            <button class="category-tab ${this.activeCategory === cat ? 'active' : ''}" data-category="${cat}">${cat}</button>
                        `).join('')}
                    </div>
                ` : ''}
                
                <h2 class="detail-news-title">今日新闻</h2>
                <div class="news-list">
                    ${report.news.length > 0 ? report.news.map((news, index) => `
                        <div class="collapsible-card" data-category="${news.category || ''}" data-source="${news.source || ''}">
                            <div class="collapsible-header">
                                <div class="collapsible-header-left">
                                    <h3 class="collapsible-title">${news.title}</h3>
                                    <span class="collapsible-source">${news.source}</span>
                                </div>
                                <div class="collapsible-header-right">
                                    <button class="delete-btn" onclick="App.deleteNews('${date}', ${news.id})" title="删除这条新闻">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                                    </button>
                                    <span class="collapsible-arrow">▼</span>
                                </div>
                            </div>
                            <div class="collapsible-content">
                                <p class="collapsible-summary">${news.summary}</p>
                                <div class="collapsible-meta">
                                    <span class="news-category">${news.category || '未分类'}</span>
                                    ${news.tags && news.tags.length > 0 ? `
                                        <div class="news-tags">${news.tags.map(tag => `<span class="news-tag">#${tag}</span>`).join('')}</div>
                                    ` : ''}
                                    ${news.link ? `<a href="${news.link}" target="_blank" class="news-link">阅读原文 ↗</a>` : ''}
                                </div>
                            </div>
                        </div>
                    `).join('') : `
                        <div class="section-card">
                            <p style="text-align:center;color:var(--text-secondary);padding:40px;">该日报下的所有新闻已被删除</p>
                            <div style="text-align:center;">
                                <button class="btn btn-secondary" onclick="App.clearAllDeleted()">恢复所有已删除内容</button>
                            </div>
                        </div>
                    `}
                </div>
            </div>
        `;
    },
    
    renderDetailTrends(trends) {
        return `
            <div class="trends-section">
                <h3>📊 今日趋势</h3>
                <div class="trends-grid">
                    ${trends.topCategories.slice(0, 3).map(cat => `
                        <div class="trend-item">
                            <div class="trend-value">${cat.count}</div>
                            <div class="trend-label">${cat.name}</div>
                        </div>
                    `).join('')}
                </div>
                ${trends.topTags && trends.topTags.length > 0 ? `
                    <div class="tags-cloud">
                        ${trends.topTags.map(tag => `<span class="tag-cloud-item">#${tag.name}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    },
    
    renderNotFound() {
        return `
            <div class="not-found">
                <h1>404</h1>
                <p>页面不存在或报告未找到</p>
                <a href="#/" class="btn">返回首页</a>
            </div>
        `;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});