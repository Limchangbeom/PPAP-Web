from __future__ import annotations

import json
import math
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    abort,
)

import hashlib
import hmac
import secrets

from diagnostic_content import (
    STATUS_ACTIONS,
    STATUS_LABELS,
    STATUS_ORDER,
    STATUS_SCORES,
    STATUS_SUMMARIES,
    answer_is_present,
    blank_state,
    build_inline_guidance,
    build_results_context,
    evaluate_question,
    extract_answer,
    find_consistency_issues,
    find_first_issue_page,
    find_page_with_visible_questions,
    first_incomplete_page,
    get_active_questions,
    get_effective_page_size,
    get_page_questions,
    get_questions_for_regulations,
    get_selected_questions,
    prune_hidden_responses,
    regulation_display_labels,
    regulation_display_text,
    sanitize_multi_answer,
    save_state,
)
from data.law_updates import get_law_updates
from site_content import (
    BACKGROUND_CASES,
    BACKGROUND_STATS,
    EXPECTED_EFFECTS,
    PROJECT_FULL_NAME,
    PROJECT_NAME,
    PROJECT_OVERVIEW,
    USER_PROCESS_STEPS,
)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config["DATABASE"] = str(Path(__file__).parent / "instance" / "ppap.sqlite3")
app.instance_path = str(Path(__file__).parent / "instance")
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 3600
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

Path(app.instance_path).mkdir(parents=True, exist_ok=True)


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data:; font-src 'self' https://fonts.gstatic.com; connect-src 'self'"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


def generate_csrf_token() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf_token(token: str) -> bool:
    stored = session.get("csrf_token")
    if not stored or not token:
        return False
    return hmac.compare_digest(stored, token)


