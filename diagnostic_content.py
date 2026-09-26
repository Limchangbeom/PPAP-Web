from __future__ import annotations

import json
import math
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from data.questions import (
    PAGE_SIZE,
    QUESTIONS,
    QUESTION_INDEX,
    REGULATION_META,
    STATUS_LABELS,
    STATUS_ORDER,
    STATUS_SCORES,
    question_visible,
)
from data.guidance import LEGAL_BASIS_GUIDANCE, TERM_GUIDANCE


STATUS_SUMMARIES = {
    "violation": "선택한 응답이 원문 기준상 위반 또는 고위험 부적합으로 해석됩니다.",
    "insufficient": "선택한 응답이 원문 기준상 보완 필요 또는 일부 미비로 해석됩니다.",
    "compliant": "선택한 응답이 원문 기준상 충족 또는 적합으로 해석됩니다.",
    "recommended": "선택한 응답이 원문 기준상 해당 없음, 적용 제외, 또는 추가 확인 권장 상태로 해석됩니다.",
}

STATUS_ACTIONS = {
    "violation": "관련 문서와 실제 처리 흐름을 즉시 수정하고 필요 시 해당 처리를 중단하거나 재검토하세요.",
    "insufficient": "누락된 요건을 보완하고 문서, 설정, 내부 절차를 업데이트하세요.",
    "compliant": "현재 근거와 절차를 유지하되 실제 운영과 문서의 일치 여부를 정기적으로 확인하세요.",
    "recommended": "적용 범위와 실제 운영 여부를 다시 점검하고 필요 시 관련 통제를 추가하세요.",
}


def build_question_page_map(questions: list[dict]) -> dict[str, int]:
    return {
        question["id"]: math.ceil(index / PAGE_SIZE)
        for index, question in enumerate(questions, start=1)
    }


def get_questions_for_regulations(
    selected_regulations: list[str],
    responses: dict | None = None,
    include_hidden: bool = False,
) -> list[dict]:
    selected = set(selected_regulations)
    response_map = responses or {}
    matched_questions = []
    effective_responses = {}
    for question in QUESTIONS:
        if question["regulation"] not in selected:
            continue
        if include_hidden:
            matched_questions.append(question)
            continue
        if question_visible(question, effective_responses):
            matched_questions.append(question)
            if question["id"] in response_map:
                effective_responses[question["id"]] = response_map[question["id"]]
    return matched_questions


def validate_page_questions(page_questions: list[dict], responses: dict) -> list[str]:
    return [
        question["id"]
        for question in page_questions
        if not (responses.get(question["id"]) not in (None, ""))
    ]


def answer_is_present(answer: str | list[str] | None) -> bool:
    if answer is None:
        return False
    if isinstance(answer, list):
        return len(answer) > 0
    return answer != ""


def get_visible_question_ids(questions: list[dict], responses: dict) -> set[str]:
    effective_responses = {}
    visible_ids = set()
    for question in questions:
        if question.get("visible_if") and not question_visible(
            question, effective_responses
        ):
            continue
        visible_ids.add(question["id"])
        answer = responses.get(question["id"])
        if answer_is_present(answer):
            effective_responses[question["id"]] = answer
    return visible_ids


def get_page_questions(
    all_questions: list[dict], responses: dict, requested_page: int
) -> tuple[list[dict], list[dict], set[str], int, int]:
    page_questions, current_page, total_pages = paginate_questions(
        all_questions, requested_page
    )
    visible_ids = get_visible_question_ids(all_questions, responses)
    visible_page_questions = [
        question for question in page_questions if question["id"] in visible_ids
    ]
    return (
        page_questions,
        visible_page_questions,
        visible_ids,
        current_page,
        total_pages,
    )


def get_effective_page_size(total_items: int) -> int:
    if total_items <= PAGE_SIZE:
        return PAGE_SIZE
    remainder = total_items % PAGE_SIZE
    if 1 <= remainder <= 2:
        return PAGE_SIZE + remainder
    return PAGE_SIZE


def paginate_questions(questions: list[dict], page: int) -> tuple[list[dict], int, int]:
    effective_size = get_effective_page_size(len(questions))
    total_pages = max(1, math.ceil(len(questions) / effective_size))
    current_page = max(1, min(page, total_pages))
    start_index = (current_page - 1) * effective_size
    end_index = start_index + effective_size
    return questions[start_index:end_index], current_page, total_pages


