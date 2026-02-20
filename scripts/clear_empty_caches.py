import os
import json

def clear_empty_caches():
    print("=== Clearing Empty Local Caches ===")
    data_dir = "data"
    if not os.path.exists(data_dir):
        print("Data directory not found. Nothing to clear.")
        return

    cleared_count = 0
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file == "questions.json":
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list) and len(data) == 0:
                            os.remove(file_path)
                            cleared_count += 1
                            print(f"Removed empty cache: {file_path}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    print("-" * 30)
    print(f"Done! Cleared {cleared_count} empty cache files.")
    print("You can now run 'python scripts/sync_data.py' to retry scraping.")

if __name__ == "__main__":
    clear_empty_caches()
