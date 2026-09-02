from __future__ import annotations

import json
import math
import os
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

from diagnostic_content import (
    PAGE_SIZE,
    QUESTIONS,
    QUESTION_INDEX,
    REGULATION_META,
    STATUS_LABELS,
    STATUS_ORDER,
    STATUS_SCORES,
    get_questions_for_regulations,
    question_visible,
)
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
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "ppap-prototype-dev-key")
app.config["DATABASE"] = Path(app.instance_path) / "ppap.sqlite3"

Path(app.instance_path).mkdir(parents=True, exist_ok=True)

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

LEGAL_BASIS_GUIDANCE = [
    (
        ("GDPR 제4조 제1호",),
        "GDPR 제4조 제1호는 식별되었거나 식별 가능한 살아있는 자연인에 관한 정보를 개인정보로 정의합니다.",
    ),
    (
        ("GDPR 제4조 제2호",),
        "GDPR 제4조 제2호는 수집, 기록, 저장, 전송, 공개, 삭제 등 개인정보에 하는 거의 모든 행위를 '처리'로 봅니다.",
    ),
    (
        ("GDPR 제4조 제4호", "GDPR 제4조(4)"),
        "GDPR 제4조 제4호는 프로파일링을 자동 처리로 정의하며 개인의 성향, 선호, 행동을 평가·예측하는 처리까지 포함합니다.",
    ),
    (
        ("GDPR 제4조 제5호",),
        "GDPR 제4조 제5호는 가명처리를 직접 식별자를 치운 상태로 설명하지만, 다시 연결 가능하면 여전히 개인정보일 수 있음을 전제합니다.",
    ),
    (
        ("GDPR 제4조 제7호",),
        "GDPR 제4조 제7호는 개인정보 처리 목적과 수단을 결정하는 주체를 컨트롤러로 봅니다.",
    ),
    (
        ("GDPR 제4조 제8호",),
        "GDPR 제4조 제8호는 컨트롤러를 대신해 개인정보를 처리하는 주체를 프로세서로 정의합니다.",
    ),
    (
        ("GDPR 제4조 제11호", "GDPR 제4조(11)"),
        "GDPR 제4조 제11호는 동의를 자유롭고, 구체적이며, 정보에 기반하고, 명확한 의사표시로 요구합니다.",
    ),
    (
        ("GDPR 제5조 제1항 (a)", "GDPR 제5조(1)(a)", "GDPR 제5조"),
        "GDPR 제5조는 적법성, 공정성, 투명성, 목적 제한, 최소수집 같은 기본 원칙을 정합니다.",
    ),
    (
        ("GDPR 제5조 제1항 (c)", "GDPR 제5조(1)(c)"),
        "GDPR 제5조 제1항 (c)는 처리 목적에 필요한 최소한의 데이터만 수집·처리해야 한다는 데이터 최소화 원칙입니다.",
    ),
    (
        ("GDPR 제5조(2)",),
        "GDPR 제5조 제2항은 원칙을 지키는 것뿐 아니라 그 이행 사실까지 입증해야 한다는 책임성 원칙을 둡니다.",
    ),
    (
        ("GDPR 제6조",),
        "GDPR 제6조는 동의, 계약, 법적 의무, 정당한 이익 등 적법근거 중 하나가 있어야 개인정보 처리가 가능하다고 규정합니다.",
    ),
    (
        ("GDPR 제7조",),
        "GDPR 제7조는 동의 입증, 쉬운 철회, 자유롭고 구체적인 동의라는 기본 요건을 다룹니다.",
    ),
    (
        ("GDPR 제8조",),
        "GDPR 제8조는 아동 대상 정보사회서비스에서 회원국별 연령 기준과 친권자 동의 요건을 규정합니다.",
    ),
    (
        ("GDPR 제9조",),
        "GDPR 제9조는 건강정보, 생체정보 등 민감정보를 원칙적으로 금지하고, 명시적 동의나 법정 예외가 있을 때만 허용합니다.",
    ),
    (
        ("GDPR 제12조",),
        "GDPR 제12조는 정보주체에게 제공하는 안내와 권리 응답을 명확하고 이해하기 쉬운 언어로 제공하라고 요구합니다.",
    ),
    (
        ("GDPR 제13조",),
        "GDPR 제13조는 수집 시점에 목적, 법적근거, 수령자, 국외이전, 보유기간 등 핵심 정보를 정보주체에게 고지하도록 요구합니다.",
    ),
    (
        ("GDPR 제14조",),
        "GDPR 제14조는 개인정보를 정보주체로부터 직접 받지 않은 경우에도 일정 기간 안에 필요한 고지를 제공하도록 요구합니다.",
    ),
    (
        ("GDPR 제15조",),
        "GDPR 제15조는 정보주체가 자신의 개인정보 사본과 처리 목적, 수령자, 이전 정보 등을 열람할 권리를 규정합니다.",
    ),
    (
        ("GDPR 제19조",),
        "GDPR 제19조는 정정·삭제·처리제한이 이루어지면 그 정보를 받은 수령자에게도 이를 통지해야 한다고 정합니다.",
    ),
    (
        ("GDPR 제22조",),
        "GDPR 제22조는 법적 효과 또는 그에 준하는 중대한 영향을 주는 완전 자동결정에 제한과 권리보장을 둡니다.",
    ),
    (
        ("GDPR 제24조",),
        "GDPR 제24조는 적절한 보호조치를 설계·운영하고 그 이행을 입증해야 하는 책임성을 요구합니다.",
    ),
    (
        ("GDPR 제25조",),
        "GDPR 제25조는 개인정보 보호 중심 설계와 기본설정 원칙을 요구합니다.",
    ),
    (
        ("GDPR 제26조",),
        "GDPR 제26조는 공동 컨트롤러가 책임 배분 약정을 체결하고 핵심 내용을 공개하도록 요구합니다.",
    ),
    (
        ("GDPR 제28조",),
        "GDPR 제28조는 프로세서와의 처리계약에 목적, 범위, 보안, 재위탁, 종료 후 삭제 등을 포함하도록 정합니다.",
    ),
    (
        ("GDPR 제30조",),
        "GDPR 제30조는 처리활동 기록(RoPA)에 개인정보 범주, 목적, 수령자, 국외이전 등을 문서화하도록 요구합니다.",
    ),
    (
        ("GDPR 제32조",),
        "GDPR 제32조는 위험에 비례한 기술적·관리적 보호조치를 요구합니다.",
    ),
    (
        ("GDPR 제35조",),
        "GDPR 제35조는 고위험 처리에 대해 DPIA를 수행해 위험과 완화조치를 사전 평가하도록 요구합니다.",
    ),
    (
        ("GDPR 제44조~제49조", "GDPR 제45조~제49조"),
        "GDPR 제44조부터 제49조는 EEA 밖으로 개인정보를 이전할 때 적정성 결정, SCC, BCR 또는 제한적 예외사유 같은 적법한 이전 수단이 필요하다고 규정합니다.",
    ),
    (
        ("GDPR 제45조",),
        "GDPR 제45조는 적정성 결정이 있는 국가·기관에는 별도 추가 수단 없이 이전할 수 있음을 다룹니다.",
    ),
    (
        ("GDPR 제46조",),
        "GDPR 제46조는 적정성 결정이 없을 때 SCC 등 적절한 보호조치를 통해 이전할 수 있도록 합니다.",
    ),
    (
        ("GDPR 제47조",),
        "GDPR 제47조는 BCR을 다국적 기업집단 내부의 국외이전을 위한 승인형 내부 규칙으로 다룹니다.",
    ),
    (
        ("GDPR 제49조",),
        "GDPR 제49조는 명시적 동의나 계약상 필요 같은 예외사유를 제한적·비반복적 상황에서만 쓰도록 합니다.",
    ),
    (
        ("GDPR 고려사항 제26항",),
        "GDPR 고려사항 제26항은 개인정보 여부를 판단할 때 합리적인 재식별 수단까지 고려해야 하며, 완전 익명정보만 적용 밖이 된다고 설명합니다.",
    ),
    (
        ("GDPR 고려사항 제28항",),
        "GDPR 고려사항 제28항은 가명처리된 데이터라도 추가정보로 재연결 가능하면 GDPR 적용 대상에 남는다고 설명합니다.",
    ),
    (
        ("GDPR 고려사항 제30항",),
        "GDPR 고려사항 제30항은 IP 주소, 쿠키 식별자, 기기 식별자 같은 온라인 식별자도 개인과 연결되면 개인정보가 될 수 있음을 설명합니다.",
    ),
    (
        ("GDPR 고려사항 제47항",),
        "GDPR 고려사항 제47항은 정당한 이익 근거를 사용할 때 정보주체의 합리적 기대와 권리 침해 여부를 함께 살피라고 봅니다.",
    ),
    (
        ("GDPR 고려사항 제58항",),
        "GDPR 고려사항 제58항은 특히 아동에게 제공되는 고지가 더 명확하고 이해하기 쉬워야 함을 강조합니다.",
    ),
    (
        ("GDPR 고려사항 제71항",),
        "GDPR 고려사항 제71항은 프로파일링과 자동결정에서 차별, 부당한 배제 같은 위험을 줄일 보호조치가 필요하다고 설명합니다.",
    ),
    (
        ("ePrivacy Directive 제5조(3)",),
        "ePrivacy Directive 제5조(3)은 이용자 단말기에 정보를 저장하거나 읽는 쿠키·유사기술에 대해 엄격히 필요한 경우를 제외하면 사전 동의를 요구합니다.",
    ),
    (
        ("Schrems II 판결",),
        "Schrems II 판결은 SCC 문서만으로 충분한지뿐 아니라 수령국 법제와 추가 보호조치까지 함께 평가해야 한다는 기준을 제시했습니다.",
    ),
    (
        ("Planet49",),
        "Planet49 판결은 사전 체크박스 방식의 쿠키 동의가 유효하지 않다는 대표 판례입니다.",
    ),
    (
        ("CJEU Case C-582/14", "Breyer 판례", "Breyer 판결"),
        "Breyer 판결은 동적 IP 주소도 합리적 수단으로 개인과 연결될 수 있으면 개인정보가 될 수 있다고 보았습니다.",
    ),
    (
        ("CJEU Case C-434/16", "Nowak 판결", "Nowak 판례"),
        "Nowak 판결은 평가 의견, 메모, 시험 답안처럼 개인에 관한 평가 정보도 개인정보가 될 수 있다고 설명합니다.",
    ),
    (
        ("CCPA §1798.100(a)",),
        "CCPA §1798.100(a)는 수집 시점에 개인정보 카테고리와 이용 목적, 판매·공유 여부 등을 소비자에게 고지해야 한다고 정합니다.",
    ),
    (
        ("CCPA §1798.100(d)",),
        "CCPA §1798.100(d)는 사업목적 제공 관계라면 서비스제공자 또는 계약자 요건을 충족하는 계약 구조가 필요하다는 전제를 둡니다.",
    ),
    (
        ("CCPA §1798.105(d)",),
        "CCPA §1798.105(d)는 삭제 요청이 있어도 법정 예외사유가 있으면 계속 보유할 수 있다고 규정합니다.",
    ),
    (
        ("CCPA §1798.120", "CCPA §1798.120(c)"),
        "CCPA §1798.120은 개인정보 판매·공유에 대한 소비자의 거부권과 미성년자에 대한 opt-in 요건을 규정합니다.",
    ),
    (
        ("CCPA §1798.121",),
        "CCPA §1798.121은 민감 개인정보에 대한 이용 제한권을 다룹니다.",
    ),
    (
        ("CCPA §1798.125",),
        "CCPA §1798.125는 소비자가 권리를 행사했다는 이유만으로 가격, 품질, 서비스에서 차별해서는 안 된다고 규정합니다.",
    ),
    (
        ("CCPA §1798.130",),
        "CCPA §1798.130은 권리 행사 방법, 응답 기한, 최근 12개월 정보 공개 등 개인정보처리방침 기재사항과 운영 절차를 규정합니다.",
    ),
    (
        ("CCPA §1798.135",),
        "CCPA §1798.135는 판매·공유 옵트아웃 링크와 GPC 신호 수용 같은 외부 선택권 경로를 규정합니다.",
    ),
    (
        ("CCPA §1798.140(v)",),
        "CCPA §1798.140(v)는 합리적으로 소비자 또는 가구와 연결될 수 있는 정보를 개인정보로 정의합니다.",
    ),
    (
        ("CCPA §1798.140(v)(1)",),
        "CCPA §1798.140(v)(1)은 식별자, 상업정보, 인터넷 활동정보, 위치정보, 추론정보 같은 카테고리 예시를 제시합니다.",
    ),
    (
        ("CCPA §1798.140(ae)",),
        "CCPA §1798.140(ae)는 정부 식별번호, 정밀 위치정보, 로그인 자격정보 등 민감 개인정보 범주를 정의합니다.",
    ),
    (
        ("CCPA §1798.140(h)", "CCPA §1798.140(l)"),
        "CCPA §1798.140(h), (l)은 소비자 동의와 다크패턴에 의한 무효 동의를 구분하는 정의 규정과 연결됩니다.",
    ),
    (
        ("CCPA §1798.192",),
        "CCPA §1798.192는 다크패턴을 통한 사용자 유도 방식은 유효한 동의 또는 선택권 행사로 보기 어렵다는 방향을 보여줍니다.",
    ),
    (
        ("11 CCR §7220~7227",),
        "11 CCR §7220~7227은 자동화된 의사결정 기술 관련 사전고지, 접근권, 옵트아웃, 영향평가 체계를 다루는 시행 규정 묶음입니다.",
    ),
    (
        ("§7150",),
        "11 CCR §7150 이하 규정은 위험평가 등 캘리포니아 규정 세부 절차를 보완하는 시행체계를 다룹니다.",
    ),
]