def find_page_with_visible_questions(
    all_questions: list[dict], responses: dict, start_page: int, direction: int
) -> int | None:
    effective_size = get_effective_page_size(len(all_questions))
    total_pages = max(1, math.ceil(len(all_questions) / effective_size))
    visible_ids = get_visible_question_ids(all_questions, responses)
    page_range = (
        range(max(1, start_page), total_pages + 1)
        if direction >= 0
        else range(min(total_pages, start_page), 0, -1)
    )
    for page in page_range:
        page_questions, _current_page, _total_pages = paginate_questions(
            all_questions, page
        )
        if any(question["id"] in visible_ids for question in page_questions):
            return page
    return None


def first_incomplete_page(state: dict) -> int | None:
    questions = get_selected_questions(state)
    responses = state.get("responses", {})
    visible_ids = get_visible_question_ids(questions, responses)
    page_map = build_question_page_map(questions)
    for question in questions:
        if question["id"] not in visible_ids:
            continue
        if not answer_is_present(responses.get(question["id"])):
            return page_map[question["id"]]
    return None


def get_selected_questions(state: dict) -> list[dict]:
    return get_questions_for_regulations(
        state.get("selected_regulations", []), include_hidden=True
    )


def get_answer_values(answer: str | list[str] | None) -> set[str]:
    if answer is None:
        return set()
    if isinstance(answer, list):
        return set(answer)
    return {answer}


def has_non_none_answer(question_id: str, responses: dict) -> bool:
    question = QUESTION_INDEX.get(question_id)
    answer = responses.get(question_id)
    if not question or not answer_is_present(answer):
        return False
    none_value = question.get("evaluation", {}).get("none_value")
    values = get_answer_values(answer)
    return any(value != none_value for value in values)


def append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def build_inline_guidance(question: dict) -> tuple[list[str], list[str]]:
    guidance = []
    legal_basis = question.get("legal_basis", "")
    for aliases, text in LEGAL_BASIS_GUIDANCE:
        if any(alias in legal_basis for alias in aliases):
            append_unique(guidance, text)

    if not guidance:
        append_unique(guidance, question["description"].replace("판단 포인트: ", ""))

    combined = " ".join(
        [
            question.get("title", ""),
            question.get("question", ""),
            question.get("description", ""),
            question.get("legal_basis", ""),
        ]
    ).lower()
    terms = []
    for aliases, text in TERM_GUIDANCE:
        if any(alias.lower() in combined for alias in aliases):
            append_unique(terms, text)

    if question["id"] == "gdpr_scope_detail_person":
        guidance.insert(
            0,
            "여기서 자연인은 살아 있는 인간 개인을 뜻하며, 법인·단체·기관 정보는 그 자체만으로는 이 질문의 대상이 아닙니다.",
        )
        append_unique(
            terms,
            "일상적으로 말하는 '개인'보다 GDPR의 '자연인'이 더 정확한 기준이며, 살아 있는 사람과 연결되는지 여부가 핵심입니다.",
        )

    return guidance[:2], terms[:2]


