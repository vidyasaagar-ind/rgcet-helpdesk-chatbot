import difflib
import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

METADATA_KEYS = {
    "id",
    "source_ref",
    "source_type",
    "trust_priority",
    "reviewed",
    "last_updated",
    "notes",
    "status",
    "path_or_url",
    "raw_local_path",
}

STRUCTURED_EXCLUDE_FILES = {
    "source_inventory.json",
    "manual_faq_seed.json",
}

RETRIEVAL_USEFUL_STRUCTURED_FILES = {
    "admissions.json",
    "bus_routes.json",
    "contact_info.json",
    "departments.json",
    "facilities.json",
    "fees_forms.json",
    "hod_faculty.json",
    "office_timings.json",
    "official_general.json",
}

PLACEHOLDER_BRACKET_PATTERN = re.compile(r"\[[^\]]+\]")
WHITESPACE_PATTERN = re.compile(r"\s+")

TITLE_FIELD_CANDIDATES = (
    "title",
    "topic",
    "item_name",
    "office_name",
    "contact_type",
    "department_name",
    "facility_name",
    "official_page_title",
    "route_name",
    "question",
    "name",
)

KEY_LABELS = {
    "question": "Question",
    "answer": "Answer",
    "content": "Content",
    "description": "Description",
    "office_location": "Office Location",
    "email": "Email",
    "phone": "Phone",
    "office_phone": "Office Phone",
    "contact_numbers": "Contact Numbers",
    "action_link": "Official Link",
    "official_download_link": "Official Download Link",
    "official_form_link": "Official Form Link",
    "official_image_link": "Official Image Link",
    "official_pdf_link": "Official PDF Link",
    "official_page_url": "Official Page URL",
    "website": "Website",
    "programme_type": "Programme Type",
    "notable_gallery_items": "Notable Gallery Items",
    "undergraduate_eligibility": "UG Eligibility",
    "lateral_entry_eligibility": "Lateral Entry Eligibility",
    "mca_eligibility": "MCA Eligibility",
    "mba_eligibility": "MBA Eligibility",
    "ug_programmes": "UG Programmes",
    "pg_programmes": "PG Programmes",
    "enquiry_guidance": "Enquiry Guidance",
    "usage_note": "Usage Note",
    "review_note": "Review Note",
}

PREFERRED_KEY_ORDER = (
    "question",
    "answer",
    "content",
    "description",
    "contact_person",
    "designation",
    "office_location",
    "contact_numbers",
    "office_phone",
    "phone",
    "email",
    "undergraduate_eligibility",
    "lateral_entry_eligibility",
    "mca_eligibility",
    "mba_eligibility",
    "ug_programmes",
    "pg_programmes",
    "enquiry_guidance",
    "action_link",
    "official_download_link",
    "official_form_link",
    "official_image_link",
    "official_pdf_link",
    "official_page_url",
    "website",
    "programme_type",
    "notable_gallery_items",
    "coverage_notes",
    "usage_note",
    "review_note",
)

SUPPORT_RECORD_ALLOWLIST = {
    "general_hod_support_official",
    "general_office_timings_support_official",
    "general_principal_support_official",
    "general_department_count_support_official",
}