TERM_GUIDANCE = [
    (
        ("자연인", "natural person"),
        "자연인은 살아 있는 인간 개인을 뜻하는 법률 용어이며, 법인·단체·기관 자체는 포함하지 않습니다.",
    ),
    (
        ("개인정보", "personal data"),
        "개인정보는 이름뿐 아니라 다른 정보와 결합해 특정 사람을 알아볼 수 있는 정보까지 포함합니다.",
    ),
    (
        ("consumer", "소비자"),
        "CCPA의 소비자는 캘리포니아 거주 자연인을 뜻하며, 단순 방문자도 조건에 따라 포함될 수 있습니다.",
    ),
    (
        ("household", "가구"),
        "가구는 함께 거주하며 하나의 생활 단위로 연결되는 사람들의 집합을 뜻해, 개인이 아니어도 CCPA 판단에 중요할 수 있습니다.",
    ),
    (
        ("controller", "컨트롤러", "개인정보처리자"),
        "컨트롤러는 개인정보 처리 목적과 수단을 결정하는 주체입니다.",
    ),
    (
        ("processor", "프로세서", "처리수탁자", "처리자"),
        "프로세서는 컨트롤러의 지시에 따라 개인정보를 처리하는 수탁자 역할입니다.",
    ),
    (
        ("scc",),
        "SCC는 EU 표준계약조항으로, 적정성 결정이 없는 국가로 개인정보를 이전할 때 가장 널리 쓰이는 계약상 보호수단입니다.",
    ),
    (
        ("bcr",),
        "BCR은 같은 기업집단 내부 국외이전에 사용하는 감독기관 승인형 내부 규칙입니다.",
    ),
    (("gpc",), "GPC는 브라우저가 전송하는 판매·공유 옵트아웃 선호신호입니다."),
    (
        ("spi", "민감정보", "민감 개인정보"),
        "민감 개인정보는 정밀 위치정보, 로그인 자격정보, 건강정보처럼 추가 제한이나 강화된 보호가 필요한 정보입니다.",
    ),
    (
        ("admt",),
        "ADMT는 사람의 판단을 대체하거나 실질적으로 보조하는 자동화된 의사결정 기술입니다.",
    ),
    (
        ("dpia",),
        "DPIA는 고위험 처리에 앞서 위험과 보호조치를 평가하는 개인정보 영향평가 절차입니다.",
    ),
    (
        ("ropa",),
        "RoPA는 처리 목적, 개인정보 범주, 수령자, 국외이전 현황을 정리한 처리활동 기록입니다.",
    ),
    (
        ("pseudonym", "가명처리"),
        "가명처리는 직접 식별자를 치운 상태이지만, 추가정보로 다시 연결 가능하면 여전히 개인정보로 취급될 수 있습니다.",
    ),
    (
        ("anonymous", "익명정보"),
        "완전한 익명정보는 합리적인 수단으로도 특정인을 다시 알아볼 수 없는 상태를 말합니다.",
    ),
    (
        ("sell/share", "판매(sell)", "공유(share)", "판매·공유", "판매 또는 공유"),
        "CCPA의 판매·공유는 금전 거래뿐 아니라 교차맥락 행동광고 목적의 제3자 제공까지 넓게 해석될 수 있습니다.",
    ),
    (
        ("service provider", "서비스제공자"),
        "서비스제공자는 사업자의 지시에 따라 정해진 사업목적으로만 개인정보를 처리하는 외부 수탁업체 유형입니다.",
    ),
    (
        ("contractor", "계약자"),
        "CCPA의 계약자는 계약상 제한을 전제로 개인정보를 처리하는 외부 파트너 유형으로, 일반 제3자와 구분됩니다.",
    ),
]


