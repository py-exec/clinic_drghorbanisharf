import json
import re

INPUT_FILE = "initial_roles_fixed.json"
OUTPUT_FILE = "../initial_roles_fixed_clean.json"


def slugify(value):
    value = value.lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_]+", "_", value)
    return value.strip("_")


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

seen_codes = set()
for obj in data:
    fields = obj.get("fields", {})
    code = fields.get("code")

    if not code:
        generated_code = slugify(fields["name"])
        original = generated_code
        i = 1
        while generated_code in seen_codes:
            generated_code = f"{original}_{i}"
            i += 1
        fields["code"] = generated_code
        print(f"🛠 code ساخته شد: {fields['name']} → {generated_code}")

    seen_codes.add(fields["code"])
    obj["fields"] = fields

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ فایل اصلاح‌شده ذخیره شد: {OUTPUT_FILE}")
