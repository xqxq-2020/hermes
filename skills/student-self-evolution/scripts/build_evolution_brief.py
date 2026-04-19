from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable


SUPPORTED_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030", "cp936")

EVAL_COLUMNS = {
    "user_id",
    "content",
    "overall",
    "word",
    "score",
    "phone_char",
    "phone_score",
    "date_str",
}

TEXTBOOK_COLUMNS = {
    "user_id",
    "book_name",
    "name",
    "basic",
    "listening_score",
    "utilize_score",
    "pronunciation_score",
    "semantics_score",
    "writing_score",
}

LISTENING_RESOURCE_KEYS = {
    "年级",
    "关联题目数量",
    "版本",
    "册",
    "题干集合",
    "单元名称",
    "设置的题目数量",
    "级别",
    "学科",
    "对应端类型",
}

WORD_RESOURCE_KEYS = {
    "例句",
    "年级",
    "版本",
    "释义",
    "册",
    "单词",
    "id",
    "单词名称",
    "单元名称",
    "音频",
    "学科",
}

PICTUREBOOK_RESOURCE_KEYS = {
    "阅读时长",
    "年级",
    "封面",
    "主题",
    "分类二",
    "单词",
    "简介",
    "id",
    "脚本",
    "分类一",
    "中文名称",
    "词汇量",
    "英文名称",
}

GRADE_CODE_MAP = {
    "一年级": "oneGrade",
    "二年级": "twoGrade",
    "三年级": "threeGrade",
    "四年级": "fourGrade",
    "五年级": "fiveGrade",
    "六年级": "sixGrade",
}


@dataclass
class LoadedCsv:
    path: Path
    encoding: str
    headers: list[str]
    rows: list[dict[str, str]]
    kind: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a markdown evolution brief from MEMORY.md, USER.md, and supported CSV evidence.",
    )
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--memory", help="Path to MEMORY.md. Defaults to <workspace>/MEMORY.md.")
    parser.add_argument("--user", help="Path to USER.md. Defaults to <workspace>/USER.md.")
    parser.add_argument("--data-dir", help="Path to data directory. Defaults to <workspace>/data.")
    parser.add_argument("--output", help="Optional path to save the markdown brief.")
    return parser.parse_args()


def read_text(path: Path) -> str:
    for encoding in SUPPORTED_ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def load_csv(path: Path) -> LoadedCsv | None:
    raw = path.read_bytes()
    text = None
    used_encoding = None
    for encoding in SUPPORTED_ENCODINGS:
        try:
            text = raw.decode(encoding)
            used_encoding = encoding
            break
        except UnicodeDecodeError:
            continue
    if text is None or used_encoding is None:
        return None

    reader = csv.DictReader(text.splitlines())
    if reader.fieldnames is None:
        return None
    raw_headers = [header or "" for header in reader.fieldnames]
    headers = [header.strip() for header in raw_headers]
    rows = []
    for raw_row in reader:
        cleaned_row = {}
        for key, value in raw_row.items():
            cleaned_key = (key or "").strip()
            cleaned_row[cleaned_key] = value.strip() if isinstance(value, str) else value
        rows.append(cleaned_row)
    if not rows:
        return None
    header_set = set(headers)

    if EVAL_COLUMNS.issubset(header_set):
        kind = "oral_eval"
    elif TEXTBOOK_COLUMNS.issubset(header_set):
        kind = "textbook_vocab"
    else:
        json_rows = load_wrapped_json_lines(text)
        if json_rows:
            json_headers = sorted({key for row in json_rows for key in row.keys()})
            json_header_set = set(json_headers)
            if LISTENING_RESOURCE_KEYS.issubset(json_header_set):
                kind = "listening_catalog"
                rows = json_rows
                headers = json_headers
            elif WORD_RESOURCE_KEYS.issubset(json_header_set):
                kind = "word_catalog"
                rows = json_rows
                headers = json_headers
            elif PICTUREBOOK_RESOURCE_KEYS.issubset(json_header_set):
                kind = "picturebook_catalog"
                rows = json_rows
                headers = json_headers
            else:
                return LoadedCsv(path=path, encoding=used_encoding, headers=headers, rows=rows, kind="unsupported")
        else:
            return LoadedCsv(path=path, encoding=used_encoding, headers=headers, rows=rows, kind="unsupported")

    return LoadedCsv(path=path, encoding=used_encoding, headers=headers, rows=rows, kind=kind)


