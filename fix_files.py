import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Fix 1: knowledge_store.py indentation
with open("knowledge_store.py", "r") as f:
    c = f.read()
old = '          cursor = conn.execute("SELECT COUNT(DISTINCT source_name) FROM articles")'
new = '        cursor = conn.execute("SELECT COUNT(DISTINCT source_name) FROM articles")'
c = c.replace(old, new)
old2 = '          stats["active_sources"] = cursor.fetchone()[0] or 0'
new2 = '        stats["active_sources"] = cursor.fetchone()[0] or 0'
c = c.replace(old2, new2)
with open("knowledge_store.py", "w") as f:
    f.write(c)
print("knowledge_store.py fixed")

# Fix 2: rss_feed.py \\r\\n literal issue
with open("data_sources/rss_feed.py", "r") as f:
    c = f.read()

import re
# Replace the broken line (literal backslash-r-backslash-n text)
c = re.sub(
    r'if not all_items:`r`n            self\.logger\.warning\("所有RSS源获取失败，使用模拟数据"\)`r`n            return self\._get_mock_data\(\)`r`n        `r`n        self\.logger\.info\(f"共获取到 \{len\(all_items\)\} 条RSS新闻"\)`r`n        return all_items',
    r'if not all_items:\n            self.logger.warning("所有RSS源获取失败，使用模拟数据")\n            return self._get_mock_data()\n        \n        self.logger.info(f"共获取到 {len(all_items)} 条RSS新闻")\n        return all_items',
    c
)

with open("data_sources/rss_feed.py", "w") as f:
    f.write(c)
print("rss_feed.py fixed")

print("DONE! Now go to Web -> Reload")