def find_consistency_issues(state: dict) -> list[dict]:
    questions = get_active_questions(state)
    visible_ids = {question["id"] for question in questions}
    responses = state.get("responses", {})
    issues = []

    def add_issue(question_ids: list[str], message: str) -> None:
        relevant_ids = [
            question_id for question_id in question_ids if question_id in visible_ids
        ]
        if relevant_ids:
            issues.append({"question_ids": relevant_ids, "message": message})

    gdpr_detail_ids = [
        "gdpr_scope_detail_identifier",
        "gdpr_scope_detail_activity",
        "gdpr_scope_detail_location",
        "gdpr_scope_detail_commercial",
        "gdpr_scope_detail_inference",
        "gdpr_scope_detail_sensitive",
    ]
    if responses.get("gdpr_scope_detail_person") == "no":
        conflicting = [
            question_id
            for question_id in gdpr_detail_ids
            if has_non_none_answer(question_id, responses)
        ]
        if conflicting:
            add_issue(
                ["gdpr_scope_detail_person", *conflicting],
                "'살아있는 자연인에 대한 정보가 아니다'를 선택했는데, 아래 GDPR 개인정보 유형 문항에서는 개인정보 범주가 선택되어 있습니다.",
            )

    anonymous_values = get_answer_values(responses.get("gdpr_scope_detail_anonymous"))
    if (
        anonymous_values
        and anonymous_values != {"na"}
        and responses.get("gdpr_scope_detail_pseudonym") == "yes"
    ):
        add_issue(
            ["gdpr_scope_detail_anonymous", "gdpr_scope_detail_pseudonym"],
            "완전 익명정보라고 선택했지만, 뒤 문항에서는 재식별 가능한 가명정보라고 답했습니다. 두 응답을 다시 확인하세요.",
        )

    ccpa_detail_ids = [
        "ccpa_scope_identifiers",
        "ccpa_scope_activity",
        "ccpa_scope_location",
        "ccpa_scope_service_use",
        "ccpa_scope_inferences",
        "ccpa_scope_sensitive",
    ]
    if responses.get("ccpa_consumer_scope") == "no":
        conflicting = [
            question_id
            for question_id in ccpa_detail_ids
            if has_non_none_answer(question_id, responses)
        ]
        if conflicting:
            add_issue(
                ["ccpa_consumer_scope", *conflicting],
                "캘리포니아 소비자 또는 가구와 연결되지 않는다고 답했는데, 아래 CCPA 개인정보 카테고리 문항에서는 관련 범주가 선택되어 있습니다.",
            )

    exemption_values = get_answer_values(responses.get("ccpa_scope_exemptions"))
    if (
        exemption_values
        and exemption_values != {"none"}
        and responses.get("ccpa_scope_reidentification") == "yes"
    ):
        add_issue(
            ["ccpa_scope_exemptions", "ccpa_scope_reidentification"],
            "CCPA 예외 또는 비식별 상태를 선택했지만, 뒤 문항에서는 다시 재식별 가능하다고 답했습니다. 예외 주장 근거를 다시 확인하세요.",
        )

    return issues


def find_first_issue_page(questions: list[dict], issues: list[dict]) -> int | None:
    if not issues:
        return None
    page_map = build_question_page_map(questions)
    positions = [
        page_map[question_id]
        for issue in issues
        for question_id in issue["question_ids"]
        if question_id in page_map
    ]
    if not positions:
        return None
    return min(positions)


def evaluate_question(question: dict, answer: str | list[str]) -> dict[str, Any]:
    evaluation = question["evaluation"]
    answer_summary = format_answer(question, answer)

    if evaluation["kind"] == "single":
        status = evaluation["status_map"][answer]
    elif evaluation["kind"] == "multi_presence":
        normalized = (
            _sanitize_multi_answer(
                question, list(answer) if isinstance(answer, list) else []
            )
            or []
        )
        none_value = evaluation.get("none_value")
        if none_value and normalized == [none_value]:
            status = evaluation["none_status"]
        elif normalized:
            status = evaluation["any_status"]
        else:
            status = evaluation["none_status"]
        answer_summary = format_answer(question, normalized)
    elif evaluation["kind"] == "checklist":
        normalized = (
            _sanitize_multi_answer(
                question, list(answer) if isinstance(answer, list) else []
            )
            or []
        )
        selected = set(normalized)
        none_value = evaluation.get("none_value")
        required = set(evaluation.get("required_values", []))
        recommended = set(evaluation.get("recommended_values", []))
        one_of_groups = evaluation.get("one_of_groups", [])
        forbidden = set(evaluation.get("forbidden_values", []))

        if none_value and normalized == [none_value]:
            status = evaluation["none_status"]
        elif selected & forbidden:
            status = "violation"
        else:
            required_hits = len(selected & required)
            all_required = required.issubset(selected)
            groups_satisfied = all(
                any(option in selected for option in group) for group in one_of_groups
            )
            all_recommended = recommended.issubset(selected) if recommended else True
            if all_required and groups_satisfied and all_recommended:
                status = "compliant"
            elif all_required and groups_satisfied:
                status = "recommended"
            elif required_hits > 0 or selected:
                status = "insufficient"
            else:
                status = "violation"
        answer_summary = format_answer(question, normalized)
    else:
        normalized = (
            _sanitize_multi_answer(
                question, list(answer) if isinstance(answer, list) else []
            )
            or []
        )
        selected = set(normalized)
        none_value = evaluation.get("none_value")
        required = set(evaluation.get("required_values", []))
        at_least_one = set(evaluation.get("at_least_one_values", []))

        if none_value and normalized == [none_value]:
            status = evaluation["none_status"]
        elif required.issubset(selected) and selected & at_least_one:
            status = "compliant"
        elif selected & at_least_one or selected & required:
            status = "insufficient"
        else:
            status = "violation"
        answer_summary = format_answer(question, normalized)

    return {
        "status": status,
        "status_label": STATUS_LABELS[status],
        "summary": STATUS_SUMMARIES[status],
        "issue": question["description"],
        "reason": STATUS_SUMMARIES[status],
        "action": question.get("action_hint") or STATUS_ACTIONS[status],
        "answer_summary": answer_summary,
    }


