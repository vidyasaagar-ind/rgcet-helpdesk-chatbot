import os
import json
import re
from pathlib import Path
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

def clean_text(text: str) -> str:
    """Normalizes whitespace and removes duplicated blank lines."""
    if not text:
        return ""
    
    # Remove excessive repeated blank lines (3 or more down to 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Normalize excessive spaces (2 or more down to 1 space, except newline blocks)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Strip leading/trailing junk
    text = text.strip()
    return text

def extract_from_txt(path: Path) -> str:
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def extract_from_pdf(path: Path) -> str:
    if not PdfReader:
        print(f"Warning: pypdf not installed. Cannot parse {path}. Run pip install pypdf.")
        return ""
    try:
        reader = PdfReader(str(path))
        extracted_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                extracted_text.append(t)
        return "\n".join(extracted_text)
    except Exception as e:
        print(f"Failed to read PDF {path}: {e}")
        return ""

def process_inventory():
    base_dir = Path(__file__).parent.parent
    inventory_path = base_dir / 'data' / 'metadata' / 'source_inventory.json'
    processed_dir = base_dir / 'data' / 'processed'
    
    if not inventory_path.exists():
        print(f"Error: Inventory not found at {inventory_path}")
        return
        
    with open(inventory_path, 'r', encoding='utf-8') as f:
        inventory = json.load(f)
        
    processed_dir.mkdir(parents=True, exist_ok=True)
    expected_output_files = set()
    
    processed_count = 0
    for entry in inventory:
        source_path = entry.get('raw_local_path') or entry.get('path_or_url', '')
        
        # We only process local file paths that exist in our structured backend
        if not source_path.startswith('backend/data/raw/'):
            print(f"Skipping {entry['id']}: No local raw file configured for processing.")
            continue
            
        full_source_path = base_dir.parent / source_path
        
        if not full_source_path.exists() or not full_source_path.is_file():
            print(f"Skipping {entry['id']}: File '{full_source_path}' does not exist or empty placeholder.")
            continue
            
        # Parse based on extension
        raw_text = ""
        ext = full_source_path.suffix.lower()
        if ext == '.pdf':
            raw_text = extract_from_pdf(full_source_path)
        elif ext in {'.txt', '.md'}:
            raw_text = extract_from_txt(full_source_path)
        else:
            print(f"Skipping {entry['id']}: Unsupported local raw format '{ext}' for text extraction.")
            continue
            
        cleaned = clean_text(raw_text)
        
        if not cleaned:
            print(f"Skipping {entry['id']}: No extractable text found.")
            continue
            
        tp = entry.get("trust_priority", "priority_4")
        if isinstance(tp, int) or (isinstance(tp, str) and str(tp).isdigit()):
            tp_str = f"priority_{tp}"
        elif isinstance(tp, str) and tp.startswith("priority_"):
            tp_str = tp
        else:
            tp_str = "priority_4"
            
        processed_record = {
            "id": entry.get("id"),
            "source_ref": entry.get("id"),
            "source_url": entry.get("path_or_url", ""),
            "raw_local_path": source_path,
            "source_type": entry.get("source_type", "unknown"),
            "title": entry.get("title") or full_source_path.name,
            "category": entry.get("category", "general"),
            "department": entry.get("department", "general"),
            "cleaned_text": cleaned,
            "trust_priority": tp_str,
            "reviewed": entry.get("reviewed", False),
            "notes": entry.get("notes") or ""
        }
        
        out_file = processed_dir / f"{entry['id']}.json"
        expected_output_files.add(out_file.name)
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(processed_record, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully processed and saved: {out_file.name}")
        processed_count += 1

    for existing_file in processed_dir.glob("*.json"):
        if existing_file.name not in expected_output_files:
            existing_file.unlink()
            print(f"Removed stale processed artifact: {existing_file.name}")
        
    print(f"\nPipeline complete. Processed {processed_count} files.")

if __name__ == "__main__":
    process_inventory()