def normalize_space(value: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", str(value)).strip()


def canonicalize_text(value: str) -> str:
    lowered = normalize_space(value).lower()
    lowered = re.sub(r"[^a-z0-9\s]", "", lowered)
    return normalize_space(lowered)


def contains_unresolved_placeholder(value: str) -> bool:
    matches = PLACEHOLDER_BRACKET_PATTERN.findall(value)
    if not matches:
        return False
    for token in matches:
        inner = token[1:-1].strip()
        # If there is a bracket token with uppercase marker/underscore/digits, treat it as unresolved placeholder.
        if re.search(r"[A-Z0-9_]", inner):
            return True
    return False


def value_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        clean_items = [normalize_space(str(item)) for item in value if normalize_space(str(item))]
        return "; ".join(clean_items)
    return normalize_space(str(value))


def trust_priority_rank(value: str) -> int:
    if isinstance(value, str) and value.startswith("priority_"):
        try:
            return int(value.split("_", 1)[1])
        except ValueError:
            return 99
    return 99


def derive_category(record: Dict[str, Any], file_stem: str) -> str:
    category = normalize_space(str(record.get("category", ""))).lower()
    if category:
        return category
    if file_stem == "manual_faq_seed":
        return "faq"
    return file_stem.lower()


def derive_department(record: Dict[str, Any]) -> str:
    for key in ("department", "related_department", "department_code"):
        value = normalize_space(str(record.get(key, "")))
        if value:
            return value.lower()
    return "general"


def humanize_identifier(value: str) -> str:
    text = normalize_space(value.replace("_", " ").replace("-", " "))
    return text.title()


def derive_title(record: Dict[str, Any], file_stem: str, category: str) -> str:
    for field in TITLE_FIELD_CANDIDATES:
        raw = value_to_text(record.get(field))
        if raw and not contains_unresolved_placeholder(raw):
            if field == "department_name":
                code = value_to_text(record.get("department_code"))
                if code:
                    return f"{raw} Department ({code})"
                return f"{raw} Department"
            if field == "contact_type":
                person = value_to_text(record.get("name"))
                if person and not contains_unresolved_placeholder(person):
                    return f"{raw}: {person}"
            if field == "office_name":
                if any(value_to_text(record.get(k)) for k in ("contact_person", "office_phone", "contact_numbers", "email")):
                    return f"{raw} Contact"
            if field == "name" and value_to_text(record.get("contact_type")):
                continue
            return raw

    record_id = value_to_text(record.get("id"))
    if record_id:
        return humanize_identifier(record_id)

    if file_stem:
        return humanize_identifier(file_stem)
    return f"{humanize_identifier(category)} Record"


def ordered_keys(record: Dict[str, Any]) -> List[str]:
    seen = set()
    ordered = []
    for key in PREFERRED_KEY_ORDER:
        if key in record:
            ordered.append(key)
            seen.add(key)
    for key in sorted(record.keys()):
        if key not in seen:
            ordered.append(key)
    return ordered


def should_skip_structured_record(record: Dict[str, Any], file_stem: str) -> Tuple[bool, str]:
    if not isinstance(record, dict):
        return True, "not_dict"

    record_id = value_to_text(record.get("id"))
    if file_stem not in {"manual_faq_seed"} and not bool(record.get("reviewed", False)):
        if record_id in SUPPORT_RECORD_ALLOWLIST:
            return False, ""
        return True, "unreviewed_placeholder_or_draft"

    text_blob_parts = []
    for key, value in record.items():
        if key in METADATA_KEYS:
            continue
        text_value = value_to_text(value)
        if text_value:
            text_blob_parts.append(text_value)
    text_blob = " ".join(text_blob_parts)
    if contains_unresolved_placeholder(text_blob):
        if record_id in SUPPORT_RECORD_ALLOWLIST and bool(record.get("reviewed", False)):
            return False, ""
        return True, "contains_unresolved_placeholder"

    if file_stem == "source_inventory":
        return True, "metadata_inventory_record"

    return False, ""


def format_structured_text(record: Dict[str, Any], title: str) -> str:
    lines: List[str] = [f"Title: {title}"]

    for key in ordered_keys(record):
        if key in METADATA_KEYS:
            continue
        if key in {"title"}:
            continue

        value = value_to_text(record.get(key))
        if not value:
            continue
        if contains_unresolved_placeholder(value):
            continue

        label = KEY_LABELS.get(key, key.replace("_", " ").title())
        if key == "question":
            lines.append(f"Question: {value}")
            continue
        if key == "answer":
            lines.append(f"Answer: {value}")
            continue
        lines.append(f"{label}: {value}")

    normalized_lines = [normalize_space(line) for line in lines if normalize_space(line)]
    return "\n".join(normalized_lines).strip()


def chunk_text(text: str, max_chars: int = 1400) -> List[str]:
    value = text.strip()
    if not value:
        return []
    if len(value) <= max_chars:
        return [value]

    blocks = [block.strip() for block in re.split(r"\n{2,}", value) if block.strip()]
    chunks: List[str] = []
    current = ""
    for block in blocks:
        proposed = f"{current}\n\n{block}" if current else block
        if len(proposed) <= max_chars:
            current = proposed
            continue
        if current:
            chunks.append(current.strip())
        current = block

        if len(current) > max_chars:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", current) if s.strip()]
            current = ""
            for sentence in sentences:
                proposed_sentence = f"{current} {sentence}".strip()
                if len(proposed_sentence) <= max_chars:
                    current = proposed_sentence
                else:
                    if current:
                        chunks.append(current.strip())
                    current = sentence

    if current:
        chunks.append(current.strip())
    return chunks


def deterministic_chunk_id(source_ref: str, source_record_id: str, record_type: str, chunk_idx: int, text: str) -> str:
    base = "|".join(
        [
            normalize_space(source_ref),
            normalize_space(source_record_id),
            normalize_space(record_type),
            str(chunk_idx),
            canonicalize_text(text),
        ]
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, base))


