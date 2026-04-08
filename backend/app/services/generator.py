import re
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from app.core.config import settings
from app.services.logging_service import app_logger
from app.services.retrieve import retrieve_context

FALLBACK_RESPONSE = "I could not find reliable information in the approved college knowledge base."
PLACEHOLDER_TOKENS = (
    "[name",
    "[phone",
    "[email",
    "0000000000",
    "link_placeholder",
    "placeholder - edit required",
)
PLACEHOLDER_BRACKET_PATTERN = re.compile(r"\[[^\]]+\]")
SKIP_LINE_PREFIXES = (
    "category:",
    "department:",
    "status:",
    "trust priority:",
    "reviewed:",
    "last updated:",
    "notes:",
    "source ref:",
    "raw local path:",
)
URL_PATTERN = re.compile(r"https?://[^\s)>\]]+")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(?:\+91[\s-]*)?(?:\(?0?413\)?[\s-]*2615[\s-]*308(?:[\s,/-]*309)?|\(?\+91\)?[\s-]*\d{5}[\s-]*\d{5})")

try:
    genai.configure(api_key=settings.gemini_api_key)
except Exception as exc:
    app_logger.warning("Gemini configuration failed: %s", exc)

model_name = getattr(settings, "model_name", "models/gemini-2.0-flash")
try:
    model = genai.GenerativeModel(model_name)
except Exception as exc:
    app_logger.warning("Gemini model initialization failed for '%s': %s", model_name, exc)
    model = None


