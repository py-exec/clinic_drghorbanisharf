import json
from datetime import datetime

file_path = 'initial_menu_data_fixed_ready.json'
output_path = 'initial_menu_data_final.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

for obj in data:
    fields = obj['fields']
    fields.setdefault('created_at', now)
    fields.setdefault('updated_at', now)
    fields.setdefault('link_type', 'none')
    if not fields.get('icon'):
        fields['icon'] = 'bx-circle'  # مقدار پیش‌فرض

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ فایل اصلاح‌شده ذخیره شد: {output_path}")
