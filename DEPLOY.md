# 部署指南

## 方案一：GitHub Pages（推荐）

### 步骤 1：创建 GitHub 仓库

1. 访问 https://github.com/new
2. 仓库名称可以设为 `ai-observer` 或你的用户名.github.io
3. 选择公开仓库

### 步骤 2：推送代码

```bash
cd AIobserve
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/仓库名.git
git branch -M main
git push -u origin main
```

### 步骤 3：启用 GitHub Pages

1. 进入仓库 → Settings → Pages
2. Source 选择 GitHub Actions
3. 等待自动部署完成

### 步骤 4：配置定时更新

已创建 `.github/workflows/deploy.yml`，会：
- 每次 push 到 main 分支自动部署
- 每天 UTC 0 点自动运行数据生成脚本

### 访问地址

```
https://你的用户名.github.io/仓库名/
```

---

## 方案二：Gitee Pages（国内访问更快）

1. 访问 https://gitee.com 创建仓库
2. 推送代码到 Gitee
3. 进入仓库 → 服务 → Gitee Pages
4. 选择 master 分支，目录填写 `web`

---

## 方案三：Vercel（一键部署）

1. 访问 https://vercel.com
2. 导入 GitHub 仓库
3. 在配置中设置：
   - Build Command: `python generate_web_data.py`
   - Output Directory: `web`
4. 点击 Deploy

---

## 方案四：Netlify（一键部署）

1. 访问 https://www.netlify.com
2. 导入 GitHub 仓库
3. 在构建设置中：
   - Build command: `python generate_web_data.py`
   - Publish directory: `web`
4. 点击 Deploy site

---

## 方案五：使用自己的服务器

```bash
# 安装 nginx
sudo apt update && sudo apt install nginx

# 上传 web 目录到服务器
scp -r web user@your-server-ip:/var/www/ai-observer

# 配置 nginx
sudo nano /etc/nginx/sites-available/ai-observer

# 添加以下内容：
server {
    listen 80;
    server_name your-domain.com;

    root /var/www/ai-observer;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}

# 启用站点
sudo ln -s /etc/nginx/sites-available/ai-observer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 更新数据

### 手动更新（本地）

```bash
python generate_web_data.py
git add .
git commit -m "Update reports"
git push
```

### 自动更新

GitHub Actions 已配置每天自动运行数据生成脚本。
如果有新的报告，只需要将 `reports/` 目录下的新文件 push 到仓库即可自动更新。

---

## 自定义域名

### GitHub Pages

1. 在域名解析中添加 CNAME 记录指向 `你的用户名.github.io`
2. 在仓库 → Settings → Pages → Custom domain 中输入你的域名

### Vercel/Netlify

在网站设置中添加自定义域名并配置 DNS 记录。