def build_grounding_prompt(user_query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    context_text = ""
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        title = chunk.get("title") or f"Document {idx}"
        text = chunk.get("text", "")
        context_text += f"Source ({title}):\n{text}\n\n"

    return f"""You are the RGCET Help Desk assistant.

Use ONLY the approved context below.

Write in a concise, professional helpdesk style:
- 2 to 4 short sentences when possible
- natural wording, not raw field labels
- no invented facts
- no external knowledge
- no unnecessary bullet lists

If the exact answer is clearly supported by the context, answer it directly.

If the exact fact is missing but the context contains a relevant official contact, email, phone number, or official page/form/download link, say that the fact is not confirmed in the approved college sources and then guide the user to that official contact or link.

If neither a direct answer nor a safe official redirect is supported by the context, reply exactly:
'{FALLBACK_RESPONSE}'

Context:
{context_text}

Question:
{user_query}
"""


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _clean_text_fragment(value: str) -> str:
    normalized = _normalize_space(value)
    if not normalized:
        return ""

    normalized = re.sub(r"\s*\(draft\)\s*", "", normalized, flags=re.IGNORECASE)
    normalized = normalized.strip(" :.-")
    if _contains_placeholder(normalized):
        return ""

    return normalized.strip()


def _contains_placeholder(value: str) -> bool:
    lowered = value.lower()
    if any(token in lowered for token in PLACEHOLDER_TOKENS):
        return True

    matches = PLACEHOLDER_BRACKET_PATTERN.findall(value)
    for token in matches:
        inner = token[1:-1].strip().lower()
        if "_" in inner:
            return True
        if any(
            marker in inner
            for marker in (
                "hod",
                "principal",
                "office",
                "department",
                "total",
                "count",
                "time",
                "location",
                "phone",
                "email",
                "days",
                "list",
                "overview",
                "name",
            )
        ):
            return True
    return False


def _infer_query_signal(query: str) -> str:
    lowered = query.lower()
    if any(token in lowered for token in ("how many department", "department count", "number of departments")):
        return "dept_count"
    if any(token in lowered for token in ("what departments", "department list", "departments are available")):
        return "dept_list"
    if any(token in lowered for token in ("course", "courses", "programme", "programmes", "program", "programs offered")):
        return "programmes"
    if any(token in lowered for token in ("what is rgcet", "tell me about this college", "about rgcet", "about this college", "what is this college")):
        return "overview"
    if any(token in lowered for token in ("where is the college located", "college located", "rgcet located", "where is rgcet")):
        return "college_location"
    if (
        any(token in lowered for token in ("admission", "admissions", "inquiry", "enquiry"))
        and any(token in lowered for token in ("where", "location", "located", "go"))
    ):
        return "admissions_location"
    if any(token in lowered for token in ("office timing", "timings", "office hours", "working hours")):
        return "timing"
    if "principal" in lowered:
        return "principal"
    if any(token in lowered for token in ("hod", "head of department")):
        return "hod"
    if lowered.startswith("who is"):
        return "person"
    if any(token in lowered for token in ("challan", "fee payment", "fees payment")):
        return "challan"
    if any(token in lowered for token in ("form", "forms", "bonafide", "hall ticket", "medical attendance", "download")):
        return "forms"
    if any(token in lowered for token in ("bus", "transport", "route")):
        return "transport"
    if any(token in lowered for token in ("placement", "training and placement", "recruiter", "internship")):
        return "placement"
    if any(token in lowered for token in ("admission", "eligibility", "apply", "inquiry", "admission office")):
        return "admissions"
    if any(token in lowered for token in ("contact", "phone", "email", "call", "reach")):
        return "contact"
    return "unknown"


def _is_college_related(query: str) -> bool:
    lowered = query.lower()
    if _infer_query_signal(query) != "unknown":
        return True

    college_terms = (
        "rgcet",
        "college",
        "campus",
        "department",
        "cse",
        "ece",
        "it",
        "bme",
        "admissions",
        "placement",
        "exam",
    )
    return any(term in lowered for term in college_terms)


def _infer_department_label(query: str) -> str:
    lowered = query.lower()
    department_map = {
        "cse": "CSE",
        "ece": "ECE",
        "it": "IT",
        "bme": "BME",
        "eee": "EEE",
        "mba": "MBA",
        "mca": "MCA",
    }
    for token, label in department_map.items():
        if token in lowered:
            return label
    return "the relevant department"


def _parse_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
    text = chunk.get("text", "")
    parsed: Dict[str, Any] = {
        "title": chunk.get("title", ""),
        "category": chunk.get("category", ""),
        "department": chunk.get("department", ""),
        "text": text,
        "fields": {},
        "answer_line": None,
        "urls": [],
        "emails": [],
        "phones": [],
        "clean_lines": [],
    }

    for raw_line in text.splitlines():
        line = _normalize_space(raw_line)
        if not line:
            continue

        lower_line = line.lower()
        if lower_line.startswith("question:"):
            continue
        if lower_line.startswith(SKIP_LINE_PREFIXES):
            continue

        if lower_line.startswith("answer:"):
            answer_line = _clean_text_fragment(line.split(":", 1)[1])
            if answer_line:
                parsed["answer_line"] = answer_line
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            normalized_key = _normalize_space(key).lower().replace(" ", "_")
            cleaned_value = _clean_text_fragment(value)
            if cleaned_value:
                parsed["fields"][normalized_key] = cleaned_value
                parsed["clean_lines"].append(f"{key.strip()}: {cleaned_value}")
            continue

        cleaned_line = _clean_text_fragment(line)
        if cleaned_line:
            parsed["clean_lines"].append(cleaned_line)

    parsed["urls"] = list(dict.fromkeys(URL_PATTERN.findall(text)))
    parsed["emails"] = list(dict.fromkeys(EMAIL_PATTERN.findall(text)))
    parsed["phones"] = list(dict.fromkeys(_normalize_space(match) for match in PHONE_PATTERN.findall(text)))

    return parsed


def _make_supported_payload(answer: str, sources_used: int = 1) -> Optional[Dict[str, Any]]:
    final_answer = _normalize_space(answer)
    if not final_answer or _contains_placeholder(final_answer):
        return None
    return {
        "answer": final_answer,
        "grounded": True,
        "sources_used": sources_used,
        "weak_results": False,
        "response_mode": "retrieval_only",
        "fallback_type": "supported",
    }


def _chunk_blob(parsed: Dict[str, Any]) -> str:
    return " ".join(
        [
            parsed.get("title", ""),
            parsed.get("category", ""),
            parsed.get("department", ""),
            parsed.get("text", ""),
        ]
    ).lower()


def _score_parsed_for_signal(signal: str, parsed: Dict[str, Any], query: str) -> int:
    blob = _chunk_blob(parsed)
    score = 0
    if parsed.get("category") == "official_general":
        score += 3

    if signal == "overview":
        if "institution overview" in blob:
            score += 10
        if "college location support" in blob:
            score += 6
        if "internet service" in blob or "transport service overview" in blob:
            score -= 5

    if signal == "college_location":
        if "location support" in blob:
            score += 12
        if "institution overview" in blob:
            score += 5
        if "transport service overview" in blob or "internet service" in blob:
            score -= 4

    if signal == "dept_count":
        if "department and programme coverage summary" in blob:
            score += 12
        if "department count and summary" in blob:
            score += 8
        if "contact helper" in blob:
            score -= 8

    if signal == "dept_list":
        if "programme list support" in blob or "programmes listed on home page" in blob:
            score += 10
        if "department and programme coverage summary" in blob:
            score += 8
        if "contact helper" in blob:
            score -= 8

    if signal == "programmes":
        if "programmes listed on home page" in blob:
            score += 10
        if "programme list support" in blob:
            score += 8

    if signal == "admissions_location":
        if parsed.get("category") in {"admissions", "contact_info", "official_general"}:
            score += 6
        if "admission office location support" in blob:
            score += 10
        if "admission" in blob or "admissions" in blob:
            score += 5
        if "placement" in blob:
            score -= 8
        if "admission inquiry form" in blob:
            score -= 6

    if signal == "principal":
        if "principal support" in blob or "trust and leadership" in blob:
            score += 10
        if "vice principal" in blob:
            score += 4

    if signal in {"hod", "timing"}:
        if "placeholder" in blob:
            score -= 4

    if query.lower().strip() in blob:
        score += 1
    return score


def _merge_unique_chunks(first: List[Dict[str, Any]], second: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen_ids = set()
    for chunk in first + second:
        chunk_id = chunk.get("chunk_id")
        if chunk_id and chunk_id in seen_ids:
            continue
        if chunk_id:
            seen_ids.add(chunk_id)
        merged.append(chunk)
    return merged


def _prioritize_chunks_for_query(query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    signal = _infer_query_signal(query)
    priority_chunks: List[Dict[str, Any]] = []

    if signal in {"overview", "college_location", "dept_count", "dept_list", "programmes", "principal"}:
        extra = retrieve_context(query=query, top_k=max(len(chunks), 4), filters={"category": "official_general"})
        priority_chunks = extra.get("results", [])

    if signal == "admissions_location":
        admissions_extra = retrieve_context(query="admission office location", top_k=4, filters={"category": "admissions"})
        contact_extra = retrieve_context(query="admission office location", top_k=3, filters={"category": "contact_info"})
        official_general_extra = retrieve_context(
            query="admission office location", top_k=2, filters={"category": "official_general"}
        )
        priority_chunks = (
            admissions_extra.get("results", [])
            + contact_extra.get("results", [])
            + official_general_extra.get("results", [])
        )

    merged = _merge_unique_chunks(priority_chunks, chunks)
    if not merged:
        return merged

    parsed_cache = {chunk.get("chunk_id", id(chunk)): _parse_chunk(chunk) for chunk in merged}

    def sort_key(chunk: Dict[str, Any]) -> tuple:
        key = chunk.get("chunk_id", id(chunk))
        parsed = parsed_cache[key]
        score = _score_parsed_for_signal(signal, parsed, query)
        distance = chunk.get("distance", 999.0)
        return (-score, distance)

    return sorted(merged, key=sort_key)


def _extract_principal_name(parsed: Dict[str, Any]) -> str:
    fields = parsed.get("fields", {})
    candidate_names = [
        fields.get("name", ""),
        fields.get("contact_person", ""),
    ]
    for candidate in candidate_names:
        cleaned = _clean_text_fragment(candidate)
        if cleaned and not _contains_placeholder(cleaned):
            return cleaned

    content = fields.get("content", "")
    if content:
        match = re.search(r"(?:names|lists)\s+([^,\n]+?)\s+as\s+(?:the\s+)?principal", content, flags=re.IGNORECASE)
        if match:
            cleaned = _clean_text_fragment(match.group(1))
            if cleaned and not _contains_placeholder(cleaned):
                return cleaned
    return ""


def _ensure_period(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    if value.endswith((".", "!", "?")):
        return value
    return f"{value}."


def _format_phone_list(phone_values: List[str]) -> str:
    cleaned = [value.replace(", ", " / ") for value in phone_values if value]
    cleaned = list(dict.fromkeys(cleaned))
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return ", ".join(cleaned[:-1]) + f", and {cleaned[-1]}"


def _naturalize_answer_line(signal: str, answer_line: str) -> str:
    if signal in {"admissions", "contact"}:
        normalized_line = re.sub(
            r"^Admission contact listed on the official page:\s*",
            "",
            answer_line,
            flags=re.IGNORECASE,
        )
        if "Contact numbers:" in normalized_line and "Office phone:" in normalized_line and "Email:" in normalized_line:
            person_segment, remainder = normalized_line.split("Contact numbers:", 1)
            mobiles_segment, remainder = remainder.split("Office phone:", 1)
            office_segment, email_segment = remainder.split("Email:", 1)

            person_segment = person_segment.strip().rstrip(".")
            person = person_segment
            designation = ""
            if "," in person_segment:
                person, designation = [part.strip() for part in person_segment.rsplit(",", 1)]

            mobiles = _normalize_space(mobiles_segment).rstrip(".")
            office_phone = _normalize_space(office_segment).rstrip(".")
            email = _normalize_space(email_segment).rstrip(".")

            sentences = []
            if designation:
                sentences.append(f"You can contact the admission office through {person}, {designation}.")
            else:
                sentences.append(f"You can contact the admission office through {person}.")
            sentences.append(f"The official mobile numbers listed are {mobiles}.")
            sentences.append(f"The office phone numbers are {office_phone.replace(', ', ' and ')}.")
            sentences.append(f"The email address is {email}.")
            return " ".join(sentences)

    if signal == "challan":
        match = re.search(r"link:\s*(https?://\S+)", answer_line, flags=re.IGNORECASE)
        if match:
            return f"You can download the official fee payment challan here: {match.group(1)}"

    return _ensure_period(answer_line)


def _gather_links(parsed_chunks: List[Dict[str, Any]]) -> List[str]:
    links: List[str] = []
    for parsed in parsed_chunks:
        for field_name in (
            "official_download_link",
            "official_image_link",
            "official_pdf_link",
            "official_form_link",
            "action_link",
            "official_page_url",
            "source_url",
            "website",
        ):
            value = parsed["fields"].get(field_name)
            if value and value.startswith("http"):
                links.append(value)
        links.extend(parsed["urls"])
    return list(dict.fromkeys(links))


def _build_supported_answer(query: str, chunks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    signal = _infer_query_signal(query)
    prioritized_chunks = _prioritize_chunks_for_query(query, chunks)
    parsed_chunks = [_parse_chunk(chunk) for chunk in prioritized_chunks]
    summary_signals = {
        "overview",
        "college_location",
        "dept_count",
        "dept_list",
        "programmes",
        "admissions_location",
        "principal",
        "hod",
        "timing",
    }

    if signal not in summary_signals:
        for parsed in parsed_chunks:
            answer_line = parsed.get("answer_line")
            if answer_line:
                payload = _make_supported_payload(_naturalize_answer_line(signal, answer_line))
                if payload:
                    return payload

    if signal in {"overview", "college_location", "dept_count", "dept_list", "programmes"}:
        for parsed in parsed_chunks:
            fields = parsed.get("fields", {})
            content = fields.get("content") or fields.get("description")
            if content:
                payload = _make_supported_payload(_ensure_period(content))
                if payload:
                    return payload

    if signal == "admissions_location":
        for parsed in parsed_chunks:
            relevance_blob = _chunk_blob(parsed)
            if "admission" not in relevance_blob and "admissions" not in relevance_blob:
                continue
            fields = parsed.get("fields", {})
            office_location = fields.get("office_location")
            person = fields.get("contact_person")
            office_phone = fields.get("office_phone") or fields.get("phone")
            email = fields.get("email")
            if office_location:
                sentences = [f"For admission enquiry, the approved sources point to {office_location}."]
                if person:
                    sentences.append(f"The listed contact person is {person}.")
                if office_phone:
                    sentences.append(f"Office phone: {office_phone}.")
                if email:
                    sentences.append(f"Email: {email}.")
                payload = _make_supported_payload(" ".join(sentences))
                if payload:
                    return payload

    if signal == "principal":
        for parsed in parsed_chunks:
            principal_name = _extract_principal_name(parsed)
            if principal_name:
                payload = _make_supported_payload(
                    f"The approved college sources list {principal_name} as the Principal."
                )
                if payload:
                    return payload

    for parsed in parsed_chunks:
        fields = parsed["fields"]
        links = _gather_links([parsed])

        if signal in {"admissions", "contact"}:
            person = fields.get("contact_person")
            designation = fields.get("designation")
            mobiles = fields.get("contact_numbers")
            office_phone = fields.get("office_phone") or fields.get("phone")
            email = fields.get("email") or (parsed["emails"][0] if parsed["emails"] else "")

            if person or office_phone or email:
                sentences: List[str] = []
                if person and designation:
                    sentences.append(f"You can contact the admission office through {person}, {designation}.")
                elif person:
                    sentences.append(f"You can contact the admission office through {person}.")
                if mobiles:
                    sentences.append(f"The official mobile numbers listed are {mobiles}.")
                if office_phone:
                    sentences.append(f"The office phone numbers are {office_phone.replace(', ', ' and ')}.")
                if email:
                    sentences.append(f"The email address is {email}.")

                payload = _make_supported_payload(" ".join(sentences))
                if payload:
                    return payload

        if signal == "challan":
            challan_link = fields.get("official_download_link") or (links[0] if links else "")
            if challan_link:
                bank_name = fields.get("bank_name")
                sentences = [f"You can download the official fee payment challan here: {challan_link}"]
                if bank_name:
                    sentences.append(f"The challan is issued for payment through {bank_name}.")
                payload = _make_supported_payload(" ".join(sentences))
                if payload:
                    return payload

        if signal == "forms":
            item_name = fields.get("item_name")
            form_link = fields.get("official_download_link") or fields.get("official_form_link") or fields.get("action_link") or (links[0] if links else "")
            if item_name and form_link:
                payload = _make_supported_payload(f"You can use the official {item_name} here: {form_link}")
                if payload:
                    return payload

        if signal == "transport":
            route_link = fields.get("official_image_link") or fields.get("official_pdf_link") or (links[0] if links else "")
            description = fields.get("description")
            if route_link and description:
                payload = _make_supported_payload(
                    f"{description} You can check the official route information here: {route_link}"
                )
                if payload:
                    return payload

        if signal == "placement":
            description = fields.get("description") or fields.get("content")
            email = fields.get("email") or (parsed["emails"][0] if parsed["emails"] else "")
            if description:
                sentences = [_ensure_period(description)]
                if email:
                    sentences.append(f"You can reach the placement team at {email}.")
                payload = _make_supported_payload(" ".join(sentences))
                if payload:
                    return payload

        if signal == "timing":
            time_fields = [value for key, value in fields.items() if any(token in key for token in ("time", "opening", "closing", "days"))]
            if time_fields:
                payload = _make_supported_payload(_ensure_period(" ".join(time_fields[:3])))
                if payload:
                    return payload

        if signal in {"hod", "person"}:
            person_name = fields.get("hod") or fields.get("name")
            if person_name:
                role = fields.get("role") or "HOD"
                payload = _make_supported_payload(f"The approved college sources list {person_name} as the {role}.")
                if payload:
                    return payload

    return None


def _build_redirect_query(signal: str, original_query: str) -> Optional[Dict[str, Any]]:
    if signal in {"timing", "hod", "principal", "person", "contact"}:
        return {
            "query": "official college contact details",
            "filters": {"category": "contact_info"},
        }
    if signal in {"admissions", "admissions_location"}:
        return {
            "query": "official admission contact details",
            "filters": {"category": "admissions"},
        }
    if signal == "placement":
        return {
            "query": "official placement contact details",
            "filters": {"category": "contact_info"},
        }
    if signal == "challan":
        return {
            "query": "official fee payment challan download link",
            "filters": {"category": "fees_forms"},
        }
    if signal == "forms":
        return {
            "query": "official downloadable forms",
            "filters": {"category": "fees_forms"},
        }
    if signal == "transport":
        return {
            "query": "official bus route information",
            "filters": {"category": "bus_routes"},
        }
    return None


def _select_redirect_support(query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    signal = _infer_query_signal(query)
    support_request = _build_redirect_query(signal, query)
    if not support_request:
        return []

    support_chunks = retrieve_context(
        support_request["query"],
        top_k=6,
        filters=support_request["filters"],
    )
    if not support_chunks.get("results"):
        return []

    redirect_threshold = settings.similarity_threshold + 0.15
    for candidate in support_chunks["results"]:
        top_distance = candidate.get("distance", 999.0)
        if top_distance > redirect_threshold:
            continue

        parsed = _parse_chunk(candidate)
        fields = parsed.get("fields", {})
        has_contact_value = any(
            fields.get(field_name)
            for field_name in ("email", "phone", "office_phone", "contact_numbers", "office_location")
        )
        has_extracted_contact = bool(parsed.get("emails") or parsed.get("phones"))
        has_link = bool(_gather_links([parsed]))

        if has_contact_value or has_extracted_contact or has_link:
            return [candidate]

    return []


def _build_redirect_answer(query: str, primary_chunks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not _is_college_related(query):
        return None

    signal = _infer_query_signal(query)
    support_chunks = _select_redirect_support(query, primary_chunks)
    if not support_chunks:
        return None

    parsed_support = [_parse_chunk(chunk) for chunk in support_chunks]
    emails: List[str] = []
    phones: List[str] = []
    links = _gather_links(parsed_support)

    for parsed in parsed_support:
        emails.extend(parsed["emails"])
        phones.extend(parsed["phones"])
        fields = parsed["fields"]
        for field_name in ("email", "office_phone", "phone", "contact_numbers"):
            field_value = fields.get(field_name)
            if field_value:
                if "@" in field_value:
                    emails.extend(EMAIL_PATTERN.findall(field_value))
                else:
                    phones.append(field_value)

    emails = list(dict.fromkeys(emails))
    phones = list(dict.fromkeys(_normalize_space(phone) for phone in phones if phone))

    contact_bits: List[str] = []
    if emails:
        contact_bits.append(f"Official email: {emails[0]}.")
    if phones:
        contact_bits.append(f"Official phone: {_format_phone_list(phones[:1])}.")
    if links:
        contact_bits.append(f"Official link: {links[0]}")

    if not contact_bits:
        return None

    if signal in {"hod", "person"}:
        department_label = _infer_department_label(query)
        redirect_prefix = f"I could not find a confirmed HOD name for {department_label} in the approved college sources. Please contact the college office for the latest department details."
    elif signal == "principal":
        redirect_prefix = "I could not find a fully confirmed principal detail in the approved college sources. Please contact the college office for the latest leadership information."
    elif signal == "timing":
        redirect_prefix = "I could not find officially published office timings in the approved college sources. Please contact the college office directly for confirmation."
    elif signal == "admissions_location":
        redirect_prefix = "I could not find a separately published admission office room location in the approved college sources. Please use the official admission contact below."
    elif signal == "placement":
        redirect_prefix = "I could not confirm that detail from the approved placement sources. Please use the official placement contact below."
    elif signal == "admissions":
        redirect_prefix = "I could not confirm that exact admission detail from the approved college sources. Please use the official admission contact below."
    elif signal == "transport":
        redirect_prefix = "I could not find a more specific confirmed transport detail in the approved college sources. Please use the official route information below."
    elif signal in {"forms", "challan"}:
        redirect_prefix = "I could not confirm a more specific form detail from the approved college sources. Please use the official link below."
    else:
        redirect_prefix = "I could not confirm that exact detail in the approved college sources. Please use the official contact details below."

    return {
        "answer": " ".join([redirect_prefix] + contact_bits),
        "grounded": True,
        "sources_used": len(support_chunks),
        "weak_results": False,
        "response_mode": "retrieval_redirect",
        "fallback_type": "redirect",
    }


def _fallback_payload(weak_results: bool, sources_used: int = 0) -> Dict[str, Any]:
    return {
        "answer": FALLBACK_RESPONSE,
        "grounded": False,
        "sources_used": sources_used,
        "weak_results": weak_results,
        "response_mode": "fallback",
        "fallback_type": "generic",
    }


def generate_answer(query: str, chunks: List[Dict[str, Any]], weak_results: bool = False) -> Dict[str, Any]:
    """
    Generate a grounded direct answer, a grounded official redirect, or the
    generic fallback when nothing safe is supported by approved data.
    """
    gemini_available = (
        settings.use_gemini
        and bool(settings.gemini_api_key)
        and settings.gemini_api_key not in {"placeholder", "placeholder_key"}
        and model is not None
    )

    app_logger.info("Generator entry | query='%s' | gemini_available=%s | chunks=%d | weak=%s", query, gemini_available, len(chunks), weak_results)

    if not _is_college_related(query):
        app_logger.info("Generator skipped | query='%s' | reason=out_of_domain", query)
        return _fallback_payload(weak_results=False, sources_used=0)

    if chunks and not weak_results and gemini_available:
        prompt = build_grounding_prompt(query, chunks)
        try:
            app_logger.info("Generator attempting Gemini | query='%s' | model='%s'", query, model_name)
            response = model.generate_content(prompt)
            answer_text = (response.text or "").strip()
            if answer_text and FALLBACK_RESPONSE.lower() not in answer_text.lower():
                return {
                    "answer": answer_text,
                    "grounded": True,
                    "sources_used": len(chunks),
                    "weak_results": False,
                    "response_mode": "gemini",
                    "fallback_type": "supported",
                }
            app_logger.info("Gemini returned fallback for '%s'; using non-Gemini path.", query)
        except Exception as exc:
            app_logger.warning(
                "Gemini call failed for '%s'. Exception: %s. Message: %s. Falling back to non-Gemini path.",
                query,
                type(exc).__name__,
                str(exc),
            )

    if chunks and not weak_results and not gemini_available:
        reason = "use_gemini_disabled" if not settings.use_gemini else "gemini_unavailable"
        app_logger.info("Generator skipped gemini | query='%s' | reason=%s", query, reason)

    # Now we are in non-Gemini paths (either disabled, failed, or returned fallback)
    if chunks and not weak_results:
        supported_answer = _build_supported_answer(query=query, chunks=chunks)
        if supported_answer:
            app_logger.info("Generator using structured retrieval-only answer | query='%s'", query)
            return supported_answer

    redirect_answer = _build_redirect_answer(query=query, primary_chunks=chunks)
    if redirect_answer:
        app_logger.info(
            "Generator redirect | query='%s' | reason=exact_fact_missing_but_safe_redirect_available",
            query,
        )
        return redirect_answer

    if weak_results or not chunks:
        app_logger.info(
            "Generator skipped | query='%s' | reason=%s",
            query,
            "weak_retrieval" if weak_results else "no_chunks",
        )
        return _fallback_payload(weak_results=weak_results, sources_used=0)

    app_logger.info(
        "Generator skipped | query='%s' | reason=no_safe_supported_answer_or_redirect",
        query,
    )
    return _fallback_payload(weak_results=False, sources_used=0)
