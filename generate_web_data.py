import os
import re
import json
from datetime import datetime


def parse_report_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    report = {
        'date': '',
        'displayDate': '',
        'generatedAt': '',
        'newsCount': 0,
        'news': [],
        'categories': {},
        'trends': {
            'topCategories': [],
            'topTags': [],
            'topSources': []
        }
    }

    date_match = re.search(r'日期:\s*(\d{4})年(\d{2})月(\d{2})日', content)
    if date_match:
        year, month, day = date_match.groups()
        report['date'] = f'{year}-{month}-{day}'
        report['displayDate'] = f'{year}年{month}月{day}日'

    gen_match = re.search(r'报告生成时间:\s*(.+)', content)
    if gen_match:
        report['generatedAt'] = gen_match.group(1).strip()

    count_match = re.search(r'共收录\s*(\d+)\s*条新闻', content)
    if count_match:
        report['newsCount'] = int(count_match.group(1))

    trend_section = re.search(r'【今日趋势分析】(.*?)(?=\n【|\Z)', content, re.DOTALL)
    if trend_section:
        trend_text = trend_section.group(1)
        
        cat_pattern = re.compile(r'•\s*(.+?):\s*(\d+)条')
        raw_cats = [{'name': name.strip(), 'count': int(count)} 
                    for name, count in cat_pattern.findall(trend_text)]
        
        report['trends']['topCategories'] = [
            c for c in raw_cats 
            if 'scheme' not in c['name'] and 'http://' not in c['name']
        ]
        
        tag_pattern = re.compile(r'•\s*#(.+?):\s*(\d+)条')
        report['trends']['topTags'] = [
            {'name': name.strip(), 'count': int(count)}
            for name, count in tag_pattern.findall(trend_text)
        ]
        
        source_pattern = re.compile(r'•\s*(.+?):\s*(\d+)条')
        raw_sources = [{'name': name.strip(), 'count': int(count)} 
                       for name, count in source_pattern.findall(trend_text)]
        
        valid_sources = ['arXiv', 'GitHub', 'Hacker News', '量子位', '知乎', 'OpenAI', 
                         'DeepMind', 'Anthropic', 'Stability AI', 'TechCrunch']
        report['trends']['topSources'] = [
            s for s in raw_sources 
            if any(vs.lower() in s['name'].lower() for vs in valid_sources)
        ]

    clean_content = re.sub(r'<[^>]+>', '', content)

    category_sections = re.split(r'(📁\s+.+)', clean_content)
    
    current_category = '其他'
    for i, part in enumerate(category_sections):
        if part.startswith('📁'):
            current_category = part[2:].strip()
            if 'scheme' in current_category or 'http://' in current_category:
                current_category = '其他'
        else:
            item_pattern = re.compile(
                r'(\d+)\.\s*(.+?)(?:\s*\[([^\]]+)\])?\n\s*来源:\s*(.+?)\n\s*摘要:\s*(.+?)\n\s*链接:\s*(.+?)(?:\n\s*作者:\s*(.+?))?(?=\n\s*\d+\.|\Z)',
                re.DOTALL
            )

            for item_match in item_pattern.finditer(part):
                idx, title, tags_str, source, summary, link, author = item_match.groups()
                tags = [t.strip().lstrip('#') for t in tags_str.split()] if tags_str else []
                
                link = link.strip()
                if '\n' in link:
                    link = link.split('\n')[0].strip()
                
                if link.startswith('📁'):
                    link = ''
                
                news_item = {
                    'id': int(idx),
                    'title': title.strip(),
                    'source': source.strip(),
                    'summary': summary.strip(),
                    'link': link,
                    'author': author.strip() if author else '',
                    'category': current_category,
                    'tags': tags
                }
                report['news'].append(news_item)
                
                if current_category not in report['categories']:
                    report['categories'][current_category] = []
                report['categories'][current_category].append(news_item)

    if not report['news']:
        news_pattern_fallback = re.compile(
            r'(\d+)\.\s*(.+?)\n\s*来源:\s*(.+?)\n\s*摘要:\s*(.+?)\n\s*链接:\s*(.+?)(?=\n\n|\n\d+\.|\n-+$|\Z)',
            re.DOTALL
        )
        for match in news_pattern_fallback.finditer(content):
            idx, title, source, summary, link = match.groups()
            
            link = link.strip()
            if '\n' in link:
                link = link.split('\n')[0].strip()
            
            report['news'].append({
                'id': int(idx),
                'title': title.strip(),
                'source': source.strip(),
                'summary': summary.strip(),
                'link': link,
                'category': '',
                'tags': [],
                'author': ''
            })

    return report


def generate_reports_json():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, 'reports')
    output_dir = os.path.join(base_dir, 'web', 'data')
    os.makedirs(output_dir, exist_ok=True)

    reports = []
    if os.path.exists(reports_dir):
        for filename in sorted(os.listdir(reports_dir), reverse=True):
            if filename.startswith('ai_report_') and filename.endswith('.txt'):
                filepath = os.path.join(reports_dir, filename)
                try:
                    report = parse_report_file(filepath)
                    reports.append(report)
                except Exception as e:
                    print(f'Error parsing {filename}: {e}')

    all_categories = set()
    all_tags = set()
    all_sources = set()
    total_news = 0

    for report in reports:
        total_news += report['newsCount']
        for news in report['news']:
            cat = news.get('category')
            if cat and 'scheme' not in cat and 'http://' not in cat:
                all_categories.add(cat)
            for tag in news.get('tags', []):
                all_tags.add(tag)
            if news.get('source'):
                all_sources.add(news['source'])

    stats = {
        'totalReports': len(reports),
        'totalNews': total_news,
        'latestDate': reports[0]['displayDate'] if reports else '',
        'sources': sorted(list(all_sources)),
        'categories': sorted(list(all_categories)),
        'tags': sorted(list(all_tags))
    }

    output_path = os.path.join(output_dir, 'reports.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': stats,
            'reports': reports
        }, f, ensure_ascii=False, indent=2)

    print(f'Generated {output_path}')
    print(f'Total reports: {len(reports)}')
    print(f'Total news: {stats["totalNews"]}')
    print(f'Categories: {", ".join(stats["categories"])}')


if __name__ == '__main__':
    generate_reports_json()