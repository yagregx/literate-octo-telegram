import json
import csv
import sys
from pathlib import Path

def json_to_csv(json_file, csv_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        raise ValueError("JSON must be a list of objects or a single object")
    
    if not data:
        print("Warning: JSON file is empty")
        return
    
    all_keys = set()
    for obj in data:
        if isinstance(obj, dict):
            all_keys.update(obj.keys())
    
    fieldnames = sorted(list(all_keys))
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"✓ Converted {json_file} to {csv_file}")
    print(f"  Rows: {len(data)}, Columns: {len(fieldnames)}")


def csv_to_json(csv_file, json_file):
    data = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Converted {csv_file} to {json_file}")
    print(f"  Objects: {len(data)}")


def main():
    if len(sys.argv) < 4:
        print("Usage:")
        print("  python csv_json_converter.py json-to-csv <input.json> <output.csv>")
        print("  python csv_json_converter.py csv-to-json <input.csv> <output.json>")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    input_file = sys.argv[2]
    output_file = sys.argv[3]
    
    if not Path(input_file).exists():
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    try:
        if command == "json-to-csv":
            json_to_csv(input_file, output_file)
        elif command == "csv-to-json":
            csv_to_json(input_file, output_file)
        else:
            print(f"Error: Unknown command '{command}'")
            print("Use 'json-to-csv' or 'csv-to-json'")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