def blank_state() -> dict:
    return {"selected_regulations": [], "responses": {}}


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        connection = sqlite3.connect(app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


def init_db() -> None:
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS survey_state (
            session_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    db.commit()


@app.teardown_appcontext
def close_db(_exception: BaseException | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ensure_client_session_id() -> str:
    session_id = session.get("ppap_session_id")
    if not session_id:
        session_id = uuid4().hex
        session["ppap_session_id"] = session_id
    return session_id


def load_state() -> dict:
    init_db()
    session_id = ensure_client_session_id()
    row = (
        get_db()
        .execute(
            "SELECT data FROM survey_state WHERE session_id = ?",
            (session_id,),
        )
        .fetchone()
    )
    if not row:
        state = blank_state()
        save_state(state)
        return state
    state = json.loads(row["data"])
    state.setdefault("selected_regulations", [])
    state.setdefault("responses", {})
    return state


def save_state(state: dict) -> None:
    init_db()
    session_id = ensure_client_session_id()
    payload = json.dumps(state, ensure_ascii=False)
    updated_at = datetime.now(timezone.utc).isoformat()
    get_db().execute(
        """
        INSERT INTO survey_state (session_id, data, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(session_id)
        DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at
        """,
        (session_id, payload, updated_at),
    )
    get_db().commit()


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


def update_responses_for_page(
    responses: dict, page_questions: list[dict], form_data
) -> dict:
    updated = dict(responses)
    for question in page_questions:
        updated.pop(question["id"], None)
        answer = extract_answer(question, form_data)
        if answer_is_present(answer):
            updated[question["id"]] = answer
    return updated


def validate_page_questions(page_questions: list[dict], responses: dict) -> list[str]:
    return [
        question["id"]
        for question in page_questions
        if not answer_is_present(responses.get(question["id"]))
    ]


def extract_answer(question: dict, form_data) -> str | list[str] | None:
    if question["type"] == "multi":
        return sanitize_multi_answer(question, form_data.getlist(question["id"]))
    value = form_data.get(question["id"], "").strip()
    return value or None


def get_answer_values(answer: str | list[str] | None) -> set[str]:
    if answer is None:
        return set()
    if isinstance(answer, list):
        return set(answer)
    return {answer}


def has_non_none_answer(question_id: str, responses: dict) -> bool:
    question = None
    QUESTIONS = get_questions_for_regulations([], include_hidden=True)
    for q in QUESTIONS:
        if q["id"] == question_id:
            question = q
            break
    answer = responses.get(question_id)
    if not question or not answer_is_present(answer):
        return False
    none_value = question.get("evaluation", {}).get("none_value")
    values = get_answer_values(answer)
    return any(value != none_value for value in values)


app.jinja_env.globals["csrf_token"] = generate_csrf_token
app.jinja_env.globals["project_name"] = PROJECT_NAME
app.jinja_env.globals["project_full_name"] = PROJECT_FULL_NAME


@app.before_request
def csrf_protect():
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        token = session.get("csrf_token")
        form_token = request.form.get("csrf_token")
        if not token or not form_token or not hmac.compare_digest(token, form_token):
            abort(403)


@app.route("/")
def index():
    state = load_state()
    return render_template(
        "index.html",
        selected_regulations=state.get("selected_regulations", []),
        selected_regulation_text=regulation_display_labels(
            state.get("selected_regulations", [])
        ),
        law_updates=get_law_updates(),
        project_overview=PROJECT_OVERVIEW,
        background_cases=BACKGROUND_CASES,
        background_stats=BACKGROUND_STATS,
        expected_effects=EXPECTED_EFFECTS,
        process_steps=USER_PROCESS_STEPS,
    )


@app.post("/start")
def start_diagnosis():
    selected_regulations = [
        regulation
        for regulation in ["GDPR", "CCPA"]
        if regulation in request.form.getlist("selected_regulations")
    ]

    has_error = False
    if not 1 <= len(selected_regulations) <= 2:
        flash("GDPR 또는 CCPA를 최소 1개 이상 선택하세요.", "error")
        has_error = True

    if has_error:
        state = load_state()
        state["selected_regulations"] = selected_regulations
        save_state(state)
        return redirect(url_for("index"))

    state = blank_state()
    state["selected_regulations"] = selected_regulations
    save_state(state)
    return redirect(url_for("diagnosis", page=1))


@app.route("/diagnosis", methods=["GET", "POST"])
def diagnosis():
    state = load_state()
    requested_page = request.args.get("page", default=1, type=int)

    if request.method == "POST":
        requested_page = request.form.get("page", default=1, type=int)
        all_questions = get_selected_questions(state)
        if not all_questions:
            flash("먼저 진단할 규정을 선택하세요.", "error")
            return redirect(url_for("index"))

        (
            _page_questions,
            _visible_page_questions,
            _visible_ids,
            current_page,
            total_pages,
        ) = get_page_questions(
            all_questions, state.get("responses", {}), requested_page
        )
        state["responses"] = update_responses_for_questions(
            state.get("responses", {}), all_questions, request.form
        )
        state = prune_hidden_responses(state)
        save_state(state)

        action = request.form.get("action", "next")
        if action == "prev":
            target_page = (
                find_page_with_visible_questions(
                    all_questions, state.get("responses", {}), current_page - 1, -1
                )
                or 1
            )
            return redirect(url_for("diagnosis", page=target_page))

        (
            page_questions_after,
            visible_page_questions_after,
            _visible_ids_after,
            current_page,
            total_pages,
        ) = get_page_questions(
            all_questions, state.get("responses", {}), requested_page
        )
        invalid_question_ids = validate_page_questions(
            visible_page_questions_after, state.get("responses", {})
        )
        if invalid_question_ids:
            flash(
                "현재 페이지의 모든 문항에 응답해야 다음 단계로 이동할 수 있습니다.",
                "error",
            )
            return render_diagnosis_page(state, current_page, invalid_question_ids)

        consistency_issues = find_consistency_issues(state)
        current_page_ids = {question["id"] for question in visible_page_questions_after}
        current_page_issues = [
            issue
            for issue in consistency_issues
            if current_page_ids.intersection(issue["question_ids"])
        ]
        if current_page_issues:
            flash(
                "응답 간 논리 충돌이 있습니다. 표시된 문항의 관련 응답을 다시 확인하세요.",
                "error",
            )
            return render_diagnosis_page(state, current_page)

        if action == "complete":
            first_issue_page = find_first_issue_page(all_questions, consistency_issues)
            if first_issue_page is not None:
                flash(
                    "진단을 완료하기 전에 응답 간 논리 충돌을 먼저 수정하세요.",
                    "error",
                )
                return redirect(url_for("diagnosis", page=first_issue_page))
            return redirect(url_for("result"))
        target_page = find_page_with_visible_questions(
            all_questions, state.get("responses", {}), current_page + 1, 1
        )
        if target_page is None:
            return redirect(url_for("result"))
        return redirect(url_for("diagnosis", page=target_page))

    state = prune_hidden_responses(state)
    save_state(state)
    return render_diagnosis_page(state, requested_page)


@app.route("/result")
def result():
    state = prune_hidden_responses(load_state())
    save_state(state)
    questions = get_active_questions(state)
    all_questions = get_selected_questions(state)
    if not questions:
        flash("먼저 진단을 시작하세요.", "error")
        return redirect(url_for("index"))
    incomplete_page = first_incomplete_page(state)
    if incomplete_page is not None:
        flash("모든 진단 문항에 응답한 뒤 결과를 확인할 수 있습니다.", "error")
        return redirect(url_for("diagnosis", page=incomplete_page))
    issue_page = find_first_issue_page(all_questions, find_consistency_issues(state))
    if issue_page is not None:
        flash("응답 간 논리 충돌을 수정한 뒤 결과를 확인할 수 있습니다.", "error")
        return redirect(url_for("diagnosis", page=issue_page))
    return render_template("result.html", **build_results_context(state))


@app.route("/report/print")
def print_report():
    state = prune_hidden_responses(load_state())
    save_state(state)
    questions = get_active_questions(state)
    all_questions = get_selected_questions(state)
    if not questions:
        flash("출력할 진단 결과가 없습니다.", "error")
        return redirect(url_for("index"))
    incomplete_page = first_incomplete_page(state)
    if incomplete_page is not None:
        flash("PDF 출력 전 모든 문항에 응답해야 합니다.", "error")
        return redirect(url_for("diagnosis", page=incomplete_page))
    issue_page = find_first_issue_page(all_questions, find_consistency_issues(state))
    if issue_page is not None:
        flash("응답 간 논리 충돌을 수정한 뒤 PDF를 출력할 수 있습니다.", "error")
        return redirect(url_for("diagnosis", page=issue_page))
    return render_template("print_report.html", **build_results_context(state))


@app.route("/reset", methods=["POST"])
def reset_assessment():
    save_state(blank_state())
    flash("진단 상태를 초기화했습니다.", "info")
    return redirect(url_for("index"))


QUESTIONS = get_questions_for_regulations([], include_hidden=True)


def render_diagnosis_page(
    state: dict,
    requested_page: int,
    invalid_question_ids: list[str] | None = None,
):
    questions = get_active_questions(state)
    all_questions = get_selected_questions(state)
    selected_regulations = state.get("selected_regulations", [])
    if not all_questions:
        flash("먼저 진단할 규정을 선택하세요.", "error")
        return redirect(url_for("index"))

    responses = state.get("responses", {})
    page_questions, visible_page_questions, visible_ids, current_page, total_pages = (
        get_page_questions(all_questions, responses, requested_page)
    )
    if not visible_page_questions:
        next_page = find_page_with_visible_questions(
            all_questions, responses, current_page, 1
        )
        previous_page = find_page_with_visible_questions(
            all_questions, responses, current_page, -1
        )
        target_page = next_page or previous_page or 1
        if target_page != current_page:
            return redirect(url_for("diagnosis", page=target_page))

    consistency_issues = find_consistency_issues(state)
    current_page_ids = {question["id"] for question in visible_page_questions}
    current_page_issues = [
        issue
        for issue in consistency_issues
        if current_page_ids.intersection(issue["question_ids"])
    ]
    issue_question_ids = {
        question_id
        for issue in current_page_issues
        for question_id in issue["question_ids"]
    }
    answered_count = sum(
        1 for question in questions if answer_is_present(responses.get(question["id"]))
    )
    unanswered_count = sum(
        1
        for question in questions
        if not answer_is_present(responses.get(question["id"]))
    )

    effective_page_size = get_effective_page_size(len(all_questions))
    decorated_all_questions = []
    for index, question in enumerate(all_questions, start=1):
        question_copy = dict(question)
        question_copy["inline_law_details"], question_copy["inline_term_details"] = (
            build_inline_guidance(question)
        )
        question_copy["none_value"] = question.get("evaluation", {}).get("none_value")
        question_copy["exclusive_values"] = (
            question.get("evaluation", {}).get("exclusive_values") or []
        )
        question_copy["one_of_groups"] = (
            question.get("evaluation", {}).get("one_of_groups") or []
        )
        question_copy["page_slot"] = math.ceil(index / effective_page_size)
        question_copy["visible_if_json"] = json.dumps(
            question.get("visible_if"), ensure_ascii=False
        )
        question_copy["is_visible"] = question["id"] in visible_ids
        question_copy["is_current_page"] = question_copy["page_slot"] == current_page
        decorated_all_questions.append(question_copy)

    return render_template(
        "diagnosis.html",
        selected_regulations=selected_regulations,
        selected_regulation_text=regulation_display_labels(
            selected_regulations
        ),
        questions=questions,
        all_questions=decorated_all_questions,
        current_page=current_page,
        total_pages=total_pages,
        answered_count=answered_count,
        total_questions=len(questions),
        remaining_count=len(questions) - answered_count,
        unanswered_count=unanswered_count,
        progress_percent=round((answered_count / len(questions)) * 100)
        if questions
        else 0,
        defined_question_count=sum(
            1
            for question in QUESTIONS
            if question["regulation"] in selected_regulations
        ),
        consistency_issues=current_page_issues,
        issue_question_ids=issue_question_ids,
        responses=responses,
        invalid_question_ids=set(invalid_question_ids or []),
    )


with app.app_context():
    init_db()