def blank_state() -> dict:
    return {
        "selected_regulations": [],
        "gdpr_role": "",
        "responses": {},
    }


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
    state.setdefault("gdpr_role", "")
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


def role_label(role: str) -> str:
    return {
        "controller": "개인정보처리자 기준",
        "processor": "처리수탁자 기준",
    }.get(role, "미선택")


def regulation_display_labels(
    selected_regulations: list[str], gdpr_role: str
) -> list[str]:
    labels = []
    for regulation in selected_regulations:
        if regulation == "GDPR" and gdpr_role:
            labels.append(f"GDPR ({role_label(gdpr_role)})")
        else:
            labels.append(regulation)
    return labels


def regulation_display_text(selected_regulations: list[str], gdpr_role: str) -> str:
    return ", ".join(regulation_display_labels(selected_regulations, gdpr_role))


def sanitize_multi_answer(question: dict, raw_values: list[str]) -> list[str] | None:
    valid_values = {choice["value"] for choice in question["choices"]}
    values = [value for value in raw_values if value in valid_values]

    none_value = question.get("evaluation", {}).get("none_value")
    if none_value and none_value in values and len(values) > 1:
        values = [value for value in values if value != none_value]

    values = list(dict.fromkeys(values))
    return values or None


def extract_answer(question: dict, form_data) -> str | list[str] | None:
    if question["type"] == "multi":
        return sanitize_multi_answer(question, form_data.getlist(question["id"]))

    value = form_data.get(question["id"], "").strip()
    return value or None


