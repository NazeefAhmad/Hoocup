import json

file_path = r"C:\Users\praga\Music\HOOCUP\aradhya.jsonl"
with open(file_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        stripped_line = line.strip()
        if stripped_line:  # Only process non-empty lines
            print(f"Line {i}: '{stripped_line}'")
            try:
                json.loads(stripped_line)
                print(f"Line {i}: Valid JSON")
            except json.JSONDecodeError as e:
                print(f"Line {i}: Error - {e}")
        else:
            print(f"Line {i}: Empty line")