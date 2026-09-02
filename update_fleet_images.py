import os

file_path = os.path.join(os.path.dirname(__file__), "j1939", "fleet_data.py")
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

lines = content.splitlines()
new_lines = []
current_id = ""

for line in lines:
    if '"id": "' in line and not line.strip().startswith("#"):
        current_id = line.split('"id": "')[1].split('"')[0]
    if '"image_url":' in line:
        line = f'        "image_url": "/static/images/cars/{current_id}.svg",'
    new_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines) + "\n")

print("Updated fleet_data.py with local SVG image paths!")