def build_chunk_payload(
    chunk_text_value: str,
    record: Dict[str, Any],
    record_type: str,
    chunk_idx: int,
    total_chunks: int,
    source_type: str,
    category: str,
    department: str,
    title: str,
) -> Dict[str, Any]:
    source_record_id = value_to_text(record.get("id")) or value_to_text(record.get("source_ref"))
    source_ref = value_to_text(record.get("source_ref")) or source_record_id or f"unknown_{record_type}"

    return {
        "chunk_id": deterministic_chunk_id(source_ref, source_record_id, record_type, chunk_idx, chunk_text_value),
        "source_ref": source_ref,
        "source_type": source_type,
        "source_record_id": source_record_id,
        "title": title or "Untitled Record",
        "category": category or "general",
        "department": department or "general",
        "trust_priority": value_to_text(record.get("trust_priority")) or "priority_4",
        "reviewed": bool(record.get("reviewed", False)),
        "chunk_index": chunk_idx,
        "chunk_count": total_chunks,
        "text": chunk_text_value,
        "notes": value_to_text(record.get("notes")),
        "record_type": record_type,
    }


def chunk_quality_score(chunk: Dict[str, Any]) -> Tuple[int, int, int, int]:
    reviewed_score = 1 if chunk.get("reviewed") else 0
    priority_score = 100 - trust_priority_rank(chunk.get("trust_priority", "priority_99"))
    record_type = chunk.get("record_type", "")
    record_score = 3 if record_type == "structured_node" else 2 if record_type == "extracted_document" else 1
    length_score = len(canonicalize_text(chunk.get("text", "")))
    return reviewed_score, priority_score, record_score, length_score


def dedupe_exact_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for chunk in chunks:
        key = (chunk.get("category", ""), canonicalize_text(chunk.get("text", "")))
        if not key[1]:
            continue
        existing = deduped.get(key)
        if not existing:
            deduped[key] = chunk
            continue
        if chunk_quality_score(chunk) > chunk_quality_score(existing):
            deduped[key] = chunk
    return list(deduped.values())


def is_near_duplicate(candidate_text: str, existing_chunks: List[Dict[str, Any]], category: str, threshold: float = 0.93) -> bool:
    candidate = canonicalize_text(candidate_text)
    if not candidate:
        return True
    for chunk in existing_chunks:
        if chunk.get("category") != category:
            continue
        baseline = canonicalize_text(chunk.get("text", ""))
        if not baseline:
            continue
        ratio = difflib.SequenceMatcher(None, candidate, baseline).ratio()
        if ratio >= threshold:
            return True
    return False