def answer_is_present(answer: str | list[str] | None) -> bool:
    if answer is None:
        return False
    if isinstance(answer, list):
        return len(answer) > 0
    return answer != ""


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


def get_choice_label_map(question: dict) -> dict[str, str]:
    return {choice["value"]: choice["label"] for choice in question["choices"]}


def format_answer(question: dict, answer: str | list[str]) -> str:
    label_map = get_choice_label_map(question)
    if isinstance(answer, list):
        return ", ".join(label_map.get(value, value) for value in answer)
    return label_map.get(answer, answer)


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


def validate_page_questions(page_questions: list[dict], responses: dict) -> list[str]:
    return [
        question["id"]
        for question in page_questions
        if not answer_is_present(responses.get(question["id"]))
    ]


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


def build_question_page_map(questions: list[dict]) -> dict[str, int]:
    return {
        question["id"]: math.ceil(index / PAGE_SIZE)
        for index, question in enumerate(questions, start=1)
    }


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


def find_page_with_visible_questions(
    all_questions: list[dict], responses: dict, start_page: int, direction: int
) -> int | None:
    total_pages = max(1, math.ceil(len(all_questions) / PAGE_SIZE))
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


def build_question_number_map(questions: list[dict]) -> dict[str, int]:
    return {question["id"]: index for index, question in enumerate(questions, start=1)}


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


