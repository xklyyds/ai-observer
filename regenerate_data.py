import json
import os

reports_dir = 'reports'
output_file = 'web/data/reports.json'

reports = []
sources_set = set()
categories_set = set()
news_count = 0

if os.path.exists(reports_dir):
    for filename in sorted(os.listdir(reports_dir)):
        if filename.startswith('ai_report_') and filename.endswith('.txt'):
            filepath = os.path.join(reports_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            date_str = filename.replace('ai_report_', '').replace('.txt', '')
            report = {
                "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                "displayDate": f"{date_str[:4]}年{date_str[4:6]}月{date_str[6:8]}日",
                "generatedAt": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} 20:00:00",
                "news": []
            }
            
            lines = content.strip().split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('### '):
                    title = line[4:].strip()
                    i += 1
                    source = ''
                    summary = ''
                    link = ''
                    category = ''
                    
                    while i < len(lines) and not lines[i].startswith('### '):
                        current_line = lines[i].strip()
                        if current_line.startswith('**来源：**'):
                            source = current_line.replace('**来源：**', '').strip()
                        elif current_line.startswith('**摘要：**'):
                            summary = current_line.replace('**摘要：**', '').strip()
                        elif current_line.startswith('**链接：**'):
                            link = current_line.replace('**链接：**', '').strip()
                        elif current_line.startswith('**分类：**'):
                            category = current_line.replace('**分类：**', '').strip()
                        i += 1
                    
                    if title and source:
                        report["news"].append({
                            "id": len(report["news"]) + 1,
                            "title": title,
                            "source": source,
                            "summary": summary,
                            "link": link,
                            "category": category if category else "未分类"
                        })
                        sources_set.add(source)
                        categories_set.add(category if category else "未分类")
                        news_count += 1
            
            if report["news"]:
                report["newsCount"] = len(report["news"])
                reports.append(report)

reports.sort(key=lambda x: x["date"], reverse=True)

latest_date = reports[0]["displayDate"] if reports else "未知"

result = {
    "stats": {
        "totalReports": len(reports),
        "totalNews": news_count,
        "latestDate": latest_date,
        "sources": sorted(list(sources_set)),
        "categories": sorted(list(categories_set))
    },
    "reports": reports
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Generated {output_file}")
print(f"Total reports: {len(reports)}")
print(f"Total news: {news_count}")
print(f"Categories: {', '.join(sorted(list(categories_set)))}")