def process_structured_files(base_dir: Path, out_file: Path) -> List[Dict[str, Any]]:
    structured_dir = base_dir / "data" / "structured"
    metadata_dir = base_dir / "data" / "metadata"
    structured_files = sorted(
        [
            path
            for path in structured_dir.glob("*.json")
            if path.name in RETRIEVAL_USEFUL_STRUCTURED_FILES and path.name not in STRUCTURED_EXCLUDE_FILES
        ]
    )

    all_chunks: List[Dict[str, Any]] = []
    skipped_counters: Dict[str, int] = {}

    for file_path in structured_files:
        try:
            records = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(records, list):
            continue

        file_stem = file_path.stem
        for record in records:
            skip, reason = should_skip_structured_record(record, file_stem)
            if skip:
                skipped_counters[reason] = skipped_counters.get(reason, 0) + 1
                continue

            category = derive_category(record, file_stem)
            department = derive_department(record)
            title = derive_title(record, file_stem, category)
            text_representation = format_structured_text(record, title)
            if not text_representation:
                skipped_counters["empty_text"] = skipped_counters.get("empty_text", 0) + 1
                continue
            if contains_unresolved_placeholder(text_representation):
                skipped_counters["placeholder_text"] = skipped_counters.get("placeholder_text", 0) + 1
                continue

            raw_chunks = chunk_text(text_representation)
            total = len(raw_chunks)
            for idx, c_text in enumerate(raw_chunks, start=1):
                payload = build_chunk_payload(
                    chunk_text_value=c_text,
                    record=record,
                    record_type="structured_node",
                    chunk_idx=idx,
                    total_chunks=total,
                    source_type="structured",
                    category=category,
                    department=department,
                    title=title,
                )
                all_chunks.append(payload)

    faq_file = metadata_dir / "manual_faq_seed.json"
    if faq_file.exists():
        try:
            faq_records = json.loads(faq_file.read_text(encoding="utf-8"))
        except Exception:
            faq_records = []
        if isinstance(faq_records, list):
            for record in faq_records:
                if not isinstance(record, dict):
                    continue
                if not bool(record.get("reviewed", False)):
                    continue
                question = value_to_text(record.get("question"))
                answer = value_to_text(record.get("answer"))
                if not question or not answer:
                    continue
                faq_text = f"Question: {question}\nAnswer: {answer}"
                if contains_unresolved_placeholder(faq_text):
                    continue

                category = derive_category(record, "manual_faq_seed")
                if is_near_duplicate(faq_text, all_chunks, category=category):
                    continue

                title = question
                payload = build_chunk_payload(
                    chunk_text_value=faq_text,
                    record=record,
                    record_type="faq_node",
                    chunk_idx=1,
                    total_chunks=1,
                    source_type="structured",
                    category=category,
                    department=derive_department(record),
                    title=title,
                )
                all_chunks.append(payload)

    all_chunks = dedupe_exact_chunks(all_chunks)
    all_chunks.sort(key=lambda chunk: (chunk.get("category", ""), chunk.get("source_record_id", ""), chunk.get("chunk_index", 0)))

    out_file.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Generated {len(all_chunks)} structured chunks from {len(structured_files)} structured files"
        f" (+FAQ seed) -> {out_file.name}"
    )
    if skipped_counters:
        print(f"Structured skip summary: {skipped_counters}")
    return all_chunks


def process_processed_content(base_dir: Path, out_file: Path) -> List[Dict[str, Any]]:
    processed_dir = base_dir / "data" / "processed"
    processed_files = sorted(processed_dir.glob("*.json"))
    all_chunks: List[Dict[str, Any]] = []

    for file_path in processed_files:
        try:
            record = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(record, dict):
            continue

        text = value_to_text(record.get("cleaned_text"))
        if not text:
            continue

        if contains_unresolved_placeholder(text):
            # Processed extracts should represent official sources; unresolved placeholders are noise.
            continue

        title = derive_title(record, file_path.stem, derive_category(record, file_path.stem))
        category = derive_category(record, file_path.stem)
        department = derive_department(record)
        source_type = value_to_text(record.get("source_type")) or "document"

        raw_chunks = chunk_text(text)
        total = len(raw_chunks)
        for idx, c_text in enumerate(raw_chunks, start=1):
            payload = build_chunk_payload(
                chunk_text_value=c_text,
                record=record,
                record_type="extracted_document",
                chunk_idx=idx,
                total_chunks=total,
                source_type=source_type,
                category=category,
                department=department,
                title=title,
            )
            all_chunks.append(payload)

    all_chunks = dedupe_exact_chunks(all_chunks)
    all_chunks.sort(key=lambda chunk: (chunk.get("category", ""), chunk.get("source_record_id", ""), chunk.get("chunk_index", 0)))
    out_file.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {len(all_chunks)} processed chunks for {len(processed_files)} processed files -> {out_file.name}")
    return all_chunks


def run_chunking() -> None:
    base_dir = Path(__file__).parent.parent
    chunks_dir = base_dir / "data" / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    structured_chunks_path = chunks_dir / "structured_chunks.json"
    struct_chunks = process_structured_files(base_dir, structured_chunks_path)

    processed_chunks_path = chunks_dir / "processed_chunks.json"
    proc_chunks = process_processed_content(base_dir, processed_chunks_path)

    all_chunks_path = chunks_dir / "all_chunks.json"
    all_chunks = dedupe_exact_chunks((struct_chunks or []) + (proc_chunks or []))
    all_chunks.sort(key=lambda chunk: (chunk.get("category", ""), chunk.get("source_record_id", ""), chunk.get("chunk_index", 0)))
    all_chunks_path.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Combined {len(all_chunks)} total chunks -> {all_chunks_path.name}")
    print("\nChunking pipeline complete.")


if __name__ == "__main__":
    run_chunking()
