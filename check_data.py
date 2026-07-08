import json

with open('web/data/reports.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Latest Date: {data['stats']['latestDate']}")
print(f"Total News: {data['stats']['totalNews']}")
print(f"Total Reports: {data['stats']['totalReports']}")
