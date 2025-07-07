import json

# 读取JSON文件
with open('knowledge_base.json', 'r', encoding='utf-8') as f:
    content = f.read()

# 解析JSON
data = json.loads(content)

# 重新写入格式化的JSON
with open('knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4) 