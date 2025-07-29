import json

input_file = "initial_users_clean_fixed_ready.json"
output_file = "../initial_users_fixed.json"

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

for i, item in enumerate(data):
    if item.get("model") == "accounts.user":
        fields = item["fields"]
        # اگر national_code نبود یا خالی بود، مقدار جدید بده
        if not fields.get("national_code"):
            fields["national_code"] = f"90000{i:04d}"  # مثلاً 900000001, 900000002, ...

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ national_code اضافه شد:", output_file)