def load_wrapped_json_lines(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            first = json.loads(line)
            obj = json.loads(first) if isinstance(first, str) else first
            if not isinstance(obj, dict):
                return []
            cleaned = {}
            for key, value in obj.items():
                cleaned_key = str(key).strip()
                cleaned[cleaned_key] = value.strip() if isinstance(value, str) else value
            rows.append(cleaned)
        except Exception:
            return []
    return rows


def safe_float(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def compact_number(value: object) -> str:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "0"
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def avg(values: Iterable[float]) -> float:
    values = list(values)
    return mean(values) if values else 0.0


def top_n(counter: Counter[str], n: int) -> list[tuple[str, int]]:
    return counter.most_common(n)


def unique_keep_order(items: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def normalize_term(value: object) -> str:
    return str(value or "").strip().lower()


def strip_html(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_prompt_sample(value: object) -> str:
    text = strip_html(value)
    text = re.sub(r"\|space(?:\s+space)?\|", "_", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"(,\s*){3,}", ", ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,")


def split_resource_words(value: object) -> list[str]:
    text = str(value or "")
    parts = re.split(r"[,，;/、]+", text)
    return [part.strip() for part in parts if part.strip()]


def matched_terms(text: object, target_terms: list[str]) -> list[str]:
    normalized_text = normalize_term(strip_html(text))
    matches = []
    for term in target_terms:
        normalized_term = normalize_term(term)
        if normalized_term and normalized_term in normalized_text:
            matches.append(term)
    return matches


def score_overlap(values: Iterable[object], target_terms: list[str]) -> list[str]:
    matches: list[str] = []
    for value in values:
        matches.extend(matched_terms(value, target_terms))
    return unique_keep_order(matches)


def analyze_oral_eval(rows: list[dict[str, str]]) -> dict[str, object]:
    user_counts = Counter(row["user_id"] for row in rows if row.get("user_id"))
    primary_user, primary_count = user_counts.most_common(1)[0]
    user_rows = [row for row in rows if row.get("user_id") == primary_user]

    date_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in user_rows:
        date_groups[row.get("date_str", "")].append(row)

    weak_phones = []
    phone_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in user_rows:
        phone = row.get("phone_char", "").strip()
        if phone:
            phone_groups[phone].append(row)
    for phone, group in phone_groups.items():
        if len(group) >= 5:
            weak_phones.append((phone, len(group), round(avg(safe_float(r.get("phone_score")) for r in group), 2)))
    weak_phones.sort(key=lambda item: (item[2], -item[1], item[0]))

    strong_phones = list(reversed(sorted(weak_phones, key=lambda item: (item[2], item[1], item[0]))))[:5]

    word_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in user_rows:
        word = row.get("word", "").strip()
        if word:
            word_groups[word].append(row)

    weak_words = []
    strong_words = []
    for word, group in word_groups.items():
        if len(group) >= 5:
            score = round(avg(safe_float(r.get("score")) for r in group), 2)
            weak_words.append((word, len(group), score))
            strong_words.append((word, len(group), score))
    weak_words.sort(key=lambda item: (item[2], -item[1], item[0]))
    strong_words.sort(key=lambda item: (-item[2], -item[1], item[0]))

    content_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in user_rows:
        content = row.get("content", "").strip()
        if content:
            content_groups[content].append(row)

    weak_contents = []
    for content, group in content_groups.items():
        weak_contents.append((content, len(group), round(avg(safe_float(r.get("overall")) for r in group), 2)))
    weak_contents.sort(key=lambda item: (item[2], -item[1], item[0]))

    return {
        "primary_user": primary_user,
        "primary_count": primary_count,
        "total_rows": len(rows),
        "user_count": len(user_counts),
        "date_min": min(date_groups) if date_groups else "",
        "date_max": max(date_groups) if date_groups else "",
        "date_scores": [
            {
                "date": date,
                "avg_overall": round(avg(safe_float(r.get("overall")) for r in group), 2),
                "avg_phone": round(avg(safe_float(r.get("phone_score")) for r in group), 2),
                "count": len(group),
            }
            for date, group in sorted(date_groups.items())
        ],
        "unique_contents": len(content_groups),
        "unique_words": len(word_groups),
        "avg_overall": round(avg(safe_float(r.get("overall")) for r in user_rows), 2),
        "avg_word_score": round(avg(safe_float(r.get("score")) for r in user_rows), 2),
        "avg_phone_score": round(avg(safe_float(r.get("phone_score")) for r in user_rows), 2),
        "weak_phones": weak_phones[:8],
        "strong_phones": strong_phones,
        "weak_words": weak_words[:8],
        "strong_words": strong_words[:8],
        "weak_contents": weak_contents[:5],
    }


def analyze_textbook_vocab(rows: list[dict[str, str]]) -> dict[str, object]:
    user_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    word_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        user_groups[row.get("user_id", "")].append(row)
        word_groups[row.get("name", "")].append(row)

    user_summaries = []
    for user_id, group in user_groups.items():
        user_summaries.append(
            {
                "user_id": user_id,
                "words": len(group),
                "avg_basic": round(avg(safe_float(r.get("basic")) for r in group), 2),
                "avg_listening": round(avg(safe_float(r.get("listening_score")) for r in group), 2),
                "avg_utilize": round(avg(safe_float(r.get("utilize_score")) for r in group), 2),
            }
        )
    user_summaries.sort(key=lambda item: (item["avg_utilize"], item["avg_listening"], -item["words"]))

    weak_words = []
    for word, group in word_groups.items():
        if word and len(group) >= 2:
            weak_words.append(
                {
                    "word": word,
                    "learners": len(group),
                    "avg_listening": round(avg(safe_float(r.get("listening_score")) for r in group), 2),
                    "avg_utilize": round(avg(safe_float(r.get("utilize_score")) for r in group), 2),
                }
            )
    weak_words.sort(key=lambda item: (item["avg_utilize"], item["avg_listening"], -item["learners"], item["word"]))

    return {
        "total_rows": len(rows),
        "user_count": len(user_groups),
        "word_count": len(word_groups),
        "book_names": sorted({row.get("book_name", "") for row in rows if row.get("book_name")}),
        "avg_basic": round(avg(safe_float(r.get("basic")) for r in rows), 2),
        "avg_listening": round(avg(safe_float(r.get("listening_score")) for r in rows), 2),
        "avg_utilize": round(avg(safe_float(r.get("utilize_score")) for r in rows), 2),
        "avg_pronunciation": round(avg(safe_float(r.get("pronunciation_score")) for r in rows), 2),
        "avg_semantics": round(avg(safe_float(r.get("semantics_score")) for r in rows), 2),
        "avg_writing": round(avg(safe_float(r.get("writing_score")) for r in rows), 2),
        "weak_words": weak_words[:10],
        "bottom_users": user_summaries[:5],
    }


def infer_target_grade(cohort: dict[str, object] | None) -> tuple[str | None, str | None]:
    if not cohort:
        return None, None
    for book_name in cohort["book_names"]:  # type: ignore[index]
        match = re.search(r"([一二三四五六])年级", book_name)
        if match:
            grade_cn = f"{match.group(1)}年级"
            return grade_cn, GRADE_CODE_MAP.get(grade_cn)
    return None, None


def analyze_listening_catalog(rows: list[dict[str, str]], target_grade_cn: str | None) -> dict[str, object]:
    grade_rows = [row for row in rows if not target_grade_cn or row.get("年级") == target_grade_cn]
    levels = Counter(str(row.get("级别", "")).strip() for row in grade_rows if str(row.get("级别", "")).strip())
    units = []
    seen = set()
    for row in grade_rows:
        unit = str(row.get("单元名称", "")).strip()
        if unit and unit not in seen:
            seen.add(unit)
            units.append(unit)
    return {
        "total_rows": len(rows),
        "grade_rows": len(grade_rows),
        "top_levels": top_n(levels, 5),
        "sample_units": units[:6],
    }


def analyze_word_catalog(rows: list[dict[str, str]], target_grade_cn: str | None) -> dict[str, object]:
    grade_rows = [row for row in rows if not target_grade_cn or row.get("年级") == target_grade_cn]
    units = Counter(str(row.get("单元名称", "")).strip() for row in grade_rows if str(row.get("单元名称", "")).strip())
    words = [str(row.get("单词", "")).strip() for row in grade_rows if str(row.get("单词", "")).strip()]
    return {
        "total_rows": len(rows),
        "grade_rows": len(grade_rows),
        "unit_count": len(units),
        "sample_words": words[:12],
        "top_units": top_n(units, 5),
    }


def analyze_picturebook_catalog(
    rows: list[dict[str, str]],
    target_grade_code: str | None,
    target_words: list[str],
) -> dict[str, object]:
    grade_rows = []
    for row in rows:
        grades = str(row.get("年级", "")).split(",")
        if not target_grade_code or target_grade_code in grades:
            grade_rows.append(row)

    scored_books = []
    target_word_set = {word.lower() for word in target_words if word}
    for row in grade_rows:
        words = [item.strip().lower() for item in str(row.get("单词", "")).split(",") if item.strip()]
        overlap = sorted(target_word_set.intersection(words))
        scored_books.append(
            {
                "title": str(row.get("英文名称") or row.get("中文名称") or row.get("id")).strip(),
                "duration": safe_float(str(row.get("阅读时长", "0"))),
                "overlap": overlap,
                "themes": str(row.get("主题", "")).strip(),
            }
        )
    scored_books.sort(key=lambda item: (-len(item["overlap"]), item["duration"], item["title"]))
    return {
        "total_rows": len(rows),
        "grade_rows": len(grade_rows),
        "candidate_books": [book for book in scored_books if book["title"]][:5],
    }


def build_practice_pack(
    listening_rows: list[dict[str, str]] | None,
    word_rows: list[dict[str, str]] | None,
    picturebook_rows: list[dict[str, str]] | None,
    target_grade_cn: str | None,
    target_grade_code: str | None,
    target_words: list[str],
) -> dict[str, object]:
    target_terms = unique_keep_order(target_words)[:12]
    if not target_terms:
        return {}

    package: dict[str, object] = {
        "targets": target_terms,
        "listening": [],
        "words": [],
        "books": [],
    }

    if listening_rows:
        listening_candidates = []
        for row in listening_rows:
            if target_grade_cn and row.get("年级") != target_grade_cn:
                continue
            matches = score_overlap([row.get("单元名称"), row.get("题干集合")], target_terms)
            prompt = clean_prompt_sample(row.get("题干集合"))
            listening_candidates.append(
                {
                    "unit": str(row.get("单元名称", "")).strip(),
                    "level": str(row.get("级别", "")).strip(),
                    "linked_questions": safe_float(str(row.get("关联题目数量", ""))),
                    "configured_questions": safe_float(str(row.get("设置的题目数量", ""))),
                    "matches": matches,
                    "prompt": prompt[:90],
                    "score": len(matches) * 100
                    + safe_float(str(row.get("关联题目数量", "")))
                    + safe_float(str(row.get("设置的题目数量", ""))),
                }
            )
        listening_candidates.sort(
            key=lambda item: (-item["score"], item["level"], item["unit"])  # type: ignore[index]
        )
        matched_listening = [item for item in listening_candidates if item["matches"]]
        package["listening"] = (matched_listening or listening_candidates)[:3]

    if word_rows:
        word_candidates = []
        for row in word_rows:
            if target_grade_cn and row.get("年级") != target_grade_cn:
                continue
            resource_terms = split_resource_words(row.get("单词")) + split_resource_words(row.get("单词名称"))
            normalized_resource_terms = {normalize_term(term) for term in resource_terms}
            exact_matches = [term for term in target_terms if normalize_term(term) in normalized_resource_terms]
            if not exact_matches:
                continue
            matches = unique_keep_order(exact_matches)
            word_candidates.append(
                {
                    "word": str(row.get("单词") or row.get("单词名称") or "").strip(),
                    "meaning": str(row.get("释义", "")).strip(),
                    "unit": str(row.get("单元名称", "")).strip(),
                    "sentence": strip_html(row.get("例句")),
                    "has_audio": bool(str(row.get("音频", "")).strip()),
                    "matches": matches,
                    "score": len(exact_matches) * 100 + (1 if row.get("音频") else 0),
                }
            )
        word_candidates.sort(key=lambda item: (-item["score"], item["word"]))  # type: ignore[index]
        selected_words = []
        used_words = set()
        for item in word_candidates:
            word_key = normalize_term(item["word"])
            if not word_key or word_key in used_words:
                continue
            used_words.add(word_key)
            selected_words.append(item)
            if len(selected_words) >= 8:
                break
        package["words"] = selected_words

    if picturebook_rows:
        book_candidates = []
        target_term_set = {normalize_term(term) for term in target_terms}
        for row in picturebook_rows:
            grades = str(row.get("年级", "")).split(",")
            if target_grade_code and target_grade_code not in grades:
                continue
            resource_words = split_resource_words(row.get("单词"))
            resource_word_set = {normalize_term(word) for word in resource_words}
            exact_matches = [term for term in target_terms if normalize_term(term) in resource_word_set]
            fuzzy_matches = score_overlap(
                [row.get("英文名称"), row.get("中文名称"), row.get("主题"), row.get("简介"), row.get("单词")],
                target_terms,
            )
            matches = unique_keep_order(exact_matches + fuzzy_matches)
            if not matches:
                continue
            title = str(row.get("英文名称") or row.get("中文名称") or row.get("id") or "").strip()
            book_candidates.append(
                {
                    "title": title,
                    "cn_title": str(row.get("中文名称", "")).strip(),
                    "themes": str(row.get("主题", "")).strip(),
                    "vocab_size": safe_float(str(row.get("词汇量", "0"))),
                    "duration": safe_float(str(row.get("阅读时长", "0"))),
                    "matches": matches,
                    "score": len(set(normalize_term(match) for match in matches).intersection(target_term_set)) * 100
                    - safe_float(str(row.get("词汇量", "0"))) / 100,
                }
            )
        book_candidates.sort(key=lambda item: (-item["score"], item["duration"], item["title"]))  # type: ignore[index]
        package["books"] = book_candidates[:5]

    return package


def contains_any(text: str, terms: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def build_memory_suggestions(memory_text: str, oral: dict[str, object] | None, cohort: dict[str, object] | None) -> list[str]:
    suggestions: list[str] = []
    if oral and cohort and not contains_any(memory_text, ["individual", "cohort", "个体", "群体"]):
        suggestions.append("Add a data-boundary note separating individual oral evidence from cohort textbook evidence.")

    if oral:
        date_scores = oral["date_scores"]  # type: ignore[index]
        if len(date_scores) >= 2:
            first = date_scores[0]["avg_overall"]  # type: ignore[index]
            last = date_scores[-1]["avg_overall"]  # type: ignore[index]
            if first - last >= 8:
                suggestions.append("Keep a durable teaching note that accuracy drops when the learner moves from short items to longer sentence-level tasks.")
        weak_phones = [item[0] for item in oral["weak_phones"][:4]]  # type: ignore[index]
        if weak_phones:
            suggestions.append(f"Prioritize a stable correction path built around high-frequency weak phones: {', '.join(weak_phones)}.")

    if cohort:
        if cohort["avg_utilize"] <= 10:  # type: ignore[index]
            suggestions.append("Keep the cohort strategy focused on moving from listening exposure to usable output, not on adding more explanation alone.")
        if cohort["avg_pronunciation"] <= 25:  # type: ignore[index]
            suggestions.append("Retain pronunciation-first, frame-based drills as the default cohort teaching move.")
    return suggestions


def build_user_suggestions(user_text: str, oral: dict[str, object] | None) -> list[str]:
    suggestions: list[str] = []
    if not oral:
        return suggestions

    if oral["unique_contents"] >= 20 and oral["primary_count"] >= 100:  # type: ignore[index]
        suggestions.append("Preserve the portrait that this learner is willing to practice repeatedly and can sustain high-frequency oral work.")

    weak_words = [item[0] for item in oral["weak_words"][:5]]  # type: ignore[index]
    if weak_words:
        suggestions.append(f"Highlight current weak lexical targets: {', '.join(weak_words)}.")

    weak_phones = [item[0] for item in oral["weak_phones"][:5]]  # type: ignore[index]
    if weak_phones:
        suggestions.append(f"Keep the individual correction focus narrow: {', '.join(weak_phones)}.")

    strong_words = [item[0] for item in oral["strong_words"][:5]]  # type: ignore[index]
    if strong_words and not contains_any(user_text, strong_words):
        suggestions.append(f"Use stable success items as warm-up anchors: {', '.join(strong_words)}.")

    return suggestions


def build_micro_loop(oral: dict[str, object] | None, cohort: dict[str, object] | None) -> list[str]:
    target = "Stabilize one oral output pattern with a single correction focus."
    correction_points: list[str] = []
    transfer = "Use one short sentence frame and finish with a measurable exit check."

    if oral:
        weak_phone_names = [item[0] for item in oral["weak_phones"][:2]]  # type: ignore[index]
        weak_word_names = [item[0] for item in oral["weak_words"][:3]]  # type: ignore[index]
        if weak_phone_names:
            correction_points.append(f"Phone focus: {', '.join(weak_phone_names)}")
        if weak_word_names:
            correction_points.append(f"Word focus: {', '.join(weak_word_names)}")
        weak_contents = oral["weak_contents"]  # type: ignore[index]
        if weak_contents:
            transfer = f"Transfer back into the weak sentence pattern: {weak_contents[0][0]}"
    elif cohort:
        weak_words = [item["word"] for item in cohort["weak_words"][:3]]  # type: ignore[index]
        if weak_words:
            correction_points.append(f"Word focus: {', '.join(weak_words)}")

    if not correction_points:
        correction_points.append("One correction only: choose a single phoneme, word set, or sentence frame.")

    return [
        f"Goal: {target}",
        "Warm-up: start with one familiar high-success item.",
        f"Correction: {'; '.join(correction_points)}.",
        f"Transfer: {transfer}",
        "Exit check: require one clean word run and one clean sentence-level repetition.",
    ]


def render_brief(
    workspace: Path,
    memory_text: str,
    user_text: str,
    supported: list[LoadedCsv],
    unsupported: list[LoadedCsv],
) -> str:
    oral_file = next((item for item in supported if item.kind == "oral_eval"), None)
    textbook_file = next((item for item in supported if item.kind == "textbook_vocab"), None)
    listening_file = next((item for item in supported if item.kind == "listening_catalog"), None)
    word_file = next((item for item in supported if item.kind == "word_catalog"), None)
    picturebook_file = next((item for item in supported if item.kind == "picturebook_catalog"), None)

    oral = analyze_oral_eval(oral_file.rows) if oral_file else None
    cohort = analyze_textbook_vocab(textbook_file.rows) if textbook_file else None
    target_grade_cn, target_grade_code = infer_target_grade(cohort)
    target_words = []
    if oral:
        target_words.extend(item[0] for item in oral["weak_words"][:5])  # type: ignore[index]
    if cohort:
        target_words.extend(item["word"] for item in cohort["weak_words"][:8])  # type: ignore[index]
    listening_catalog = analyze_listening_catalog(listening_file.rows, target_grade_cn) if listening_file else None
    word_catalog = analyze_word_catalog(word_file.rows, target_grade_cn) if word_file else None
    picturebook_catalog = (
        analyze_picturebook_catalog(picturebook_file.rows, target_grade_code, target_words) if picturebook_file else None
    )
    practice_pack = build_practice_pack(
        listening_file.rows if listening_file else None,
        word_file.rows if word_file else None,
        picturebook_file.rows if picturebook_file else None,
        target_grade_cn,
        target_grade_code,
        target_words,
    )

    lines: list[str] = []
    lines.append("# Evolution Brief")
    lines.append("")
    lines.append("## Scope")
    lines.append(f"- Workspace: `{workspace}`")
    lines.append(f"- MEMORY loaded: {'yes' if memory_text.strip() else 'no'}")
    lines.append(f"- USER loaded: {'yes' if user_text.strip() else 'no'}")
    for item in supported:
        lines.append(f"- Supported evidence: `{item.path.name}` as `{item.kind}`")
    for item in unsupported:
        lines.append(f"- Skipped evidence: `{item.path.name}` (unsupported schema or resource-style export)")
    lines.append("")

    if oral:
        lines.append("## Individual Oral Evidence")
        lines.append(
            f"- Direct evidence: primary learner `{oral['primary_user']}` has {oral['primary_count']} oral records "
            f"from {oral['date_min']} to {oral['date_max']} across {oral['unique_contents']} contents and {oral['unique_words']} words."
        )
        lines.append(
            f"- Direct evidence: average overall `{oral['avg_overall']}`, word score `{oral['avg_word_score']}`, phone score `{oral['avg_phone_score']}`."
        )
        date_parts = [f"{item['date']}={item['avg_overall']}" for item in oral["date_scores"]]  # type: ignore[index]
        lines.append(f"- Direct evidence: daily overall trend {' -> '.join(date_parts)}.")
        weak_phones = ", ".join(f"{phone}({score})" for phone, _, score in oral["weak_phones"])  # type: ignore[index]
        strong_words = ", ".join(f"{word}({score})" for word, _, score in oral["strong_words"][:5])  # type: ignore[index]
        weak_words = ", ".join(f"{word}({score})" for word, _, score in oral["weak_words"])  # type: ignore[index]
        lines.append(f"- Inference: weak phones concentrate around {weak_phones}.")
        lines.append(f"- Inference: strong warm-up words include {strong_words}.")
        lines.append(f"- Inference: weak lexical targets include {weak_words}.")
        lines.append("")

    if cohort:
        lines.append("## Cohort Textbook Evidence")
        lines.append(
            f"- Cohort pattern: {cohort['user_count']} learners, {cohort['word_count']} words, "
            f"book={', '.join(cohort['book_names'])}."
        )
        lines.append(
            f"- Cohort pattern: avg basic `{cohort['avg_basic']}`, listening `{cohort['avg_listening']}`, "
            f"utilize `{cohort['avg_utilize']}`, pronunciation `{cohort['avg_pronunciation']}`, "
            f"semantics `{cohort['avg_semantics']}`, writing `{cohort['avg_writing']}`."
        )
        weak_words = ", ".join(
            f"{item['word']}({item['avg_listening']}/{item['avg_utilize']})" for item in cohort["weak_words"][:8]  # type: ignore[index]
        )
        lines.append(f"- Inference: cohort weak-transfer words include {weak_words}.")
        lines.append("")

    if listening_catalog or word_catalog or picturebook_catalog:
        lines.append("## Resource Signals")
        if listening_catalog:
            level_text = ", ".join(f"{name}({count})" for name, count in listening_catalog["top_levels"]) or "none"
            unit_text = ", ".join(listening_catalog["sample_units"]) or "none"
            lines.append(
                f"- Resource catalog: listening bank has {listening_catalog['total_rows']} rows; "
                f"{listening_catalog['grade_rows']} match target grade `{target_grade_cn or 'unknown'}`."
            )
            lines.append(f"- Resource support: top listening levels {level_text}; sample units {unit_text}.")
        if word_catalog:
            unit_text = ", ".join(f"{name}({count})" for name, count in word_catalog["top_units"]) or "none"
            sample_words = ", ".join(word_catalog["sample_words"][:8]) or "none"
            lines.append(
                f"- Resource catalog: quick-word bank has {word_catalog['total_rows']} rows; "
                f"{word_catalog['grade_rows']} match target grade `{target_grade_cn or 'unknown'}` across "
                f"{word_catalog['unit_count']} units."
            )
            lines.append(f"- Resource support: sample words {sample_words}; active units {unit_text}.")
        if picturebook_catalog:
            lines.append(
                f"- Resource catalog: picture-book bank has {picturebook_catalog['total_rows']} rows; "
                f"{picturebook_catalog['grade_rows']} match target grade code `{target_grade_code or 'unknown'}`."
            )
            candidate_bits = []
            for book in picturebook_catalog["candidate_books"]:
                overlap = ",".join(book["overlap"]) if book["overlap"] else "no direct overlap"
                candidate_bits.append(f"{book['title']}[{overlap}]")
            lines.append(
                f"- Resource support: candidate books for transfer or warm-up {', '.join(candidate_bits) or 'none'}."
            )
        lines.append("")

    if practice_pack:
        lines.append("## Recommended Practice Pack")
        targets = practice_pack["targets"]  # type: ignore[index]
        lines.append(
            f"- Target bridge: prioritize weak words with available resources: {', '.join(targets[:10])}."
        )
        lines.append("- Use order: listening recognition -> quick-word recall -> picture-book transfer.")

        listening_items = practice_pack["listening"]  # type: ignore[index]
        if listening_items:
            lines.append("- Listening picks:")
            for item in listening_items:  # type: ignore[assignment]
                matches = ", ".join(item["matches"]) if item["matches"] else "grade-fit fallback"
                prompt = f"; prompt sample: {item['prompt']}" if item["prompt"] else ""
                lines.append(
                    f"  - {item['unit']} / {item['level']} "
                    f"({compact_number(item['configured_questions'])} configured, "
                    f"{compact_number(item['linked_questions'])} linked; match: {matches}{prompt})"
                )
        else:
            lines.append("- Listening picks: no matching grade resource found.")

        word_items = practice_pack["words"]  # type: ignore[index]
        if word_items:
            lines.append("- Quick-word picks:")
            for item in word_items:  # type: ignore[assignment]
                audio = "audio" if item["has_audio"] else "no audio"
                meaning = f" - {item['meaning']}" if item["meaning"] else ""
                sentence = f"; example: {item['sentence']}" if item["sentence"] else ""
                matches = ", ".join(item["matches"])
                lines.append(
                    f"  - {item['word']} ({item['unit']}, {audio}, match: {matches}){meaning}{sentence}"
                )
        else:
            lines.append("- Quick-word picks: no matching grade word resource found.")

        book_items = practice_pack["books"]  # type: ignore[index]
        if book_items:
            lines.append("- Picture-book picks:")
            for item in book_items:  # type: ignore[assignment]
                matches = ", ".join(item["matches"])
                themes = f"; theme: {item['themes']}" if item["themes"] else ""
                lines.append(
                    f"  - {item['title']} "
                    f"(vocab {compact_number(item['vocab_size'])}, "
                    f"duration {compact_number(item['duration'])}, match: {matches}{themes})"
                )
        else:
            lines.append("- Picture-book picks: no matching grade book resource found.")
        lines.append("")

    lines.append("## Suggested MEMORY Delta")
    memory_suggestions = build_memory_suggestions(memory_text, oral, cohort)
    if memory_suggestions:
        for item in memory_suggestions:
            lines.append(f"- {item}")
    else:
        lines.append("- No durable MEMORY update is strongly justified from the supported evidence alone.")
    lines.append("")

    lines.append("## Suggested USER Delta")
    user_suggestions = build_user_suggestions(user_text, oral)
    if user_suggestions:
        for item in user_suggestions:
            lines.append(f"- {item}")
    else:
        lines.append("- No individual USER update is strongly justified from the supported evidence alone.")
    lines.append("")

    lines.append("## Next Micro-Loop")
    for item in build_micro_loop(oral, cohort):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Persistence Decision")
    lines.append(f"- MEMORY.md: {'update suggested' if memory_suggestions else 'hold'}")
    lines.append(f"- USER.md: {'update suggested' if user_suggestions else 'hold'}")
    lines.append("- Resource catalogs: use for drill selection and support matching, not as direct learner evidence.")
    lines.append("- Unsupported files: review manually before promoting any conclusion from them.")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    memory_path = Path(args.memory).resolve() if args.memory else workspace / "MEMORY.md"
    user_path = Path(args.user).resolve() if args.user else workspace / "USER.md"
    data_dir = Path(args.data_dir).resolve() if args.data_dir else workspace / "data"

    memory_text = read_text(memory_path) if memory_path.exists() else ""
    user_text = read_text(user_path) if user_path.exists() else ""

    supported: list[LoadedCsv] = []
    unsupported: list[LoadedCsv] = []
    if data_dir.exists():
        for path in sorted(data_dir.glob("*.csv")):
            loaded = load_csv(path)
            if loaded is None:
                continue
            if loaded.kind == "unsupported":
                unsupported.append(loaded)
            else:
                supported.append(loaded)

    brief = render_brief(workspace, memory_text, user_text, supported, unsupported)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(brief, encoding="utf-8")
    print(brief)


if __name__ == "__main__":
    main()
