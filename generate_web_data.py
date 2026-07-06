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
        'news': []
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

    news_pattern = re.compile(
        r'(\d+)\.\s*(.+?)\n\s*来源:\s*(.+?)\n\s*摘要:\s*(.+?)\n\s*链接:\s*(.+?)(?=\n\n|\n\d+\.|\n-+$|\Z)',
        re.DOTALL
    )

    for match in news_pattern.finditer(content):
        idx, title, source, summary, link = match.groups()
        report['news'].append({
            'id': int(idx),
            'title': title.strip(),
            'source': source.strip(),
            'summary': summary.strip(),
            'link': link.strip()
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

    stats = {
        'totalReports': len(reports),
        'totalNews': sum(r['newsCount'] for r in reports),
        'latestDate': reports[0]['displayDate'] if reports else '',
        'sources': list(set(
            news['source']
            for report in reports
            for news in report['news']
        ))
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


if __name__ == '__main__':
    generate_reports_json()