def evaluate_question(question: dict, answer: str | list[str]) -> dict:
    evaluation = question["evaluation"]
    answer_summary = format_answer(question, answer)

    if evaluation["kind"] == "single":
        status = evaluation["status_map"][answer]
    elif evaluation["kind"] == "multi_presence":
        normalized = (
            sanitize_multi_answer(
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
            sanitize_multi_answer(
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
            sanitize_multi_answer(
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


def get_active_questions(state: dict) -> list[dict]:
    selected = state.get("selected_regulations", [])
    responses = state.get("responses", {})
    return get_questions_for_regulations(selected, responses)


def get_selected_questions(state: dict) -> list[dict]:
    return get_questions_for_regulations(
        state.get("selected_regulations", []), include_hidden=True
    )


def paginate_questions(questions: list[dict], page: int) -> tuple[list[dict], int, int]:
    total_pages = max(1, math.ceil(len(questions) / PAGE_SIZE))
    current_page = max(1, min(page, total_pages))
    start_index = (current_page - 1) * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    return questions[start_index:end_index], current_page, total_pages


def summarize_counts(items: list[dict]) -> dict[str, int]:
    counts = Counter(item["status"] for item in items)
    return {status: counts.get(status, 0) for status in STATUS_ORDER}


def build_status_cards(counts: dict[str, int]) -> list[dict]:
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


def score_from_items(items: list[dict]) -> int:
    if not items:
        return 0
    total = sum(STATUS_SCORES[item["status"]] for item in items)
    return round(total / len(items))


def build_regulation_groups(
    selected_regulations: list[str], evaluated_items: list[dict]
) -> list[dict]:
    groups = []
    for regulation in selected_regulations:
        regulation_items = [
            item for item in evaluated_items if item["regulation"] == regulation
        ]
        counts = summarize_counts(regulation_items)
        sections = {}
        for item in regulation_items:
            sections.setdefault(item["section"], []).append(item)
        groups.append(
            {
                "key": regulation,
                "title": REGULATION_META[regulation]["title"],
                "subtitle": REGULATION_META[regulation]["subtitle"],
                "score": score_from_items(regulation_items),
                "counts": counts,
                "status_cards": build_status_cards(counts),
                "sections": [
                    {"name": name, "items": items} for name, items in sections.items()
                ],
            }
        )
    return groups


def build_results_context(state: dict) -> dict:
    state = prune_hidden_responses(state)
    questions = get_active_questions(state)
    selected_regulations = state.get("selected_regulations", [])
    gdpr_role = state.get("gdpr_role", "")
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

    counts = summarize_counts(evaluated_items)
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
        "selected_regulation_labels": regulation_display_labels(
            selected_regulations, gdpr_role
        ),
        "selected_regulation_text": regulation_display_text(
            selected_regulations, gdpr_role
        ),
        "gdpr_role": gdpr_role,
        "gdpr_role_label": role_label(gdpr_role),
        "questions": questions,
        "results": evaluated_items,
        "unanswered_items": unanswered_items,
        "priority_findings": priority_findings,
        "total_questions": total_questions,
        "completion_count": completion_count,
        "completion_rate": completion_rate,
        "unanswered_count": len(unanswered_items),
        "counts": counts,
        "score": score_from_items(evaluated_items),
        "generated_at": datetime.now().strftime("%Y.%m.%d %H:%M"),
        "status_cards": build_status_cards(counts),
        "regulation_groups": build_regulation_groups(
            selected_regulations, evaluated_items
        ),
    }


def render_diagnosis_page(
    state: dict, requested_page: int, invalid_question_ids: list[str] | None = None
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

    decorated_all_questions = []
    for index, question in enumerate(all_questions, start=1):
        question_copy = dict(question)
        question_copy["inline_law_details"], question_copy["inline_term_details"] = (
            build_inline_guidance(question)
        )
        question_copy["none_value"] = question.get("evaluation", {}).get("none_value")
        question_copy["page_slot"] = math.ceil(index / PAGE_SIZE)
        question_copy["visible_if_json"] = json.dumps(
            question.get("visible_if"), ensure_ascii=False
        )
        question_copy["is_visible"] = question["id"] in visible_ids
        question_copy["is_current_page"] = question_copy["page_slot"] == current_page
        decorated_all_questions.append(question_copy)

    return render_template(
        "diagnosis.html",
        selected_regulations=selected_regulations,
        selected_regulation_text=regulation_display_text(
            selected_regulations, state.get("gdpr_role", "")
        ),
        gdpr_role=state.get("gdpr_role", ""),
        gdpr_role_label=role_label(state.get("gdpr_role", "")),
        questions=questions,
        all_questions=decorated_all_questions,
        current_page=current_page,
        total_pages=total_pages,
        answered_count=answered_count,
        total_questions=len(questions),
        remaining_count=len(questions) - answered_count,
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


@app.context_processor
def inject_globals() -> dict:
    return {
        "status_labels": STATUS_LABELS,
        "regulation_meta": REGULATION_META,
        "project_name": PROJECT_NAME,
        "project_full_name": PROJECT_FULL_NAME,
    }


@app.route("/")
def index():
    state = load_state()
    return render_template(
        "index.html",
        selected_regulations=state.get("selected_regulations", []),
        selected_regulation_text=regulation_display_text(
            state.get("selected_regulations", []), state.get("gdpr_role", "")
        ),
        gdpr_role=state.get("gdpr_role", ""),
        gdpr_role_label=role_label(state.get("gdpr_role", "")),
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
    gdpr_role = request.form.get("gdpr_role", "")

    has_error = False
    if not 1 <= len(selected_regulations) <= 2:
        flash("GDPR 또는 CCPA를 최소 1개 이상 선택하세요.", "error")
        has_error = True
    if "GDPR" in selected_regulations and gdpr_role not in {"controller", "processor"}:
        flash(
            "GDPR을 선택한 경우 역할을 개인정보처리자 또는 처리수탁자 기준으로 지정하세요.",
            "error",
        )
        has_error = True

    if has_error:
        state = load_state()
        state["selected_regulations"] = selected_regulations
        state["gdpr_role"] = gdpr_role
        save_state(state)
        return redirect(url_for("index"))

    state = blank_state()
    state["selected_regulations"] = selected_regulations
    state["gdpr_role"] = gdpr_role if "GDPR" in selected_regulations else ""
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


@app.route("/reset")
def reset_assessment():
    save_state(blank_state())
    flash("진단 상태를 초기화했습니다.", "info")
    return redirect(url_for("index"))


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
