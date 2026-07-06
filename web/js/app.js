const App = {
    data: null,
    
    async init() {
        await this.loadData();
        this.setupHeader();
        this.setupMobileMenu();
        this.setupScrollEffects();
        this.setupRouter();
        this.handleRoute();
        window.addEventListener('hashchange', () => this.handleRoute());
    },
    
    async loadData() {
        try {
            const response = await fetch('data/reports.json');
            if (response.ok) {
                this.data = await response.json();
            }
        } catch (e) {
            console.error('Failed to load data:', e);
            this.data = { stats: { totalReports: 0, totalNews: 0, latestDate: '', sources: [] }, reports: [] };
        }
    },
    
    setupHeader() {
        const header = document.getElementById('header');
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    },
    
    setupMobileMenu() {
        const btn = document.getElementById('mobileMenuBtn');
        const header = document.getElementById('header');
        
        let mobileNav = document.querySelector('.mobile-nav');
        if (!mobileNav) {
            mobileNav = document.createElement('div');
            mobileNav.className = 'mobile-nav';
            mobileNav.innerHTML = `
                <a href="#/" data-route="/">首页</a>
                <a href="#/reports" data-route="/reports">日报列表</a>
            `;
            header.appendChild(mobileNav);
        }
        
        btn.addEventListener('click', () => {
            mobileNav.classList.toggle('open');
        });
        
        mobileNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobileNav.classList.remove('open');
            });
        });
    },
    
    setupScrollEffects() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1 });
        
        setTimeout(() => {
            document.querySelectorAll('.fade-in').forEach(el => {
                observer.observe(el);
            });
        }, 100);
    },
    
    setupRouter() {
        document.querySelectorAll('[data-scroll-to]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = link.dataset.scrollTo;
                if (window.location.hash === '#/' || window.location.hash === '') {
                    const element = document.getElementById(target);
                    if (element) {
                        element.scrollIntoView({ behavior: 'smooth' });
                    }
                } else {
                    window.location.hash = '#/';
                    setTimeout(() => {
                        const element = document.getElementById(target);
                        if (element) {
                            element.scrollIntoView({ behavior: 'smooth' });
                        }
                    }, 100);
                }
            });
        });
    },
    
    handleRoute() {
        const hash = window.location.hash.slice(1) || '/';
        const app = document.getElementById('app');
        
        this.updateActiveNav(hash);
        
        if (hash === '/' || hash === '') {
            app.innerHTML = this.renderHome();
        } else if (hash === '/reports') {
            app.innerHTML = this.renderReportsList();
        } else if (hash.startsWith('/reports/')) {
            const date = hash.split('/')[2];
            app.innerHTML = this.renderReportDetail(date);
        } else {
            app.innerHTML = this.renderNotFound();
        }
        
        window.scrollTo(0, 0);
        this.setupScrollEffects();
    },
    
    updateActiveNav(hash) {
        document.querySelectorAll('.nav-link[data-route]').forEach(link => {
            const route = link.dataset.route;
            if (route === hash || (hash === '' && route === '/')) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    },
    
    renderHome() {
        const stats = this.data?.stats || { totalReports: 0, totalNews: 0, latestDate: '', sources: [] };
        const latestReport = this.data?.reports?.[0] || null;
        
        return `
            <section class="hero">
                <div class="container">
                    <div class="hero-content">
                        <div class="hero-badge">
                            <span class="dot"></span>
                            <span>实时更新 · 每日自动生成</span>
                        </div>
                        <h1 class="hero-title">
                            <span class="gradient-text">AI前沿</span>技术<br>每日洞察
                        </h1>
                        <p class="hero-subtitle">
                            聚合全球顶级AI机构的最新技术突破，每日自动生成结构化日报，让你高效获取前沿信息
                        </p>
                        <div class="hero-cta">
                            <a href="#/reports" class="btn btn-primary">
                                <span>浏览日报</span>
                                <span>→</span>
                            </a>
                            <a href="#about" class="btn btn-secondary" onclick="document.getElementById('about').scrollIntoView({behavior:'smooth'});return false;">
                                <span>了解更多</span>
                            </a>
                        </div>
                        <div class="hero-stats">
                            <div class="stat-item">
                                <div class="stat-number">${stats.totalReports}</div>
                                <div class="stat-label">日报总数</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-number">${stats.totalNews}</div>
                                <div class="stat-label">新闻条目</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-number">${stats.sources?.length || 0}+</div>
                                <div class="stat-label">数据源</div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
            
            <section class="section" id="features">
                <div class="container">
                    <div class="section-header fade-in">
                        <div class="section-tag">核心特性</div>
                        <h2 class="section-title">为什么选择 <span class="gradient-text">AI前沿观察者</span></h2>
                        <p class="section-subtitle">专业、高效、全面的AI技术信息聚合平台</p>
                    </div>
                    <div class="features-grid">
                        <div class="feature-card fade-in">
                            <div class="feature-icon">🤖</div>
                            <h3 class="feature-title">AI智能筛选</h3>
                            <p class="feature-desc">利用大语言模型智能筛选最有价值的技术新闻，过滤噪音信息</p>
                        </div>
                        <div class="feature-card fade-in">
                            <div class="feature-icon">⚡</div>
                            <h3 class="feature-title">每日自动更新</h3>
                            <p class="feature-desc">定时自动爬取arXiv、顶级机构博客等数据源，每日生成结构化报告</p>
                        </div>
                        <div class="feature-card fade-in">
                            <div class="feature-icon">📊</div>
                            <h3 class="feature-title">多源聚合</h3>
                            <p class="feature-desc">覆盖OpenAI、DeepMind、Anthropic等全球顶级AI研究机构</p>
                        </div>
                        <div class="feature-card fade-in">
                            <div class="feature-icon">🎯</div>
                            <h3 class="feature-title">精准摘要</h3>
                            <p class="feature-desc">每条新闻配备精炼摘要，快速把握核心要点，节省阅读时间</p>
                        </div>
                    </div>
                </div>
            </section>
            
            <section class="section">
                <div class="container">
                    <div class="section-header fade-in">
                        <div class="section-tag">最新日报</div>
                        <h2 class="section-title">今日 <span class="gradient-text">AI要闻</span></h2>
                        <p class="section-subtitle">${stats.latestDate ? stats.latestDate + ' 最新更新' : '每日自动更新，敬请期待'}</p>
                    </div>
                    ${latestReport ? this.renderLatestReport(latestReport) : `
                        <div class="latest-report fade-in">
                            <p style="text-align:center;color:var(--text-secondary);">暂无报告数据，请运行 generate_web_data.py 生成数据</p>
                        </div>
                    `}
                </div>
            </section>
            
            <section class="section" id="about">
                <div class="container">
                    <div class="about-section">
                        <div class="about-content fade-in">
                            <div class="section-tag">关于项目</div>
                            <h2>用技术追踪<br><span class="gradient-text">技术前沿</span></h2>
                            <p>AI前沿观察者是一个开源的AI技术资讯聚合项目，旨在帮助AI从业者和爱好者高效获取全球最新的AI技术动态。</p>
                            <p>项目通过自动化脚本每日定时从多个权威数据源收集信息，利用AI技术进行智能筛选和摘要生成，最终输出结构化的技术日报。</p>
                            <ul class="about-features">
                                <li>支持邮件订阅推送</li>
                                <li>开源可自定义配置</li>
                                <li>多数据源可扩展</li>
                                <li>本地部署隐私安全</li>
                            </ul>
                        </div>
                        <div class="about-visual fade-in">
                            <div class="orb orb-1"></div>
                            <div class="orb orb-2"></div>
                        </div>
                    </div>
                </div>
            </section>
        `;
    },
    
    renderLatestReport(report) {
        const previewNews = report.news.slice(0, 3);
        return `
            <div class="latest-report fade-in">
                <div class="report-header">
                    <div class="report-date">
                        <span class="date-badge">${report.displayDate}</span>
                        <span class="report-meta">共 ${report.newsCount} 条新闻</span>
                    </div>
                    <span class="report-meta">生成于 ${report.generatedAt}</span>
                </div>
                <div class="news-list">
                    ${previewNews.map(news => this.renderNewsCard(news)).join('')}
                </div>
                <div class="view-all-btn">
                    <a href="#/reports/${report.date}" class="btn btn-secondary">
                        <span>查看完整报告</span>
                        <span>→</span>
                    </a>
                </div>
            </div>
        `;
    },
    
    renderNewsCard(news) {
        return `
            <a href="${news.link}" target="_blank" class="news-card">
                <div class="news-header">
                    <h3 class="news-title">${news.title}</h3>
                    <span class="news-source">${news.source}</span>
                </div>
                <p class="news-summary">${news.summary}</p>
                <span class="news-link">
                    <span>阅读原文</span>
                    <span>↗</span>
                </span>
            </a>
        `;
    },
    
    renderReportsList() {
        const stats = this.data?.stats || { totalReports: 0, totalNews: 0, latestDate: '', sources: [] };
        const reports = this.data?.reports || [];
        
        return `
            <div class="reports-page">
                <div class="container">
                    <div class="page-header fade-in">
                        <div class="section-tag">历史日报</div>
                        <h1 class="page-title">AI技术 <span class="gradient-text">日报归档</span></h1>
                        <p class="page-subtitle">浏览过往日报，追踪AI技术发展脉络</p>
                    </div>
                    
                    <div class="stats-row">
                        <div class="stat-card fade-in">
                            <div class="stat-number">${stats.totalReports}</div>
                            <div class="stat-label">日报总数</div>
                        </div>
                        <div class="stat-card fade-in">
                            <div class="stat-number">${stats.totalNews}</div>
                            <div class="stat-label">累计新闻</div>
                        </div>
                        <div class="stat-card fade-in">
                            <div class="stat-number">${stats.sources?.length || 0}</div>
                            <div class="stat-label">数据源</div>
                        </div>
                        <div class="stat-card fade-in">
                            <div class="stat-number">${Math.round(stats.totalNews / (stats.totalReports || 1))}</div>
                            <div class="stat-label">日均新闻</div>
                        </div>
                    </div>
                    
                    ${reports.length > 0 ? `
                        <div class="timeline fade-in">
                            ${reports.map(report => `
                                <div class="timeline-item">
                                    <div class="timeline-dot"></div>
                                    <a href="#/reports/${report.date}" class="timeline-card">
                                        <div class="timeline-date">${report.displayDate}</div>
                                        <div class="timeline-meta">
                                            <span>📰 ${report.newsCount} 条新闻</span>
                                            <span>🕐 ${report.generatedAt}</span>
                                        </div>
                                        <div class="timeline-preview">
                                            ${report.news.slice(0, 2).map(n => n.title).join(' · ')}
                                        </div>
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <div class="latest-report">
                            <p style="text-align:center;color:var(--text-secondary);">暂无报告数据，请运行 generate_web_data.py 生成数据</p>
                        </div>
                    `}
                </div>
            </div>
        `;
    },
    
    renderReportDetail(date) {
        const report = this.data?.reports?.find(r => r.date === date);
        
        if (!report) {
            return this.renderNotFound();
        }
        
        return `
            <div class="report-detail">
                <div class="container">
                    <a href="#/reports" class="back-link">
                        <span>←</span>
                        <span>返回日报列表</span>
                    </a>
                    
                    <div class="detail-header fade-in">
                        <h1 class="detail-title">${report.displayDate} 日报</h1>
                        <div class="detail-meta">
                            <span>📅 ${report.displayDate}</span>
                            <span>🕐 生成于 ${report.generatedAt}</span>
                            <span>📰 共 ${report.newsCount} 条新闻</span>
                        </div>
                    </div>
                    
                    <h2 class="detail-news-title fade-in">今日要闻</h2>
                    <div class="news-list">
                        ${report.news.map((news, index) => `
                            <div class="fade-in" style="transition-delay:${index * 0.1}s">
                                ${this.renderNewsCard(news)}
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    },
    
    renderNotFound() {
        return `
            <div class="not-found">
                <h1>404</h1>
                <p>页面不存在或报告未找到</p>
                <a href="#/" class="btn btn-primary">返回首页</a>
            </div>
        `;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
