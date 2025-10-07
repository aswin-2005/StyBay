import json
import os
from datetime import datetime
from pathlib import Path

def dump_batch_to_json(products_batch, output_dir="output/debug_dumps"):
    """
    Dump a batch of product dicts into a timestamped JSON file.
    
    Args:
        products_batch (list[dict]): List of product dictionaries to dump.
        output_dir (str): Folder to store the JSON dumps (default: ./debug_dumps).
    
    Returns:
        str: Path to the JSON file written.
    """
    if not products_batch:
        print("⚠️ No products to dump.")
        return None

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create a unique timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"products_batch_{timestamp}.json"
    file_path = os.path.join(output_dir, file_name)

    try:
        # Serialize with indentation for readability
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(products_batch, f, indent=2, ensure_ascii=False)

        print(f"✅ Dumped {len(products_batch)} products → {file_path}")
        return file_path

    except Exception as e:
        print(f"⚠️ Failed to dump batch: {e}")
        return None