def _sanitize_multi_answer(question: dict, raw_values: list[str]) -> list[str] | None:
    valid_values = {choice["value"] for choice in question["choices"]}
    values = [value for value in raw_values if value in valid_values]
    evaluation = question.get("evaluation", {})

    exclusive_values = evaluation.get("exclusive_values") or []
    chosen_exclusive = [value for value in exclusive_values if value in values]
    if chosen_exclusive:
        values = chosen_exclusive

    for group in evaluation.get("one_of_groups") or []:
        chosen_in_group = [option for option in group if option in values]
        if len(chosen_in_group) > 1:
            keep = chosen_in_group[0]
            values = [
                value for value in values if value not in group or value == keep
            ]

    none_value = evaluation.get("none_value")
    if none_value and none_value in values and len(values) > 1:
        values = [value for value in values if value != none_value]
    return list(dict.fromkeys(values)) or None


def sanitize_multi_answer(question: dict, raw_values: list[str]) -> list[str] | None:
    return _sanitize_multi_answer(question, raw_values)


def extract_answer(question: dict, form_data) -> str | list[str] | None:
    if question["type"] == "multi":
        return sanitize_multi_answer(question, form_data.getlist(question["id"]))
    value = form_data.get(question["id"], "").strip()
    return value or None


def update_responses_for_questions(
    responses: dict, questions: list[dict], form_data
) -> dict:
    updated = dict(responses)
    for question in questions:
        updated.pop(question["id"], None)
        answer = extract_answer(question, form_data)
        if answer_is_present(answer):
            updated[question["id"]] = answer
    return updated


def format_answer(question: dict, answer: str | list[str]) -> str:
    label_map = {choice["value"]: choice["label"] for choice in question["choices"]}
    if isinstance(answer, list):
        return ", ".join(label_map.get(value, value) for value in answer)
    return label_map.get(answer, answer)


def get_active_questions(state: dict) -> list[dict]:
    selected = state.get("selected_regulations", [])
    responses = state.get("responses", {})
    return get_questions_for_regulations(selected, responses)


def prune_hidden_responses(state: dict) -> dict:
    visible_ids = {
        question["id"]
        for question in get_questions_for_regulations(
            state.get("selected_regulations", []), state.get("responses", {})
        )
    }
    state["responses"] = {
        question_id: answer
        for question_id, answer in state.get("responses", {}).items()
        if question_id in visible_ids
    }
    return state


