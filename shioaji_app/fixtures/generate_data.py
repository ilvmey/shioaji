import json
import os

# cwd = os.getcwd()

data = [
    './shioaji_app/fixtures/industry/data.json',
    './shioaji_app/fixtures/stock_code/data.json',
]

if __name__ == "__main__":
    output = []
    for path in data:
        with open(path, 'r', encoding='utf-8') as f:
            rows = json.load(f)
            output.extend(rows)
    with open('./shioaji_app/fixtures/data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)