def build_results_context(state: dict) -> dict[str, Any]:
    state = prune_hidden_responses(state)
    questions = get_active_questions(state)
    selected_regulations = state.get("selected_regulations", [])
    responses = state.get("responses", {})
    evaluated_items = []
    unanswered_items = []

    for index, question in enumerate(questions, start=1):
        answer = responses.get(question["id"])
        if not answer_is_present(answer):
            unanswered_items.append(
                {
                    "number": index,
                    "regulation": question["regulation"],
                    "section": question["section"],
                    "title": question["title"],
                    "question": question["question"],
                }
            )
            continue

        evaluated = evaluate_question(question, answer)
        evaluated_items.append(
            {
                "id": question["id"],
                "number": index,
                "regulation": question["regulation"],
                "section": question["section"],
                "title": question["title"],
                "question": question["question"],
                "description": question["description"],
                "legal_basis": question["legal_basis"],
                **evaluated,
            }
        )

    counts = _summarize_counts(evaluated_items)
    priority_findings = sorted(
        [
            item
            for item in evaluated_items
            if item["status"] in {"violation", "insufficient"}
        ],
        key=lambda item: (STATUS_ORDER.index(item["status"]), item["number"]),
    )

    completion_count = len(evaluated_items)
    total_questions = len(questions)
    completion_rate = (
        round((completion_count / total_questions) * 100) if total_questions else 0
    )

    return {
        "selected_regulations": selected_regulations,
        "selected_regulation_labels": _regulation_display_labels(
            selected_regulations
        ),
        "selected_regulation_text": _regulation_display_text(
            selected_regulations
        ),
        "questions": questions,
        "results": evaluated_items,
        "unanswered_items": unanswered_items,
        "priority_findings": priority_findings,
        "total_questions": total_questions,
        "completion_count": completion_count,
        "completion_rate": completion_rate,
        "unanswered_count": len(unanswered_items),
        "counts": counts,
        "score": _score_from_items(evaluated_items),
        "generated_at": datetime.now().strftime("%Y.%m.%d %H:%M"),
        "status_cards": _build_status_cards(counts),
        "regulation_groups": _build_regulation_groups(
            selected_regulations, evaluated_items
        ),
    }


def _regulation_display_labels(
    selected_regulations: list[str],
) -> list[str]:
    return [regulation for regulation in selected_regulations]


def _regulation_display_text(selected_regulations: list[str]) -> str:
    return ", ".join(_regulation_display_labels(selected_regulations))


def _summarize_counts(items: list[dict]) -> dict[str, int]:
    counts = Counter(item["status"] for item in items)
    return {status: counts.get(status, 0) for status in STATUS_ORDER}


def _build_status_cards(counts: dict[str, int]) -> list[dict]:
    descriptions = {
        "violation": "조치가 필요한 항목",
        "insufficient": "추가 보완이 필요한 항목",
        "compliant": "기준을 충족한 항목",
        "recommended": "강화를 권장하는 항목",
    }
    return [
        {
            "key": status,
            "label": STATUS_LABELS[status],
            "count": counts.get(status, 0),
            "description": descriptions[status],
        }
        for status in STATUS_ORDER
    ]


def _score_from_items(items: list[dict]) -> int:
    if not items:
        return 0
    total = sum(STATUS_SCORES[item["status"]] for item in items)
    return round(total / len(items))


def _build_regulation_groups(
    selected_regulations: list[str], evaluated_items: list[dict]
) -> list[dict]:
    groups = []
    for regulation in selected_regulations:
        regulation_items = [
            item for item in evaluated_items if item["regulation"] == regulation
        ]
        counts = _summarize_counts(regulation_items)
        sections = {}
        for item in regulation_items:
            sections.setdefault(item["section"], []).append(item)
        groups.append(
            {
                "key": regulation,
                "title": REGULATION_META[regulation]["title"],
                "subtitle": REGULATION_META[regulation]["subtitle"],
                "score": _score_from_items(regulation_items),
                "counts": counts,
                "status_cards": _build_status_cards(counts),
                "sections": [
                    {"name": name, "items": items} for name, items in sections.items()
                ],
            }
        )
    return groups


def blank_state() -> dict:
    return {"selected_regulations": [], "responses": {}}


def regulation_display_labels(
    selected_regulations: list[str],
) -> list[str]:
    return [regulation for regulation in selected_regulations]


def regulation_display_text(selected_regulations: list[str]) -> str:
    return ", ".join(regulation_display_labels(selected_regulations))


def save_state(state: dict) -> None:
    from flask import g, session
    from datetime import datetime, timezone

    db = g.get("db")
    if db is None:
        import flask

        app = flask.current_app
        db = sqlite3.connect(app.config["DATABASE"])
        db.row_factory = sqlite3.Row
        g.db = db

    session_id = session.get("ppap_session_id")
    if not session_id:
        session_id = str(uuid4())
        session["ppap_session_id"] = session_id

    payload = json.dumps(state, ensure_ascii=False)
    updated_at = datetime.now(timezone.utc).isoformat()
    db.execute(
        """
        INSERT INTO survey_state (session_id, data, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(session_id)
        DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at
        """,
        (session_id, payload, updated_at),
    )
    db.commit()
