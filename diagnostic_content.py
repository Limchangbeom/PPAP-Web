from __future__ import annotations


PAGE_SIZE = 10

STATUS_LABELS = {
    "violation": "위반",
    "insufficient": "미흡",
    "compliant": "충족",
    "recommended": "권장",
}

STATUS_SCORES = {
    "violation": 0,
    "insufficient": 55,
    "recommended": 78,
    "compliant": 100,
}

STATUS_ORDER = ["violation", "insufficient", "compliant", "recommended"]

REGULATION_META = {
    "GDPR": {
        "title": "GDPR",
        "subtitle": "EU 일반 개인정보 보호 규정",
    },
    "CCPA": {
        "title": "CCPA",
        "subtitle": "캘리포니아 소비자 개인정보 보호법",
    },
}


def choice(value: str, label: str) -> dict:
    return {"value": value, "label": label}


def condition_all(*conditions: dict) -> dict:
    return {"all": list(conditions)}


def condition_any(*conditions: dict) -> dict:
    return {"any": list(conditions)}


def equals(question_id: str, value: str) -> dict:
    return {"id": question_id, "op": "equals", "value": value}


def includes(question_id: str, value: str) -> dict:
    return {"id": question_id, "op": "includes", "value": value}


def excludes(question_id: str, value: str) -> dict:
    return {"id": question_id, "op": "excludes", "value": value}


def one_of(question_id: str, values: list[str]) -> dict:
    return {"id": question_id, "op": "one_of", "values": values}


def single_question(
    question_id: str,
    regulation: str,
    section: str,
    title: str,
    question: str,
    description: str,
    legal_basis: str,
    choices: list[dict],
    status_map: dict[str, str],
    *,
    visible_if: dict | None = None,
    action_hint: str = "원문 기준에 맞춰 관련 문서, 설정, 절차를 점검하고 필요한 항목을 보완하세요.",
) -> dict:
    return {
        "id": question_id,
        "regulation": regulation,
        "section": section,
        "title": title,
        "question": question,
        "description": description,
        "legal_basis": legal_basis,
        "type": "single",
        "choices": choices,
        "visible_if": visible_if,
        "action_hint": action_hint,
        "evaluation": {
            "kind": "single",
            "status_map": status_map,
        },
    }


def multi_presence_question(
    question_id: str,
    regulation: str,
    section: str,
    title: str,
    question: str,
    description: str,
    legal_basis: str,
    choices: list[dict],
    *,
    none_value: str | None = None,
    any_status: str = "compliant",
    none_status: str = "recommended",
    visible_if: dict | None = None,
    action_hint: str = "선택한 범주가 실제 처리 흐름, 고지 문서, 인벤토리와 일치하는지 다시 확인하세요.",
) -> dict:
    return {
        "id": question_id,
        "regulation": regulation,
        "section": section,
        "title": title,
        "question": question,
        "description": description,
        "legal_basis": legal_basis,
        "type": "multi",
        "choices": choices,
        "visible_if": visible_if,
        "action_hint": action_hint,
        "evaluation": {
            "kind": "multi_presence",
            "none_value": none_value,
            "any_status": any_status,
            "none_status": none_status,
        },
    }


def checklist_question(
    question_id: str,
    regulation: str,
    section: str,
    title: str,
    question: str,
    description: str,
    legal_basis: str,
    choices: list[dict],
    *,
    required_values: list[str],
    recommended_values: list[str] | None = None,
    one_of_groups: list[list[str]] | None = None,
    forbidden_values: list[str] | None = None,
    none_value: str | None = None,
    none_status: str = "recommended",
    visible_if: dict | None = None,
    action_hint: str = "원문 기준상 빠진 체크 항목을 문서와 실제 운영 흐름에 반영하세요.",
) -> dict:
    return {
        "id": question_id,
        "regulation": regulation,
        "section": section,
        "title": title,
        "question": question,
        "description": description,
        "legal_basis": legal_basis,
        "type": "multi",
        "choices": choices,
        "visible_if": visible_if,
        "action_hint": action_hint,
        "evaluation": {
            "kind": "checklist",
            "required_values": required_values,
            "recommended_values": recommended_values or [],
            "one_of_groups": one_of_groups or [],
            "forbidden_values": forbidden_values or [],
            "none_value": none_value,
            "none_status": none_status,
        },
    }


def grouped_checklist_question(
    question_id: str,
    regulation: str,
    section: str,
    title: str,
    question: str,
    description: str,
    legal_basis: str,
    choices: list[dict],
    *,
    required_values: list[str],
    at_least_one_values: list[str],
    none_value: str | None = None,
    none_status: str = "recommended",
    visible_if: dict | None = None,
    action_hint: str = "근거가 되는 항목과 공통 보호조치를 함께 갖췄는지 다시 점검하세요.",
) -> dict:
    return {
        "id": question_id,
        "regulation": regulation,
        "section": section,
        "title": title,
        "question": question,
        "description": description,
        "legal_basis": legal_basis,
        "type": "multi",
        "choices": choices,
        "visible_if": visible_if,
        "action_hint": action_hint,
        "evaluation": {
            "kind": "grouped_checklist",
            "required_values": required_values,
            "at_least_one_values": at_least_one_values,
            "none_value": none_value,
            "none_status": none_status,
        },
    }


def question_visible(question: dict, responses: dict) -> bool:
    condition = question.get("visible_if")
    if not condition:
        return True
    return evaluate_condition(condition, responses)


def evaluate_condition(condition: dict, responses: dict) -> bool:
    if "all" in condition:
        return all(evaluate_condition(item, responses) for item in condition["all"])
    if "any" in condition:
        return any(evaluate_condition(item, responses) for item in condition["any"])

    answer = responses.get(condition["id"])
    op = condition["op"]
    if op == "equals":
        return answer == condition["value"]
    if op == "includes":
        return isinstance(answer, list) and condition["value"] in answer
    if op == "excludes":
        return not isinstance(answer, list) or condition["value"] not in answer
    if op == "one_of":
        if isinstance(answer, list):
            return any(value in answer for value in condition["values"])
        return answer in condition["values"]
    return False


QUESTIONS: list[dict] = []


def add(question: dict) -> None:
    QUESTIONS.append(question)


section = "1. 개인정보 범위"

gdpr_detailed_scope_questions = [
    single_question(
        "gdpr_scope_detail_person",
        "GDPR",
        section,
        "1. 살아있는 자연인에 대한 정보인가?",
        "처리하는 대상 정보가 법인, 단체, 기관 등에 관한 정보가 아닌, 오직 '살아있는 자연인'에 관한 정보에만 해당합니까?",
        "판단 포인트: GDPR 제4조 제1호의 자연인은 살아있는 인간 개인을 뜻하며, 법인·단체·기관 정보는 그 자체만으로는 이 질문의 대상이 아닙니다.",
        "GDPR 제4조 제1호",
        [
            choice("yes", "예"),
            choice("no", "아니오"),
            choice("unsure", "확인 필요"),
        ],
        {"yes": "compliant", "no": "recommended", "unsure": "insufficient"},
        action_hint="적용 대상이 불명확하면 수집 시스템별로 자연인 데이터 여부부터 재분류하세요.",
    ),
    multi_presence_question(
        "gdpr_scope_detail_identifier",
        "GDPR",
        section,
        "2-1. 이름·이메일·주소·계정ID 등 식별자에 해당하는가?",
        "다음과 같은 식별정보를 수집·생성·보유하는가?",
        "판단 포인트: 이름, 연락처, 계정정보, 온라인 식별자 등 직접·간접 식별 요소를 구체적으로 확인합니다.",
        "GDPR 제4조 제1호, 제30조",
        [
            choice("name", "성명"),
            choice("email", "이메일 주소"),
            choice("postal", "우편주소"),
            choice("username", "계정명"),
            choice("phone", "전화번호"),
            choice("passport", "여권번호 등 고유 식별 번호"),
            choice("online", "온라인 식별자(IP 주소, 쿠키 식별자, 기기 식별자 등)"),
            choice("no", "해당 없음"),
        ],
        none_value="no",
        any_status="compliant",
        none_status="compliant",
    ),
    multi_presence_question(
        "gdpr_scope_detail_activity",
        "GDPR",
        section,
        "2-2. 온라인 활동 및 네트워크 이용 정보인가?",
        "특정 자연인과 연결되는 다음과 같은 온라인 활동정보를 처리하는가?",
        "판단 포인트: 웹/앱 이용기록, 세션, 네트워크 활동정보를 개인정보 범주로 식별했는지 확인합니다.",
        "GDPR 제4조 제1호, 고려사항 제30항",
        [
            choice("page", "방문한 웹사이트 / 페이지"),
            choice("search", "검색 기록"),
            choice("click", "클릭 기록"),
            choice("app_use", "앱 또는 서비스 이용기록"),
            choice("browsing", "브라우징 기록"),
            choice("session", "접속·세션 정보"),
            choice("network", "네트워크 활동정보"),
            choice("no", "해당 없음"),
        ],
        none_value="no",
        any_status="compliant",
        none_status="compliant",
    ),
    multi_presence_question(
        "gdpr_scope_detail_location",
        "GDPR",
        section,
        "2-3. 위치정보인가?",
        "자연인과 연결되는 지리적 위치정보를 수집하는가?",
        "판단 포인트: GPS, IP 기반 위치, 이동경로, 위치이력 같은 위치 데이터 범주를 확인합니다.",
        "GDPR 제4조 제1호, 제6조",
        [
            choice("gps", "GPS"),
            choice("latlng", "위도·경도"),
            choice("ip", "IP 기반 위치"),
            choice("route", "이동경로"),
            choice("place", "방문 장소"),
            choice("history", "위치이력"),
            choice("other", "기타 지리적 위치정보"),
            choice("no", "해당 없음"),
        ],
        none_value="no",
        any_status="compliant",
        none_status="compliant",
    ),
    multi_presence_question(
        "gdpr_scope_detail_commercial",
        "GDPR",
        section,
        "2-4. 구매·거래·서비스 이용 등 상업적 정보인가?",
        "자연인의 상품·서비스 이용과 관련된 정보를 수집하는가?",
        "판단 포인트: 주문, 구매, 구독, 거래, 이용이력 같은 상업 정보 범주를 확인합니다.",
        "GDPR 제4조 제1호, 제5조 제1항",
        [
            choice("purchase", "구매내역"),
            choice("order", "주문내역"),
            choice("subscription", "구독내역"),
            choice("transaction", "거래정보"),
            choice("propensity", "구매·소비 성향"),
            choice("use_history", "상품·서비스 이용 이력"),
            choice("no", "해당 없음"),
        ],
        none_value="no",
        any_status="compliant",
        none_status="compliant",
    ),
    multi_presence_question(
        "gdpr_scope_detail_inference",
        "GDPR",
        section,
        "2-5. 개인에 대한 추론·프로파일링을 생성하는가?",
        "기존 데이터를 분석하여 자연인의 특성·성향·선호·행동 등을 추론하거나 프로파일(자동화된 처리)을 생성하는가?",
        "판단 포인트: 추론정보와 프로파일 결과물도 개인정보 범주로 보고 있는지 확인합니다.",
        "GDPR 제4조 제1호, 제4조 제4호, 제22조",
        [
            choice("interest", "관심사"),
            choice("preference", "선호도"),
            choice("purchase", "구매성향"),
            choice("segment", "고객 세그먼트"),
            choice("ad_profile", "광고 타겟팅 프로파일"),
            choice("prediction", "AI/ML 기반 예측 성향"),
            choice("no", "해당 없음"),
        ],
        none_value="no",
        any_status="compliant",
        none_status="compliant",
    ),
    multi_presence_question(
        "gdpr_scope_detail_sensitive",
        "GDPR",
        section,
        "2-6. 인종·건강·생체 등 민감정보(Special Categories)에 해당하는가?",
        "다음 중 하나에 해당하는 민감범주의 정보를 수집하는가?",
        "판단 포인트: GDPR 제9조 민감정보 범주를 별도로 식별하는지 확인합니다.",
        "GDPR 제9조 제1항 및 제2항",
        [
            choice("race", "인종 또는 민족적 출신"),
            choice("political", "정치적 견해"),
            choice("religion", "종교적 또는 철학적 신념"),
            choice("union", "노동조합 가입 여부"),
            choice("genetic", "유전정보"),
            choice(
                "biometric",
                "신원을 고유하게 식별할 목적으로 처리되는 생체정보",
            ),
            choice("health", "건강에 관한 정보"),
            choice("sexuality", "자연인의 성생활 또는 성적 지향에 관한 정보"),
            choice("no", "해당 없음"),
        ],
        none_value="no",
        any_status="recommended",
        none_status="compliant",
    ),
    multi_presence_question(
        "gdpr_scope_detail_anonymous",
        "GDPR",
        section,
        "2-7. 완전한 익명정보 예외에 해당하는가?",
        "해당 데이터가 GDPR의 적용을 받지 않는 완전한 익명정보에 해당하는가?",
        "판단 포인트: 합리적 수단으로 재식별이 불가능한 통계·집계 데이터인지 확인합니다.",
        "GDPR 고려사항 제26항, CJEU Breyer 판례",
        [
            choice(
                "stats", "어떠한 합리적 수단으로도 재식별이 불가능한 통계·집계 데이터"
            ),
            choice("detached", "자연인과 완전히 분리되어 식별성을 상실한 데이터"),
            choice("na", "해당 없음"),
        ],
        none_value="na",
        any_status="recommended",
        none_status="recommended",
        action_hint="익명정보 예외를 주장하는 경우 재식별 가능성 검토 근거를 별도로 문서화하세요.",
    ),
    single_question(
        "gdpr_scope_detail_pseudonym",
        "GDPR",
        section,
        "2-8. 가명처리되었으나 재식별이 가능한가?",
        "데이터에서 이름 등을 제거하거나 가명처리했으나, 다른 정보나 별도 키를 이용하면 특정 자연인과 다시 연결할 수 있는가?",
        "판단 포인트: 해시 이메일, 토큰, 내부 ID, 암호화 식별자처럼 재연결 가능한 데이터인지 확인합니다.",
        "GDPR 제4조 제5호, 고려사항 제28항",
        [
            choice("yes", "예"),
            choice("no", "아니오"),
            choice("unsure", "확인 필요"),
        ],
        {"yes": "recommended", "no": "compliant", "unsure": "insufficient"},
        action_hint="재식별이 가능하면 개인정보로 유지하고 키 분리, 접근통제, 권리 대응 체계를 함께 관리하세요.",
    ),
]

for question in gdpr_detailed_scope_questions:
    add(question)

for question_id, title, prompt, description, legal_basis, yes_status, no_status in [
    (
        "gdpr_media_scope",
        "3. 정보의 매체 및 형식 포괄성",
        "처리하는 정보가 정형화된 디지털 데이터베이스뿐만 아니라, 서면 문서, 음성 녹음, 영상 파일 등 매체와 형식의 제한 없이 살아있는 자연인에 관한 모든 정보를 포괄합니까?",
        "판단 포인트: DB 외의 종이문서, 녹취, 영상, 비정형 자료도 개인정보 범위에 포함하는지 확인합니다.",
        "GDPR 제4조 제1호 해석 지침",
        "compliant",
        "violation",
    ),
    (
        "gdpr_direct_identification",
        "4. 직접적 식별 가능성 여부",
        "수집·보유 중인 정보 자체만으로 추가적인 대조 없이 곧바로 특정 개인의 신원을 알아볼 수 있습니까?",
        "판단 포인트: 직접 식별 가능성은 간접 식별 검토로 이어지는 기준점입니다.",
        "GDPR 제4조 제1호",
        "recommended",
        "recommended",
    ),
    (
        "gdpr_indirect_identification",
        "5. 간접적 식별 가능성 및 결합 가능성",
        "단독으로는 특정 개인을 알 수 없더라도, 보유 중인 다른 정보와 대조·결합하거나 제3자의 협조를 얻는 등 합리적으로 사용될 가능성이 있는 모든 수단을 동원할 때 개인을 식별할 수 있습니까?",
        "판단 포인트: 회원번호, 주문내역, 내부 식별자, 로그 데이터의 결합 가능성을 확인합니다.",
        "GDPR 제4조 제1호, 고려사항 제26항",
        "compliant",
        "violation",
    ),
    (
        "gdpr_online_identifier_handling",
        "6. 온라인 식별자의 식별성 전제 처리 (Breyer 판례 기준)",
        "동적 IP 주소, 쿠키, 기기 식별자 등의 온라인 식별자를 다룰 때, 제3자의 추가적·법적·기술적 수단을 통해 신원과 연결될 수 있음을 전제로 개인정보로 취급하고 있습니까?",
        "판단 포인트: IP, 쿠키, 디바이스 ID를 익명정보로 오인하지 않는지 확인합니다.",
        "GDPR 제4조 제1호, 고려사항 제30항, CJEU Case C-582/14",
        "compliant",
        "violation",
    ),
    (
        "gdpr_subjective_records",
        "7. 주관적 평가·의견 및 기록 정보의 포섭 (Nowak 판례 기준)",
        "객관적 진실성이 검증되지 않은 주관적 의견, 평가, 메모, 업무상 기록 등이 특정 정보주체의 지식, 성과, 행동, 상태 등에 관한 정보를 담고 있다면 개인정보로 취급하고 있습니까?",
        "판단 포인트: 면접 메모, 상담기록, 불만 로그 같은 주관적 기록도 개인정보 범위에 포함하는지 확인합니다.",
        "CJEU Case C-434/16 (Nowak 판결)",
        "compliant",
        "violation",
    ),
    (
        "gdpr_anonymisation_vs_pseudonymisation",
        "8. 익명화와 가명화의 법적 구분 관리",
        "처리 중인 데이터가 완전한 익명화가 이루어져 합리적인 어떤 수단으로도 재식별이 원천적으로 불가능한 상태입니까?",
        "판단 포인트: 완전 익명화와 가명처리를 구분하고 있는지 확인합니다.",
        "GDPR 제4조 제5호, 고려사항 제26항·제28항",
        "compliant",
        "violation",
    ),
    (
        "gdpr_data_minimisation",
        "9. 최소 수집 원칙 준수 여부",
        "개인정보를 처리할 때, 정해진 처리 목적에 부합하며 필요한 최소한의 정보로만 수집 및 처리 범위가 엄격하게 제한되어 있습니까?",
        "판단 포인트: 불필요한 항목의 과다 수집 여부를 확인합니다.",
        "GDPR 제5조 제1항 (c)",
        "compliant",
        "violation",
    ),
]:
    add(
        single_question(
            question_id,
            "GDPR",
            section,
            title,
            prompt,
            description,
            legal_basis,
            [choice("yes", "예"), choice("no", "아니오")],
            {"yes": yes_status, "no": no_status},
        )
    )

section = "2. 개인정보 수집·이용 시 동의 필요 여부"
add(
    single_question(
        "gdpr_notice_purpose_basis",
        "GDPR",
        section,
        "1. 각 개인정보 처리 목적에 따른 처리 근거 명시 여부",
        "개인정보를 처리하는 목적과 그 목적을 허용하는 법적 근거, 목적에 사용되는 개인정보 항목을 명시하였습니까?",
        "판단 포인트: 처리 목적, 법적 근거, 사용 항목을 수집 시점에 함께 고지하는지 확인합니다.",
        "GDPR 제13조 제1항 (c), (d)",
        [choice("yes", "예"), choice("no", "아니오")],
        {"yes": "compliant", "no": "violation"},
    )
)
add(
    multi_presence_question(
        "gdpr_lawful_bases",
        "GDPR",
        section,
        "2. 다음 중 해당되는 개인정보 처리 근거",
        "다음 중 해당되는 개인정보 처리 근거를 모두 고르시오.",
        "판단 포인트: GDPR 제6조의 적법근거 중 실제 사용하는 근거를 누락 없이 선택합니다.",
        "GDPR 제6조 제1항",
        [
            choice("consent", "정보주체의 동의"),
            choice("contract", "계약의 이행"),
            choice(
                "legal_obligation",
                "법적 의무의 준수",
            ),
            choice(
                "vital_interests",
                "정보주체 또는 타인의 중대한 이익 보호",
            ),
            choice(
                "public_task",
                "공익을 위한 업무 수행 또는 공적 권한의 행사",
            ),
            choice("legitimate_interests", "정당한 이익"),
            choice("other", "그 외 다른 사유"),
        ],
        any_status="compliant",
        none_status="violation",
        action_hint="처리 목적마다 어떤 제6조 근거를 적용하는지 기능별로 명시하세요.",
    )
)
add(
    checklist_question(
        "gdpr_consent_requirements",
        "GDPR",
        section,
        "2-동의 세부 요건",
        "동의를 근거로 개인정보를 처리하는 경우, 다음 요건을 모두 갖추고 있습니까?",
        "판단 포인트: 동의 입증, 적극적 opt-in, 목적별 분리, 쉬운 철회, 힘의 불균형 여부를 함께 확인합니다.",
        "GDPR 제4조 제11호, 제7조, 제13조 제2항 (c), 전문 32·43",
        [
            choice(
                "proof", "정보주체가 개인정보 처리에 동의하였다는 사실을 입증할 수 있다"
            ),
            choice(
                "active",
                "동의가 사전에 체크된 박스, 침묵, 부작위가 아니라 명확한 적극적 행위로 이루어진다",
            ),
            choice(
                "purpose_split",
                "개인정보가 여러 목적으로 처리되는 경우, 각 목적마다 별도로 동의를 받는다",
            ),
            choice(
                "purpose_split_na",
                "개인정보가 여러 목적으로 처리되지 않아 각 목적별 분리 동의가 해당없다",
            ),
            choice(
                "clear_request",
                "다른 사항을 포함하는 서면 선언을 통해 동의를 받는 경우, 동의 요청이 다른 사항과 명확하게 구별되고 평이한 언어로 제시된다",
            ),
            choice(
                "clear_request_na",
                "그 자체로 완전히 독립된 화면/문서로 동의 요청하여 다른 사항과의 구별이 해당없다",
            ),
            choice(
                "withdraw_notice",
                "동의를 받기 전, 정보주체가 언제든 동의를 철회할 수 있다는 사실을 고지하였다",
            ),
            choice("withdraw_easy", "동의를 철회하는 과정이 동의를 하는 과정만큼 쉽다"),
            choice(
                "not_conditioned",
                "계약의 이행에 필요하지 않은 개인정보 처리에 대한 동의를 계약 이행의 조건으로 요구하지 않는다",
            ),
            choice(
                "power_balance",
                "공공기관이거나 고용관계 등 명백한 힘의 불균형이 있는 경우에도 동의 거부가 실제로 불이익 없이 가능하다",
            ),
        ],
        required_values=[
            "proof",
            "active",
            "withdraw_notice",
            "withdraw_easy",
            "not_conditioned",
            "power_balance",
        ],
        one_of_groups=[
            ["purpose_split", "purpose_split_na"],
            ["clear_request", "clear_request_na"],
        ],
        visible_if=includes("gdpr_lawful_bases", "consent"),
        action_hint="사전 체크박스 제거, 목적별 동의 분리, 철회 경로 단순화, 동의 로그 보관부터 우선 보완하세요.",
    )
)
add(
    checklist_question(
        "gdpr_legitimate_interest_requirements",
        "GDPR",
        section,
        "2-정당한 이익 세부 요건",
        "정당한 이익을 처리 근거로 사용하는 경우, 다음 요건을 충족합니까?",
        "판단 포인트: 정당한 이익의 구체적 표기와 정보주체 기본권 우위 여부를 확인합니다. 공공기관 여부도 별도로 검토해야 합니다.",
        "GDPR 제6조 제1항 (f), 제13조 제1항 (c), (d), 전문 47",
        [
            choice(
                "stated",
                "각 처리 목적을 통해 달성하고자 하는 정당한 이익이 무엇인지 구체적으로 표기하였다",
            ),
            choice(
                "balanced",
                "귀사 또는 제3자가 추구하는 정당한 이익이 정보주체의 이익 또는 기본권·자유보다 우선하지 않는다",
            ),
        ],
        required_values=["stated", "balanced"],
        visible_if=includes("gdpr_lawful_bases", "legitimate_interests"),
        action_hint="정당한 이익 문구와 balancing test 결과를 내부 문서와 고지문에 함께 남기세요.",
    )
)
add(
    single_question(
        "gdpr_sensitive_explicit_consent",
        "GDPR",
        section,
        "3. 민감정보 처리 시 명시적 동의 여부",
        "민감정보(특별범주 개인정보)를 처리하는 경우, 명시적 동의를 받습니까?",
        "판단 포인트: 민감정보는 일반 동의보다 높은 명확성이 요구됩니다.",
        "GDPR 제9조 제1항, 제2항 (a)",
        [choice("yes", "예"), choice("no", "아니오")],
        {"yes": "compliant", "no": "violation"},
        visible_if=excludes("gdpr_scope_detail_sensitive", "no"),
        action_hint="민감정보를 계속 처리하려면 제9조 제2항 근거와 명시적 동의 문구를 함께 확보하세요.",
    )
)

section = "3. 제3자 제공 시 별도 동의"
add(
    single_question(
        "gdpr_third_party_processing",
        "GDPR",
        section,
        "1. 처리 해당 여부",
        "현재 진행하고자 하는 행위(데이터 전송·열람 허용·공개 등)는 GDPR상 '처리'에 해당하는가?",
        "판단 포인트: 단순 기술적 경유인지, 실제 개인정보 처리인지 먼저 판별합니다.",
        "GDPR 제4조 제2호",
        [
            choice(
                "processing",
                "해당한다. 데이터 전송·열람 허용·공개 등 모두 처리 행위이다.",
            ),
            choice(
                "pass_through",
                "단순 기술적 경유이며 내용에 접근하지 않는다.",
            ),
        ],
        {"processing": "compliant", "pass_through": "recommended"},
    )
)
add(
    single_question(
        "gdpr_third_party_role",
        "GDPR",
        section,
        "2. 수령자 역할 판별",
        "정보를 넘겨받는 상대방(수령자)은 귀사의 지시에 따라서만 개인정보를 처리하는가, 혹은 스스로 처리 목적·방법을 결정하는가?",
        "판단 포인트: 처리수탁자인지, 독립 개인정보처리자인지 또는 공동 개인정보처리자인지 구분합니다.",
        "GDPR 제4조 제7호, 제4조 제8호",
        [
            choice(
                "processor",
                "지시에 따라서만 처리한다. (예시 : 클라우드, CS, 물류 대행업체 등 위탁 처리)",
            ),
            choice(
                "controller",
                "수령자가 스스로 목적, 방법을 결정한다. (예시 : 현지 파트너사, 계열사, 마케팅 제휴사 등)",
            ),
        ],
        {"processor": "compliant", "controller": "compliant"},
    )
)
add(
    single_question(
        "gdpr_joint_controller_arrangement",
        "GDPR",
        section,
        "3. 공동 컨트롤러 약정",
        "(공동 컨트롤러에 해당하는 경우 답변) 책임 배분 약정을 체결하고 요지를 공개했는가?",
        "판단 포인트: 공동 개인정보처리자 구조라면 제26조 약정과 공개 여부를 확인합니다.",
        "GDPR 제26조",
        [
            choice("done", "체결 완료, 정보 주체에게 요지 공개함"),
            choice("missing", "체결 준비 중이거나 요지 미공개"),
            choice("na", "해당 없음(공동 컨트롤러 아님)"),
        ],
        {"done": "compliant", "missing": "violation", "na": "recommended"},
        visible_if=equals("gdpr_third_party_role", "controller"),
    )
)
add(
    single_question(
        "gdpr_third_party_purpose_compatibility",
        "GDPR",
        section,
        "4. 제3자 제공 목적의 양립 가능성",
        "이 제3자 제공 목적은 애초에 개인정보를 수집한 목적과 양립 가능한가?",
        "판단 포인트: 원래 수집 목적과 동일한지, 새 적법근거가 확보되었는지 확인합니다.",
        "GDPR 제6조 제4항",
        [
            choice("compatible", "원래 수집 목적과 동일하거나 양립 가능한 목적이다."),
            choice("new_basis", "원래 목적과 다르며, 별도의 새 적법근거를 확보했다."),
            choice(
                "not_reviewed", "원래 목적과 다른데 별도 근거는 아직 검토하지 않았다."
            ),
        ],
        {
            "compatible": "compliant",
            "new_basis": "compliant",
            "not_reviewed": "violation",
        },
        visible_if=equals("gdpr_third_party_role", "controller"),
    )
)
add(
    single_question(
        "gdpr_third_party_notification",
        "GDPR",
        section,
        "5. 수령자 통지 절차",
        "정보 주체가 삭제·정정을 요청하면, 이미 제공한 수령자에게도 그 사실을 통지할 절차가 있는가?",
        "판단 포인트: 삭제·정정 요청을 수령자에게도 전달할 프로세스가 있는지 확인합니다.",
        "GDPR 제19조",
        [choice("yes", "있다"), choice("no", "없다")],
        {"yes": "compliant", "no": "violation"},
        visible_if=equals("gdpr_third_party_role", "controller"),
    )
)
add(
    single_question(
        "gdpr_external_transfer_status",
        "GDPR",
        section,
        "6. 역외 재이전 여부",
        "수령자가 EU 역외에 있어 데이터가 EU 밖으로 재이전 되는가?",
        "판단 포인트: EU 역내 이전, 역외 이전 여부와 이전 수단 확보 상태를 확인합니다.",
        "GDPR 제44조~제49조",
        [
            choice("eu_only", "EU 역내 이전이라 해당 없다."),
            choice(
                "transfer_ready",
                "역외 재이전이며 SCC·적정성 결정 등 이전 수단을 확보했다.",
            ),
            choice(
                "transfer_missing", "역외 재이전인데 이전 수단을 아직 확보하지 않았다."
            ),
        ],
        {
            "eu_only": "recommended",
            "transfer_ready": "compliant",
            "transfer_missing": "violation",
        },
    )
)
add(
    single_question(
        "gdpr_external_transfer_special_categories",
        "GDPR",
        section,
        "7. 역외이전 시 특수범주 개인정보 여부",
        "국외로 이전하는 데이터 중, 건강·생체정보·성적지향·인종 등 특수 범주 개인정보가 포함되는가?",
        "판단 포인트: 제9조 특수범주 정보가 포함되면 추가 근거 확보 여부를 확인합니다.",
        "GDPR 제9조",
        [
            choice("no", "포함되지 않는다."),
            choice("yes_ready", "포함되며, 제9조②의 별도 근거를 확보했다."),
            choice("yes_missing", "포함되는데 별도 근거는 아직 확보하지 않았다."),
        ],
        {"no": "recommended", "yes_ready": "compliant", "yes_missing": "violation"},
    )
)

section = "4. 국외이전"
add(
    single_question(
        "gdpr_transfer_basic_lawful_basis",
        "GDPR",
        section,
        "4-2. 개인정보의 수집·이용·전달 자체에 GDPR 제6조의 적법근거가 있는가?",
        "개인정보의 수집·이용·전달 자체에 GDPR 제6조의 적법근거가 있는가?",
        "판단 포인트: 국외이전 수단과 별개로 기본 처리행위의 적법근거가 먼저 확보되어야 합니다.",
        "GDPR 제6조",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "compliant", "no": "violation"},
    )
)
add(
    single_question(
        "gdpr_transfer_mechanism",
        "GDPR",
        section,
        "4-3. 적용되는 국외이전 근거",
        "다음 중 적용되는 국외이전 근거가 있는가?",
        "판단 포인트: 적정성 결정, SCC, BCR, 제49조 예외 중 실제 적용 근거를 선택합니다.",
        "GDPR 제45조~제49조",
        [
            choice(
                "adequacy",
                "수령자가 EU 집행위원회가 개인정보 보호수준을 인정한 국가·기관에 있다.",
            ),
            choice("scc", "해외 수령업체와 EU 표준계약조항(SCC)을 체결했다."),
            choice(
                "bcr",
                "같은 기업집단 내부 이전이며, 감독기관이 승인한 기업구속규칙(BCR)을 적용한다.",
            ),
            choice(
                "derogation",
                "위 근거는 없지만, 명시적 동의·계약상 필요 등 제한적인 예외사유가 있다.",
            ),
            choice("unknown", "어느 항목에 해당하는지 확인할 수 없다."),
        ],
        {
            "adequacy": "compliant",
            "scc": "compliant",
            "bcr": "compliant",
            "derogation": "recommended",
            "unknown": "violation",
        },
    )
)
add(
    single_question(
        "gdpr_transfer_adequacy_scope",
        "GDPR",
        section,
        "4-4. 적정성 결정 적용범위 확인",
        "적정성 결정에 의존한다면 수령국·수령자·처리활동이 해당 결정의 적용범위에 포함되는가?",
        "판단 포인트: 적정성 결정 대상국, 수령자, 처리활동이 모두 범위 안에 있는지 확인합니다.",
        "GDPR 제45조",
        [choice("yes", "예"), choice("no", "아니요"), choice("na", "해당 없음")],
        {"yes": "compliant", "no": "insufficient", "na": "recommended"},
        visible_if=equals("gdpr_transfer_mechanism", "adequacy"),
    )
)
add(
    checklist_question(
        "gdpr_transfer_scc_alignment",
        "GDPR",
        section,
        "4-5. SCC 보호조치 확인",
        "제46조의 보호조치를 사용하는 경우, 다음 중 해당하는 사항을 확인했는가?",
        "판단 포인트: SCC 체결과 실제 이전 목적·정보 종류·수령자·처리방법의 일치 여부를 확인합니다.",
        "GDPR 제46조, 제47조",
        [
            choice("signed", "SCC를 사용하는 경우 해외 수령업체와 유효하게 체결했다."),
            choice(
                "aligned",
                "선택한 문서가 실제 이전 목적·정보 종류·수령자·처리방법과 일치한다.",
            ),
        ],
        required_values=["signed", "aligned"],
        visible_if=equals("gdpr_transfer_mechanism", "scc"),
    )
)
add(
    checklist_question(
        "gdpr_transfer_bcr_alignment",
        "GDPR",
        section,
        "4-5. BCR 보호조치 확인",
        "제47조의 보호조치를 사용하는 경우, 다음 중 해당하는 사항을 확인했는가?",
        "판단 포인트: BCR 승인과 실제 이전 목적·정보 종류·수령자·처리방법의 일치 여부를 확인합니다.",
        "GDPR 제47조",
        [
            choice("approved", "BCR을 사용하는 경우 감독기관의 승인을 받았다."),
            choice(
                "aligned",
                "선택한 문서가 실제 이전 목적·정보 종류·수령자·처리방법과 일치한다.",
            ),
        ],
        required_values=["approved", "aligned"],
        visible_if=equals("gdpr_transfer_mechanism", "bcr"),
    )
)
add(
    checklist_question(
        "gdpr_transfer_tia",
        "GDPR",
        section,
        "4-6. SCC 사용 시 이전영향평가(TIA)",
        "SCC를 사용하는 경우 이전영향평가(TIA)를 실시하고 필요한 보호조치를 마련했는가?",
        "판단 포인트: 수령국 법률·관행 평가, 보호수준 판단, 암호화·가명처리 등 보완조치, 정기 재평가를 확인합니다.",
        "GDPR 제46조, Schrems II 판결",
        [
            choice("law_review", "수령국의 법률·관행과 정부기관 접근 위험을 평가했다."),
            choice("protection_level", "SCC만으로 EU 수준의 보호가 가능한지 판단했다."),
            choice(
                "supplementary",
                "필요한 경우 암호화·가명처리·접근통제 등 보완조치를 적용했다.",
            ),
            choice("recheck", "보호수준을 정기적으로 재평가한다."),
            choice("suspend_if_needed", "충분한 보호가 불가능하면 이전을 중단한다."),
        ],
        required_values=[
            "law_review",
            "protection_level",
            "supplementary",
            "recheck",
            "suspend_if_needed",
        ],
        visible_if=equals("gdpr_transfer_mechanism", "scc"),
    )
)
add(
    grouped_checklist_question(
        "gdpr_transfer_derogation_requirements",
        "GDPR",
        section,
        "4-7. 제49조 예외 사용 요건",
        "제49조 예외를 사용한다면 일시적·예외적 상황이며 해당 예외의 엄격한 요건을 입증할 수 있는가?",
        "판단 포인트: 적어도 하나의 제49조 예외 사유와 공통 확인사항 3개를 함께 충족해야 합니다.",
        "GDPR 제49조",
        [
            choice("explicit_consent", "위험을 안내받은 정보주체의 명시적 동의"),
            choice(
                "contract_need",
                "정보주체와의 계약 또는 정보주체를 위한 계약 이행에 필요",
            ),
            choice("public_interest", "EU·회원국 법률이 인정하는 중요한 공익"),
            choice("legal_claim", "법적 청구권의 설정·행사·방어에 필요"),
            choice("vital_interest", "생명·신체 등 정보주체의 중대한 이익 보호"),
            choice("public_register", "법률상 공개된 공적 등록부에 근거"),
            choice(
                "compelling_interest",
                "그 밖의 예외가 불가능한 상황에서 비반복적·제한적인 이전을 위한 중대한 정당한 이익",
            ),
            choice("actual_fit", "선택한 예외가 실제 이전 상황에 적용된다."),
            choice("documented", "이전 필요성과 판단 근거를 문서화했다."),
            choice(
                "not_routine", "반복적·상시적 이전의 일반적인 근거로 사용하지 않는다."
            ),
        ],
        required_values=["actual_fit", "documented", "not_routine"],
        at_least_one_values=[
            "explicit_consent",
            "contract_need",
            "public_interest",
            "legal_claim",
            "vital_interest",
            "public_register",
            "compelling_interest",
        ],
        visible_if=equals("gdpr_transfer_mechanism", "derogation"),
    )
)
add(
    checklist_question(
        "gdpr_transfer_processor_contract",
        "GDPR",
        section,
        "4-8. 해외 수령업체 처리계약",
        "해외 수령업체가 처리수탁자인 경우, 제28조에 따른 처리계약이 체결되어 있는가?",
        "판단 포인트: 목적·기간·범위, 보안조치, 재위탁, 권리 지원, 종료 시 삭제·반환, 감사권을 확인합니다.",
        "GDPR 제28조, 제32조, 제44조",
        [
            choice("scope", "처리 목적·기간·범위와 개인정보 종류"),
            choice("security", "보안조치"),
            choice("subprocessors", "재위탁 및 후속 이전 통제"),
            choice("rights_support", "정보주체 권리 지원과 유출 대응"),
            choice("return_delete", "계약 종료 시 삭제·반환"),
            choice("audit", "감사·점검 권한"),
        ],
        required_values=[
            "scope",
            "security",
            "subprocessors",
            "rights_support",
            "return_delete",
            "audit",
        ],
        visible_if=equals("gdpr_third_party_role", "processor"),
    )
)
add(
    checklist_question(
        "gdpr_transfer_notice_requirements",
        "GDPR",
        section,
        "4-9. 처리방침 또는 수집 고지 포함사항",
        "처리방침 또는 수집 고지에 다음 사항이 포함되어 있는가?",
        "판단 포인트: 이전 국가, 수령자 범주, 목적, 개인정보 범주, 보호조치 사본 확인방법, 보유기간을 확인합니다.",
        "GDPR 제13조(1)(f), 제14조(1)(f), 제15조(2)",
        [
            choice("country_recipient", "이전 국가와 수령자 또는 수령자 범주"),
            choice("purpose_categories", "이전 목적과 개인정보 범주"),
            choice("basis_safeguards", "이전 근거와 보호조치"),
            choice("copy_method", "보호조치 사본의 확인방법"),
            choice("retention", "보유기간"),
        ],
        required_values=[
            "country_recipient",
            "purpose_categories",
            "basis_safeguards",
            "copy_method",
            "retention",
        ],
    )
)
add(
    single_question(
        "gdpr_transfer_documentation",
        "GDPR",
        section,
        "4-10. 국외이전 문서화 및 최신화",
        "국외이전 목록, 이전 근거, 계약, TIA, 보완조치 및 재검토 결과를 문서화하고 최신 상태로 유지하는가?",
        "판단 포인트: 책임성 입증 자료와 처리기록을 계속 업데이트하는지 확인합니다.",
        "GDPR 제5조(2), 제24조, 제30조",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "compliant", "no": "insufficient"},
    )
)

section = "5. 미성년자"
add(
    single_question(
        "gdpr_child_service",
        "GDPR",
        section,
        "5-1. 아동 대상 정보사회서비스 여부",
        "해당 서비스는 아동에게 직접 제공되는 정보사회서비스인가?",
        "판단 포인트: 아동 직접 서비스라면 제8조 검토가 필요합니다.",
        "GDPR 제8조",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "recommended", "no": "recommended"},
        action_hint="아동 대상 서비스라면 연령 기준과 보호자 동의 구조를 바로 이어서 점검하세요.",
    )
)
add(
    single_question(
        "gdpr_child_consent_basis",
        "GDPR",
        section,
        "5-2. 아동 개인정보 처리의 법적 근거가 동의인가?",
        "아동 개인정보 처리의 법적 근거가 동의인가?",
        "판단 포인트: 동의를 근거로 처리하는 경우 친권 책임자 동의 규정 검토가 이어집니다.",
        "GDPR 제6조, 제8조",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "recommended", "no": "recommended"},
        visible_if=equals("gdpr_child_service", "yes"),
        action_hint="동의가 아닌 다른 제6조 근거를 쓰더라도 그 적정성을 별도로 문서화하세요.",
    )
)
add(
    single_question(
        "gdpr_child_age_threshold",
        "GDPR",
        section,
        "5-3. 회원국별 디지털 동의 연령 확인",
        "서비스를 제공하는 각 회원국의 디지털 동의 연령을 확인했는가?",
        "판단 포인트: 회원국별 13~16세 기준 연령 차이를 반영했는지 확인합니다.",
        "GDPR 제8조(1)",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "compliant", "no": "violation"},
        visible_if=equals("gdpr_child_consent_basis", "yes"),
    )
)
add(
    single_question(
        "gdpr_child_parental_approval",
        "GDPR",
        section,
        "5-4. 친권 책임자 동의 또는 승인",
        "이용자가 해당 회원국의 기준 연령 미만이라면 친권 책임자의 동의 또는 승인을 받는가?",
        "판단 포인트: 기준 연령 미만 이용자에게 보호자 동의 흐름이 있는지 확인합니다.",
        "GDPR 제8조(1)",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "compliant", "no": "violation"},
        visible_if=equals("gdpr_child_consent_basis", "yes"),
    )
)
add(
    checklist_question(
        "gdpr_child_verification_process",
        "GDPR",
        section,
        "5-5. 연령과 친권 책임자 확인 절차",
        "연령과 친권 책임자 확인 절차가 다음 요건을 충족하는가?",
        "판단 포인트: 위험 비례성, 보호자 확인, 기록 보관, 우회 방지, 최소수집을 함께 확인합니다.",
        "GDPR 제8조(2), 제5조(1)(c)",
        [
            choice("proportional", "처리 위험에 비례한 확인"),
            choice("guardian_check", "친권 책임자 확인"),
            choice("logs", "확인기록 보관"),
            choice("anti_bypass", "우회·허위 입력 대응"),
            choice("minimise", "불필요한 신분정보 최소화"),
        ],
        required_values=[
            "proportional",
            "guardian_check",
            "logs",
            "anti_bypass",
            "minimise",
        ],
        visible_if=equals("gdpr_child_consent_basis", "yes"),
    )
)
add(
    checklist_question(
        "gdpr_child_consent_quality",
        "GDPR",
        section,
        "5-6. 아동 동의 품질",
        "동의가 다음 요건을 모두 충족하는가?",
        "판단 포인트: 자유로운 선택, 목적별 구분, 충분한 정보, 적극적 의사표시, 동의 입증과 쉬운 철회를 확인합니다.",
        "GDPR 제4조(11), 제7조",
        [
            choice("free", "자유로운 선택"),
            choice("purpose", "목적별 구분"),
            choice("info", "충분한 정보 제공"),
            choice("active", "적극적 의사표시"),
            choice("proof_withdraw", "동의 입증과 쉬운 철회"),
        ],
        required_values=["free", "purpose", "info", "active", "proof_withdraw"],
        visible_if=equals("gdpr_child_consent_basis", "yes"),
    )
)
add(
    single_question(
        "gdpr_child_plain_notice",
        "GDPR",
        section,
        "5-7. 연령에 맞는 평이한 안내문",
        "아동이 이해할 수 있도록 연령에 맞는 명확하고 평이한 안내문을 제공하는가?",
        "판단 포인트: 아동이 실제로 이해할 수 있는 표현으로 고지하는지 확인합니다.",
        "GDPR 제12조(1), 전문 제58항",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "compliant", "no": "insufficient"},
        visible_if=equals("gdpr_child_service", "yes"),
    )
)
add(
    single_question(
        "gdpr_child_rights_process",
        "GDPR",
        section,
        "5-8. 철회 및 정보주체 권리 절차",
        "아동이 동의를 철회하고 열람·정정·삭제 등 정보주체 권리를 행사할 수 있는 절차가 마련되어 있는가?",
        "판단 포인트: 아동이 이해하고 이용할 수 있는 권리행사 절차와 보호자 대리행사 범위를 확인합니다.",
        "GDPR 제7조(3), 제12조~제22조",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "compliant", "no": "insufficient"},
        visible_if=equals("gdpr_child_service", "yes"),
    )
)
add(
    grouped_checklist_question(
        "gdpr_child_special_categories",
        "GDPR",
        section,
        "5-9. 아동의 특별범주 개인정보 처리",
        "건강·생체·유전정보 등 아동의 특별범주 개인정보를 처리한다면 제9조 제2항의 예외근거와 필요한 보호조치가 있는가?",
        "판단 포인트: 특별범주 예외근거 중 하나 이상과 최소수집·접근제한·문서화를 함께 확인합니다.",
        "GDPR 제9조 제1항·제2항",
        [
            choice("explicit", "아동 또는 법정대리인의 명시적 동의"),
            choice("vital", "생명·신체 등 중대한 이익 보호"),
            choice("claims", "법적 청구권 행사 또는 법원의 사법작용"),
            choice("law_public", "법률에 근거한 고용·사회보장 또는 중대한 공익"),
            choice("medical", "의료·보건·사회복지 또는 공중보건 목적"),
            choice("research", "연구·통계·기록보존 목적 등 그 밖의 제9조 제2항 사유"),
            choice(
                "minimise",
                "처리 목적에 필요한 최소한의 정보만 수집하고 접근·보관을 제한했다.",
            ),
            choice("documented", "적용한 예외근거와 보호조치를 문서화했다."),
            choice("none", "특별범주 개인정보를 처리하지 않음"),
        ],
        required_values=["minimise", "documented"],
        at_least_one_values=[
            "explicit",
            "vital",
            "claims",
            "law_public",
            "medical",
            "research",
        ],
        none_value="none",
        none_status="recommended",
        visible_if=equals("gdpr_child_service", "yes"),
    )
)
add(
    checklist_question(
        "gdpr_child_privacy_notice",
        "GDPR",
        section,
        "5-10. 아동 대상 처리방침 포함사항",
        "아동 대상 처리방침에 다음 사항이 포함되어 있는가?",
        "판단 포인트: 대상 연령, 수집정보·목적, 법적근거, 보호자 확인, 광고·프로파일링, 제3자 제공·국외이전을 확인합니다.",
        "GDPR 제12조~제14조",
        [
            choice("age_scope", "대상 연령과 수집정보·목적"),
            choice("legal_basis", "처리의 법적근거"),
            choice("guardian", "보호자 확인과 철회·삭제 절차"),
            choice("ads_profile", "광고·프로파일링 여부"),
            choice("third_country", "제3자 제공과 국외이전"),
        ],
        required_values=[
            "age_scope",
            "legal_basis",
            "guardian",
            "ads_profile",
            "third_country",
        ],
        visible_if=equals("gdpr_child_service", "yes"),
    )
)

section = "6. 자동화된 결정"
add(
    single_question(
        "gdpr_admt_exists",
        "GDPR",
        section,
        "6-1. 프로파일링 또는 자동결정 수행 여부",
        "개인정보를 자동 분석하여 개인을 평가·예측하는 프로파일링 또는 자동 결정을 수행하는가?",
        "판단 포인트: 제22조 세부진단 대상이 되는 자동 분석·평가 기능이 있는지 확인합니다.",
        "GDPR 제4조(4), 제22조",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "recommended", "no": "recommended"},
    )
)
add(
    single_question(
        "gdpr_admt_solely_automated",
        "GDPR",
        section,
        "6-2. 오로지 자동 처리에 의존하는가?",
        "해당 결정이 오로지 자동 처리에 의존하며 실질적인 사람의 검토가 없는가?",
        "판단 포인트: 형식적 승인 수준이 아니라 실질적인 human review가 있는지 확인합니다.",
        "GDPR 제22조(1)",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "recommended", "no": "recommended"},
        visible_if=equals("gdpr_admt_exists", "yes"),
    )
)
add(
    multi_presence_question(
        "gdpr_admt_effects",
        "GDPR",
        section,
        "6-3. 자동결정의 영향 범위",
        "자동 결정이 다음 중 하나 이상의 영향을 미치는가?",
        "판단 포인트: 법적 효과, 경제·취업·교육·의료 등 중대한 영향, 서비스 기회 거절 여부를 확인합니다.",
        "GDPR 제22조(1), 전문 제71항",
        [
            choice("legal", "법적 효과"),
            choice("material", "경제·취업·교육·의료 등에 유사하게 중대한 영향"),
            choice("denial", "서비스 또는 기회의 실질적 거절"),
            choice("none", "해당 없음"),
        ],
        none_value="none",
        any_status="recommended",
        none_status="recommended",
        visible_if=equals("gdpr_admt_solely_automated", "yes"),
    )
)
add(
    multi_presence_question(
        "gdpr_admt_basis",
        "GDPR",
        section,
        "6-4. 자동결정을 허용하는 근거",
        "다음 중 자동결정을 허용하는 근거가 있는가?",
        "판단 포인트: 계약상 필요, 법률 허용, 명시적 동의 중 실제 근거를 확인합니다.",
        "GDPR 제22조(2)",
        [
            choice("contract", "계약 체결·이행에 필요"),
            choice("law", "EU 또는 회원국 법률이 허용"),
            choice("explicit", "정보주체의 명시적 동의"),
            choice("none", "미충족"),
        ],
        none_value="none",
        any_status="compliant",
        none_status="violation",
        visible_if=condition_all(
            equals("gdpr_admt_solely_automated", "yes"),
            excludes("gdpr_admt_effects", "none"),
        ),
        action_hint="자동결정을 계속 운영하려면 제22조 허용 근거를 명확히 특정하세요.",
    )
)
add(
    single_question(
        "gdpr_admt_contract_necessity",
        "GDPR",
        section,
        "6-5. 계약상 필요성 입증",
        "계약상 필요를 근거로 한다면 덜 침해적인 대안으로 계약을 이행할 수 없음을 입증할 수 있는가?",
        "판단 포인트: 단순 편의·효율성만으로는 계약상 필요성이 인정되기 어렵습니다.",
        "GDPR 제22조(2)(a)",
        [choice("yes", "예"), choice("no", "아니요"), choice("na", "해당 없음")],
        {"yes": "compliant", "no": "violation", "na": "recommended"},
        visible_if=includes("gdpr_admt_basis", "contract"),
    )
)
add(
    checklist_question(
        "gdpr_admt_rights",
        "GDPR",
        section,
        "6-6. 자동결정 대응 권리와 절차",
        "정보주체에게 자동결정에 대응할 수 있는 권리와 절차를 보장하는가?",
        "판단 포인트: 사람의 개입 요구, 의견 표현, 이의제기, 실질적 재검토, 정정·변경 가능성을 확인합니다.",
        "GDPR 제22조(3)",
        [
            choice("human", "사람의 개입을 요구할 수 있다."),
            choice("opinion", "자신의 의견을 표현할 수 있다."),
            choice("object", "자동결정에 이의를 제기할 수 있다."),
            choice("review", "이의제기 후 실질적인 재검토가 이루어진다."),
            choice("change", "오류가 확인되면 결과를 정정·변경할 수 있다."),
        ],
        required_values=["human", "opinion", "object", "review", "change"],
        visible_if=condition_all(
            equals("gdpr_admt_solely_automated", "yes"),
            excludes("gdpr_admt_effects", "none"),
        ),
    )
)
add(
    single_question(
        "gdpr_admt_human_review",
        "GDPR",
        section,
        "6-7. 검토자의 실효적 권한",
        "검토자가 자동 결과를 독립적으로 검토하고 변경할 실제 권한과 능력을 갖는가?",
        "판단 포인트: 사람 검토가 형식적 승인에 머물지 않는지 확인합니다.",
        "GDPR 제22조(1), (3)",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "compliant", "no": "violation"},
        visible_if=equals("gdpr_admt_solely_automated", "yes"),
    )
)
add(
    checklist_question(
        "gdpr_admt_notice_contents",
        "GDPR",
        section,
        "6-8. 고지문과 열람 답변 포함사항",
        "고지문과 열람 답변에 다음 사항이 포함되어 있는가?",
        "판단 포인트: 자동결정 존재, 주요 판단요소, 의미 있는 논리, 예상 결과, 사람 개입 및 문의 절차를 확인합니다.",
        "GDPR 제13조(2)(f), 제14조(2)(g), 제15조(1)(h)",
        [
            choice("existence", "자동결정의 존재와 주요 판단요소"),
            choice("logic", "의미 있는 논리정보"),
            choice("impact", "결정의 중요성과 예상 결과"),
            choice("human_object", "사람의 개입과 이의제기 방법"),
            choice("contact", "문의·재검토 절차"),
        ],
        required_values=["existence", "logic", "impact", "human_object", "contact"],
        visible_if=equals("gdpr_admt_exists", "yes"),
    )
)
add(
    single_question(
        "gdpr_admt_special_categories",
        "GDPR",
        section,
        "6-9. 특별범주 개인정보 사용 여부와 근거",
        "특별범주 개인정보를 자동결정에 사용한다면 명시적 동의 또는 중대한 공익 근거와 적절한 보호조치가 있는가?",
        "판단 포인트: 특별범주 정보가 자동결정에 쓰이면 제9조와 제22조(4) 근거를 함께 확인합니다.",
        "GDPR 제9조, 제22조(4)",
        [choice("yes", "예"), choice("no", "아니요"), choice("na", "해당 없음")],
        {"yes": "compliant", "no": "violation", "na": "recommended"},
        visible_if=equals("gdpr_admt_exists", "yes"),
    )
)
add(
    checklist_question(
        "gdpr_admt_risk_controls",
        "GDPR",
        section,
        "6-10. 자동화 처리 위험평가와 보호조치",
        "자동화 처리의 위험을 평가하고 필요한 보호조치를 적용했는가?",
        "판단 포인트: DPIA 검토, 정확성·오류관리, 편향 점검, 최소화·보안·정기 재평가를 확인합니다.",
        "GDPR 제5조, 제25조, 제35조",
        [
            choice("dpia_check", "DPIA 필요 여부를 검토했다."),
            choice(
                "dpia_done",
                "고위험 처리에 해당하면 개인정보보호 영향평가(DPIA)를 실시했다.",
            ),
            choice("accuracy", "정확성을 검증하고 오류를 관리한다."),
            choice("bias", "차별·편향 가능성을 평가한다."),
            choice(
                "security_review", "데이터 최소화·보안·정기 재평가 조치를 적용한다."
            ),
        ],
        required_values=[
            "dpia_check",
            "dpia_done",
            "accuracy",
            "bias",
            "security_review",
        ],
        visible_if=equals("gdpr_admt_exists", "yes"),
    )
)

section = "7. 쿠키"
add(
    single_question(
        "gdpr_cookie_usage",
        "GDPR",
        section,
        "7-1. 쿠키·SDK·픽셀 등 사용 여부",
        "웹·앱이 이용자 단말기에 정보를 저장하거나 접근하는 쿠키·SDK·픽셀·로컬스토리지 등을 사용하는가?",
        "판단 포인트: ePrivacy Directive 제5조(3) 대상이 되는 추적기술 사용 여부를 확인합니다.",
        "ePrivacy Directive 제5조(3)",
        [choice("yes", "예"), choice("no", "아니요")],
        {"yes": "recommended", "no": "recommended"},
    )
)
add(
    multi_presence_question(
        "gdpr_cookie_classification",
        "GDPR",
        section,
        "7-2. 추적기술 분류",
        "각 추적기술을 실제 기능과 목적에 따라 분류했는가?",
        "판단 포인트: 통신 필수, 엄격히 필요, 기능·편의, 분석, 광고·프로파일링·소셜미디어로 분류했는지 확인합니다.",
        "ePrivacy Directive 제5조(3)",
        [
            choice("communication", "통신에 필수"),
            choice("strictly_necessary", "이용자가 요청한 서비스에 엄격히 필요"),
            choice("functional", "기능·편의"),
            choice("analytics", "분석"),
            choice("ads", "광고·프로파일링·소셜미디어"),
        ],
        any_status="compliant",
        none_status="insufficient",
        visible_if=equals("gdpr_cookie_usage", "yes"),
    )
)
for question_id, title, prompt, legal_basis, yes_status, no_status in [
    (
        "gdpr_cookie_only_necessary",
        "7-3. 동의 없이 실행되는 추적기술 제한",
        "동의 없이 실행되는 추적기술이 엄격히 필요한 항목으로만 제한되는가?",
        "ePrivacy Directive 제5조(3)",
        "compliant",
        "violation",
    ),
    (
        "gdpr_cookie_prior_consent",
        "7-4. 선택적 추적기술의 사전 동의",
        "분석·광고 등 선택적 추적기술은 이용자의 사전 동의 후에만 설치·작동하는가?",
        "ePrivacy Directive 제5조(3), GDPR 제6조·제7조",
        "compliant",
        "violation",
    ),
    (
        "gdpr_cookie_reject_withdraw",
        "7-6. 모두 거부·철회 접근성",
        "첫 화면의 '모두 거부'가 '모두 동의'와 유사한 접근성으로 제공되고, 동의 후에도 동일한 수준으로 쉽게 철회할 수 있는가?",
        "GDPR 제5조(1)(a), 제7조(3)",
        "compliant",
        "insufficient",
    ),
    (
        "gdpr_cookie_third_party_roles",
        "7-8. 제3자 광고·분석업체 역할·근거 확인",
        "제3자 광고·분석업체로 개인정보를 전달하는 경우 해당 업체의 역할·처리목적·적법근거를 확인했는가?",
        "GDPR 제6조·제13조·제26조·제28조",
        "compliant",
        "violation",
    ),
    (
        "gdpr_cookie_international_transfer",
        "7-9. 쿠키·SDK 국외이전 보호조치",
        "쿠키·SDK를 통해 개인정보가 EU·EEA 밖으로 전송되는 경우 유효한 국외이전 근거와 보호조치가 있는가?",
        "GDPR 제44조~제49조",
        "compliant",
        "violation",
    ),
    (
        "gdpr_cookie_logs",
        "7-10. 동의 로그 보관",
        "동의 로그에 동의 시점, 정책 버전, 선택한 목적 및 철회 내역을 보관하는가?",
        "GDPR 제5조(2), 제7조(1)",
        "compliant",
        "insufficient",
    ),
]:
    choices = [choice("yes", "예"), choice("no", "아니요")]
    if question_id in {
        "gdpr_cookie_third_party_roles",
        "gdpr_cookie_international_transfer",
    }:
        choices.append(choice("na", "해당 없음"))
        status_map = {"yes": yes_status, "no": no_status, "na": "recommended"}
    else:
        status_map = {"yes": yes_status, "no": no_status}
    add(
        single_question(
            question_id,
            "GDPR",
            section,
            title,
            prompt,
            "판단 포인트: 쿠키 동의, 고지, 제3자 전달, 국외이전, 동의 로그까지 실제 작동 기준으로 확인합니다.",
            legal_basis,
            choices,
            status_map,
            visible_if=equals("gdpr_cookie_usage", "yes"),
        )
    )
add(
    checklist_question(
        "gdpr_cookie_consent_quality",
        "GDPR",
        section,
        "7-5. 쿠키 동의 요건",
        "쿠키 동의가 다음 요건을 모두 충족하는가?",
        "판단 포인트: 사전 체크 금지, 적극적 선택, 목적별 선택, 충분한 정보, 자유로운 거부와 동의 증빙을 확인합니다.",
        "GDPR 제4조(11), 제7조, Planet49",
        [
            choice("no_precheck", "사전 체크 없음"),
            choice("active", "이용자의 적극적 선택"),
            choice("purpose_split", "목적별 선택"),
            choice("info", "충분한 정보 제공"),
            choice("reject_proof", "자유로운 거부와 동의 증빙"),
        ],
        required_values=[
            "no_precheck",
            "active",
            "purpose_split",
            "info",
            "reject_proof",
        ],
        visible_if=equals("gdpr_cookie_usage", "yes"),
    )
)
add(
    checklist_question(
        "gdpr_cookie_policy_accuracy",
        "GDPR",
        section,
        "7-7. 쿠키 정책과 실제 작동 결과의 일치",
        "쿠키 정책의 내용이 실제 작동 결과와 일치하는가?",
        "판단 포인트: 명칭·제공자·목적, 수집정보·보유기간, 제3자 제공 여부, 법적근거·철회방법, 실제 스캔 결과 일치를 확인합니다.",
        "GDPR 제5조(1)(a), 제12조·제13조, ePrivacy Directive 제5조(3)",
        [
            choice(
                "name_provider_purpose",
                "쿠키·추적기술의 명칭·제공자·목적이 기재되어 있다.",
            ),
            choice("data_retention", "수집정보와 작동·보유기간이 기재되어 있다."),
            choice("third_party", "제3자 제공 여부가 기재되어 있다."),
            choice("basis_withdraw", "법적근거와 동의 철회방법이 안내되어 있다."),
            choice(
                "matches_scan",
                "정책 내용이 실제 스캔 및 네트워크 전송 결과와 일치한다.",
            ),
        ],
        required_values=[
            "name_provider_purpose",
            "data_retention",
            "third_party",
            "basis_withdraw",
            "matches_scan",
        ],
        visible_if=equals("gdpr_cookie_usage", "yes"),
    )
)

section = "0. CCPA 고유 부가 문항"
add(
    single_question(
        "ccpa_nondiscrimination",
        "CCPA",
        section,
        "0-1. 차별금지·인센티브",
        "권리 행사 소비자에게 서비스 거부·가격 차등·품질 저하 등 불이익을 부과하지 않으며, 인센티브 제공 시 합리적 관련성 근거가 있는가?",
        "판단 포인트: 권리 행사 소비자에 대한 차별 금지와 인센티브 가치 근거를 확인합니다.",
        "CCPA §1798.125",
        [
            choice("no", "아니오 (불이익 부과)"),
            choice("yes", "예 (차별 없음, 또는 근거자료 구비)"),
        ],
        {"yes": "compliant", "no": "violation"},
    )
)
add(
    single_question(
        "ccpa_opt_out_link",
        "CCPA",
        section,
        "0-2. 옵트아웃 링크 게시",
        "'내 개인정보 판매·공유 거부(Do Not Sell/Share My Personal Information)'와 '민감 개인정보 이용 제한(Limit the Use of My Sensitive Personal Information)' 링크를 게시하거나, GPC 신호를 수용하고 있는가?",
        "판단 포인트: 외부 노출되는 옵트아웃 링크 또는 GPC 수용 구조를 확인합니다.",
        "CCPA §1798.135(a)(1)(2)(3), (b)",
        [choice("no", "아니오"), choice("yes", "예")],
        {"yes": "compliant", "no": "violation"},
    )
)
add(
    single_question(
        "ccpa_incentive_program",
        "CCPA",
        section,
        "0-3. 경제적 인센티브 프로그램 운영 여부",
        "멤버십·포인트·할인 등 개인정보 제공을 조건으로 혜택을 주는 프로그램을 운영하는가?",
        "판단 포인트: 프로그램이 있으면 주요 조건, 가치 산정, 탈퇴 방법 고지가 이어집니다.",
        "CCPA §1798.125(b)",
        [choice("no", "아니오"), choice("yes", "예")],
        {"yes": "recommended", "no": "recommended"},
    )
)
add(
    checklist_question(
        "ccpa_incentive_program_notice",
        "CCPA",
        section,
        "0-3 세부. 경제적 인센티브 프로그램 고지",
        "경제적 인센티브 프로그램을 운영한다면 다음 사항이 방침에 기재되어 있는가?",
        "판단 포인트: 주요 조건, 개인정보 가치 산정 방식, 탈퇴 방법 안내를 확인합니다.",
        "CCPA §1798.125(b)(2), (3)",
        [
            choice("terms", "방침에 해당 프로그램의 주요 조건이 기재되어 있다"),
            choice(
                "value_method", "방침에 '개인정보의 가치' 산정 방식이 설명되어 있다"
            ),
            choice("withdraw", "방침에 프로그램 탈퇴 방법이 안내되어 있다"),
        ],
        required_values=["terms", "value_method", "withdraw"],
        visible_if=equals("ccpa_incentive_program", "yes"),
    )
)
add(
    single_question(
        "ccpa_internal_process",
        "CCPA",
        section,
        "0-4. 내부 체계",
        "소비자 요청에 대응하는 담당자가 지정되고 CCPA 절차에 대한 교육 체계가 마련되어 있는가?",
        "판단 포인트: 정책 문구뿐 아니라 요청 처리 조직과 교육 체계가 있는지 확인합니다.",
        "CCPA 내부 대응 체계",
        [choice("no", "아니오"), choice("yes", "예")],
        {"yes": "compliant", "no": "insufficient"},
    )
)

section = "1. 개인정보의 범위"
add(
    single_question(
        "ccpa_consumer_scope",
        "CCPA",
        section,
        "1-1. 캘리포니아 소비자 해당 여부",
        "해당 정보가 특정 캘리포니아 소비자 또는 가구를 식별·관련·설명·결부하거나 합리적으로 연결될 수 있는가?",
        "판단 포인트: 개인뿐 아니라 가구 단위와 연결 가능한 정보인지 확인합니다.",
        "CCPA §1798.140(v)",
        [choice("yes", "예"), choice("no", "아니오"), choice("unsure", "확인 필요")],
        {"yes": "compliant", "no": "recommended", "unsure": "insufficient"},
    )
)
for question_id, title, prompt, description, choices in [
    (
        "ccpa_scope_identifiers",
        "1-2. 식별정보 수집 여부",
        "다음과 같은 CCPA상 식별정보를 수집·생성·보유하는가?",
        "판단 포인트: 이름, 연락처, 온라인 식별자, 광고식별자를 구체적으로 식별합니다.",
        [
            choice("name", "이름"),
            choice("email", "이메일"),
            choice("postal", "우편주소"),
            choice("username", "계정명"),
            choice("phone", "전화번호"),
            choice("personal_id", "고유 개인 식별자"),
            choice("online", "온라인 식별자"),
            choice("ip", "IP 주소"),
            choice("cookie", "쿠키 식별자"),
            choice("device", "기기 식별자"),
            choice("ad_id", "광고 식별자"),
            choice("no", "해당 없음"),
        ],
    ),
    (
        "ccpa_scope_activity",
        "1-3. 활동정보 처리 여부",
        "특정 소비자와 연결되는 다음과 같은 활동정보를 처리하는가?",
        "판단 포인트: 방문 페이지, 검색, 클릭, 광고 상호작용, 세션·네트워크 활동정보를 식별합니다.",
        [
            choice("page", "방문한 웹사이트/페이지"),
            choice("search", "검색 기록"),
            choice("click", "클릭 기록"),
            choice("ad", "광고 노출·상호작용"),
            choice("service_use", "앱 또는 서비스 이용기록"),
            choice("browsing", "브라우징 기록"),
            choice("session", "접속·세션 정보"),
            choice("network", "네트워크 활동정보"),
            choice("no", "해당 없음"),
        ],
    ),
    (
        "ccpa_scope_location",
        "1-4. 위치정보 수집 여부",
        "소비자와 연결되는 위치정보를 수집하는가?",
        "판단 포인트: GPS, 주소/IP 기반 위치, 이동경로, 위치이력을 식별합니다.",
        [
            choice("gps", "GPS"),
            choice("latlng", "위도·경도"),
            choice("address", "주소 기반 위치"),
            choice("ip", "IP 기반 위치"),
            choice("route", "이동경로"),
            choice("place", "방문 장소"),
            choice("history", "위치이력"),
            choice("other", "기타 지리적 위치정보"),
            choice("no", "해당 없음"),
        ],
    ),
    (
        "ccpa_scope_service_use",
        "1-5. 상품·서비스 이용정보 수집 여부",
        "소비자의 상품·서비스 이용과 관련된 정보를 수집하는가?",
        "판단 포인트: 구매, 주문, 구독, 거래, 소비 성향, 이용이력을 식별합니다.",
        [
            choice("purchase", "구매내역"),
            choice("order", "주문내역"),
            choice("subscription", "구독내역"),
            choice("transaction", "거래정보"),
            choice("propensity", "구매·소비 성향"),
            choice("history", "상품·서비스 이용 이력"),
            choice("no", "해당 없음"),
        ],
    ),
    (
        "ccpa_scope_inferences",
        "1-6. 추론정보·프로파일링 여부",
        "기존 데이터를 분석하여 소비자의 특성·성향·선호·행동 등을 추론하거나 프로파일을 생성하는가?",
        "판단 포인트: 관심사, 세그먼트, 광고 타겟, 추천 프로파일, 예측 정보를 식별합니다.",
        [
            choice("interest", "관심사"),
            choice("preference", "선호도"),
            choice("purchase", "구매성향"),
            choice("churn", "이탈 가능성"),
            choice("segment", "고객 세그먼트"),
            choice("ad_target", "광고 타겟"),
            choice("recommendation", "추천 프로파일"),
            choice("estimate", "소비자 성향 추정"),
            choice("prediction", "AI/ML 기반 예측"),
            choice("no", "해당 없음"),
        ],
    ),
    (
        "ccpa_scope_sensitive",
        "1-7. 민감정보 수집 여부",
        "다음 중 하나에 해당하는 정보를 수집하는가?",
        "판단 포인트: 민감 개인정보 범주에 해당하는 정부 식별번호, 로그인정보, 정밀위치, 건강·생체정보 등을 식별합니다.",
        [
            choice("gov_id", "정부 식별번호"),
            choice("login", "계정 로그인정보+비밀번호/접근정보"),
            choice("precise_location", "정밀 위치정보"),
            choice("race", "인종·민족"),
            choice("citizenship", "시민권·이민 지위"),
            choice("belief", "종교·철학적 신념"),
            choice("union", "노동조합 가입"),
            choice("comm", "특정 통신 내용"),
            choice("genetic", "유전정보"),
            choice("neural", "신경 데이터"),
            choice("biometric", "생체정보"),
            choice("health", "건강정보"),
            choice("sex", "성생활"),
            choice("no", "해당 없음"),
        ],
    ),
    (
        "ccpa_scope_exemptions",
        "1-8. PI 제외 법정 예외 해당 여부",
        "해당 데이터를 CCPA상 PI에서 제외할 수 있는 법정 예외에 해당하는가?",
        "판단 포인트: 공개 사용 가능 정보, 비식별 정보, 총계정보 예외 적용 여부를 확인합니다.",
        [
            choice("public", "정부 기록 등 공개 사용 가능 정보"),
            choice("deidentified", "비식별 정보"),
            choice("aggregate", "총계정보"),
            choice("none", "해당 없음"),
        ],
    ),
]:
    add(
        multi_presence_question(
            question_id,
            "CCPA",
            section,
            title,
            prompt,
            description,
            "CCPA §1798.140(v)(1)",
            choices,
            none_value="no"
            if any(option["value"] == "no" for option in choices)
            else "none",
            any_status="compliant",
            none_status="compliant",
        )
    )
add(
    single_question(
        "ccpa_scope_reidentification",
        "CCPA",
        section,
        "1-9. 재식별 가능성",
        "데이터에서 이름 등을 제거했지만 다른 정보나 별도 키를 이용하면 특정 소비자와 다시 연결할 수 있는가?",
        "판단 포인트: 가명화 또는 비식별 처리가 실제로 재식별 가능한지 확인합니다.",
        "CCPA §1798.140(m), (h), (v)",
        [choice("yes", "예"), choice("no", "아니오"), choice("unsure", "확인 필요")],
        {"yes": "recommended", "no": "compliant", "unsure": "insufficient"},
    )
)

section = "2. 개인정보의 수집·이용"
for question_id, title, prompt, legal_basis, yes_status, no_status in [
    (
        "ccpa_notice_at_collection",
        "2-1. 수집시점 고지",
        "개인정보 수집 시점(또는 그 이전)에 카테고리·목적·판매공유여부·보유기간을 소비자에게 고지하고 있는가?",
        "CCPA §1798.100(a), §1798.130(a)(5)",
        "compliant",
        "violation",
    ),
    (
        "ccpa_new_purpose_notice",
        "2-2. 목적확장 통제",
        "고지되지 않은 새로운 목적으로 기존 개인정보를 이용하려는 경우, 재고지 절차가 마련되어 있는가?",
        "CCPA 목적 제한 원칙",
        "compliant",
        "violation",
    ),
    (
        "ccpa_legal_category_labels",
        "2-5. 카테고리 표기 방식",
        "방침에 개인정보 카테고리를 법정 용어(11개 A~K)로 표기하고 있는가, 자체 용어나 포괄 표현을 쓰고 있지는 않은가?",
        "CCPA §1798.130(a)(5)",
        "compliant",
        "violation",
    ),
    (
        "ccpa_consent_dark_patterns",
        "2-7. 동의를 사용하는 경우",
        "'동의'를 표시·활용하는 경우, 자유의사·구체적·정보제공 기반·모호하지 않은 표시라는 법정 요건을 충족하며 다크패턴은 없는가?",
        "CCPA §1798.140(h), (l)",
        "compliant",
        "violation",
    ),
    (
        "ccpa_retention_exceptions",
        "2-9. 계속이용 근거",
        "삭제요청을 받았음에도 계속 보유·이용하는 경우, 해당 예외사유의 법적 근거를 명확히 기록하고 있는가?",
        "CCPA §1798.105(d)",
        "compliant",
        "violation",
    ),
    (
        "ccpa_business_purpose",
        "2-10. 사업목적 이용",
        "개인정보 이용목적이 법정 사업목적 범위 내에 있으며, '수집' 해당 여부를 판단하여 처리하고 있는가?",
        "CCPA §1798.140(e)(f)",
        "compliant",
        "violation",
    ),
]:
    add(
        single_question(
            question_id,
            "CCPA",
            section,
            title,
            prompt,
            "판단 포인트: 고지, 목적 제한, 카테고리 표기, 삭제 예외 기록, 사업목적 정의와 실제 운영의 일치를 확인합니다.",
            legal_basis,
            [choice("no", "아니오"), choice("yes", "예")],
            {"yes": yes_status, "no": no_status},
        )
    )
add(
    single_question(
        "ccpa_data_minimisation",
        "CCPA",
        section,
        "2-3. 비례·최소수집",
        "수집 항목이 고지된 목적 달성에 합리적으로 필요한 최소 범위로 제한되어 있는가?",
        "판단 포인트: 목적 대비 과다수집인지, 일부 초과인지, 충족인지 구분합니다.",
        "CCPA 비례성·목적 제한 원칙",
        [
            choice("excessive", "과다수집"),
            choice("partial", "일부 초과(선택값 미분리)"),
            choice("good", "충족"),
        ],
        {"excessive": "violation", "partial": "recommended", "good": "compliant"},
    )
)
add(
    checklist_question(
        "ccpa_policy_contents",
        "CCPA",
        section,
        "2-4. 방침 기재사항",
        "방침에 다음 필수 기재사항이 포함되어 있는가?",
        "판단 포인트: 권리 설명, 접수방법, 최근 12개월 수집 카테고리, 출처, 목적, 제3자 유형, 판매·공유 카테고리, 12개월 갱신 여부를 확인합니다.",
        "CCPA §1798.130(a)(5)(A)(B)(C), §1798.110(c)",
        [
            choice("rights", "권리설명 + 접수방법이 방침에 기재되어 있다"),
            choice(
                "categories",
                "최근 12개월간 수집한 개인정보의 카테고리가 방침에 기재되어 있다",
            ),
            choice(
                "sources", "그 개인정보를 수집한 출처(카테고리)가 방침에 기재되어 있다"
            ),
            choice(
                "purposes", "수집·판매·공유의 사업상·상업적 목적이 방침에 기재되어 있다"
            ),
            choice(
                "third_parties",
                "개인정보를 제공받는 제3자의 유형이 방침에 기재되어 있다",
            ),
            choice(
                "sold_shared",
                "최근 12개월간 판매·공유한 개인정보 카테고리가 있고, 없다면 '없음'이 명시되어 있다",
            ),
            choice("fresh", "위 내용이 12개월 이내에 갱신되었다"),
        ],
        required_values=[
            "rights",
            "categories",
            "sources",
            "purposes",
            "third_parties",
            "sold_shared",
        ],
        recommended_values=["fresh"],
    )
)
add(
    single_question(
        "ccpa_request_process",
        "CCPA",
        section,
        "2-6. 요청처리 절차",
        "접수채널 2개 이상(웹+전화/이메일), 45일 처리기한(1회 연장 가능), 연 2회 제한, 알권리·열람권 행사 시 직전 12개월분 공개가 모두 갖춰져 있는가?",
        "판단 포인트: 채널 수, 처리기한, 연장 규칙, 공개 범위를 함께 확인합니다.",
        "CCPA §1798.130(a)(1)(2)",
        [
            choice("missing", "미비 (접수채널 1개 이하, 처리기한 규정 없음)"),
            choice("partial", "일부 미비 (일부 요건 누락)"),
            choice("good", "충족"),
        ],
        {"missing": "violation", "partial": "insufficient", "good": "compliant"},
    )
)
add(
    single_question(
        "ccpa_sensitive_use_limit",
        "CCPA",
        section,
        "2-8. 민감정보 이용제한",
        "민감 개인정보를 수집하는 경우, 소비자가 이용제한권을 실제로 행사할 수 있는 수단이 마련되어 있는가?",
        "판단 포인트: 민감 개인정보를 수집한다면 이용 제한 경로와 실제 제한 수단이 있는지 확인합니다.",
        "CCPA §1798.121",
        [
            choice("no", "아니오"),
            choice("yes", "예"),
            choice("na", "해당 없음(민감 개인정보 미수집)"),
        ],
        {"no": "violation", "yes": "compliant", "na": "compliant"},
    )
)

section = "3. 제3자 제공"
add(
    multi_presence_question(
        "ccpa_track_a_detection",
        "CCPA",
        section,
        "Q-A. 광고·마케팅 목적 행위",
        "아래 중 해당하는 것을 모두 선택하세요.",
        "판단 포인트: 판매·공유 판별이 필요한 광고·마케팅 행위를 먼저 식별합니다.",
        "CCPA §1798.120, §1798.130(a)(5)(C), §1798.135",
        [
            choice("retargeting", "사이트·앱 방문자 대상 리타겟팅 광고"),
            choice("cart", "장바구니 이탈자 리마인드 광고"),
            choice("lookalike", "룩얼라이크 광고"),
            choice("upload", "고객목록 광고플랫폼 업로드"),
            choice("analytics_link", "분석데이터-광고계정 연동 타겟팅"),
            choice("conversion_api", "서버-광고플랫폼 직접 전송(전환 API 등)"),
            choice("benefit", "개인정보 제공 후 금전·혜택 수령"),
            choice("none", "해당 없음"),
            choice("unsure", "잘 모르겠음"),
        ],
        none_value="none",
        any_status="recommended",
        none_status="recommended",
        action_hint="광고·마케팅 데이터 흐름을 먼저 판별한 뒤 방침, 옵트아웃, GPC 대응을 연결하세요.",
    )
)
add(
    single_question(
        "ccpa_track_b_detection",
        "CCPA",
        section,
        "Q-B. 위탁업체 존재 여부",
        "광고 목적 외에, 개인정보가 나가는 외부 업체가 있는가?",
        "판단 포인트: 클라우드, 결제, 배송, CS, 이메일·문자, 분석도구 등 위탁업체 존재 여부를 확인합니다.",
        "CCPA §1798.130(a)(5)(B)(iv)(C)",
        [choice("no", "아니오"), choice("yes", "예")],
        {"yes": "recommended", "no": "recommended"},
    )
)
add(
    checklist_question(
        "ccpa_track_a_policy_lists",
        "CCPA",
        section,
        "트랙 A. 판매·공유 방침 기재",
        "Q-A에서 하나라도 해당하는 경우, 다음 항목이 방침에 반영되어 있는가?",
        "판단 포인트: 최근 12개월 판매·공유 카테고리 목록, 위탁 목록 분리, 상대방 유형 분류, 판매·공유 여부 표기를 확인합니다.",
        "CCPA §1798.130(a)(5)(C)(i), §1798.100(a)(1)",
        [
            choice(
                "a1",
                "방침에 '최근 12개월간 판매·공유한 개인정보 카테고리' 목록이 별도로 있다",
            ),
            choice("a2", "판매·공유 목록과 위탁 목록이 구분되어 있다"),
            choice("a3", "제공받는 상대방이 기능별 유형으로 분류되어 있다"),
            choice("a4", "카테고리 표에 '판매·공유 여부'가 표기되어 있다"),
        ],
        required_values=["a1", "a2", "a3", "a4"],
        visible_if=condition_all(
            excludes("ccpa_track_a_detection", "none"),
            excludes("ccpa_track_a_detection", "unsure"),
        ),
    )
)
add(
    checklist_question(
        "ccpa_track_a_opt_out_contents",
        "CCPA",
        section,
        "트랙 A. 옵트아웃 기재",
        "Q-A에서 하나라도 해당하는 경우, 옵트아웃 관련 항목이 갖춰져 있는가?",
        "판단 포인트: 홈페이지 링크, 실제 작동, 방침 본문 기재, GPC 진술, 계정 없는 신청, 기능 제한 안내, 잘못된 '한국 동의로 대체' 문구 유무를 확인합니다.",
        "CCPA §1798.135(a)(1)(3), (b), (c)(1)(2), §1798.120(a), §1798.192",
        [
            choice("link_home", "홈페이지에 옵트아웃 링크가 있다"),
            choice("link_works", "옵트아웃 링크가 실제로 작동한다"),
            choice("policy_link", "방침 본문 안에도 옵트아웃 권리 설명과 링크가 있다"),
            choice("gpc", "방침에 GPC 등 옵트아웃 선호신호를 수용한다는 진술이 있다"),
            choice("no_account", "방침에 계정 없이도 옵트아웃할 수 있다는 안내가 있다"),
            choice(
                "feature_limit",
                "방침에 옵트아웃 시 일부 기능 제한 가능성이 안내되어 있다",
            ),
            choice(
                "korea_override",
                "방침에 '한국에서 동의를 받았으므로 별도 절차가 불필요하다'는 취지의 기재가 있다",
            ),
        ],
        required_values=["link_home", "link_works", "policy_link", "gpc"],
        recommended_values=["no_account", "feature_limit"],
        forbidden_values=["korea_override"],
        visible_if=condition_all(
            excludes("ccpa_track_a_detection", "none"),
            excludes("ccpa_track_a_detection", "unsure"),
        ),
        action_hint="옵트아웃 링크와 GPC 지원이 실제로 동작하는지 페이지와 처리 로직 양쪽에서 맞추세요.",
    )
)
add(
    checklist_question(
        "ccpa_track_a_request_contents",
        "CCPA",
        section,
        "트랙 A. 요청 절차 기재",
        "Q-A에서 하나라도 해당하는 경우, 요청 절차 안내가 갖춰져 있는가?",
        "판단 포인트: 대리인 신청 방법, 본인확인 정보, 답변기한 안내를 확인합니다.",
        "CCPA §1798.135(e), §1798.130(a)(2)(A), §1798.140(ak)",
        [
            choice(
                "agent",
                "대리인(가족·변호사 등)이 대신 옵트아웃을 신청하는 방법이 안내되어 있다",
            ),
            choice(
                "verify",
                "요청 시 본인 확인을 위해 어떤 정보를 요구하는지 안내되어 있다",
            ),
            choice("deadline", "요청 접수 후 며칠 안에 답변하는지 안내되어 있다"),
        ],
        required_values=["deadline"],
        recommended_values=["agent", "verify"],
        visible_if=condition_all(
            excludes("ccpa_track_a_detection", "none"),
            excludes("ccpa_track_a_detection", "unsure"),
        ),
    )
)
add(
    single_question(
        "ccpa_track_aprime_no_sale_statement",
        "CCPA",
        section,
        "트랙 A'. 판매·공유 없음 명시",
        "방침에 '당사는 개인정보를 판매하거나 공유하지 않습니다'가 눈에 띄게 명시되어 있는가?",
        "판단 포인트: 광고·마케팅 목적 행위가 전부 해당 없음인 경우에도 명시적 부존재 진술을 확인합니다.",
        "CCPA §1798.130(a)(5)(C)(i)",
        [
            choice("missing", "명시 없음(섹션 자체 부재)"),
            choice("visible", "눈에 띄게 명시"),
        ],
        {"missing": "violation", "visible": "compliant"},
        visible_if=condition_all(
            includes("ccpa_track_a_detection", "none"),
            excludes("ccpa_track_a_detection", "unsure"),
        ),
    )
)
add(
    checklist_question(
        "ccpa_track_b_vendor_lists",
        "CCPA",
        section,
        "트랙 B. 사업목적 제공 목록",
        "Q-B에서 위탁업체가 있는 경우, 다음 항목이 방침에 반영되어 있는가?",
        "판단 포인트: 사업목적 제공 카테고리 목록, 판매/공유 목록과의 분리, 수령자 유형 기재를 확인합니다.",
        "CCPA §1798.130(a)(5)(C)(ii), §1798.130(a)(5)(B)(iv)",
        [
            choice(
                "b1",
                "방침에 '최근 12개월간 사업목적으로 제공한 개인정보 카테고리' 목록이 있다",
            ),
            choice("b2", "리스트1(판매·공유)과 물리적으로 분리되어 있다"),
            choice("b3", "수령자 유형이 기재되어 있다"),
        ],
        required_values=["b1", "b2", "b3"],
        visible_if=equals("ccpa_track_b_detection", "yes"),
    )
)

section = "4. 국외이전"
add(
    single_question(
        "ccpa_cross_border_applies",
        "CCPA",
        section,
        "4-1. 캘리포니아 거주자 포함 여부",
        "서비스가 캘리포니아 거주자를 이용자로 포함하는가?",
        "판단 포인트: 캘리포니아 이용자 대상이면 국외이전 CCPA 점검을 이어갑니다.",
        "CCPA 적용 범위",
        [choice("no", "아니오"), choice("yes", "예")],
        {"yes": "recommended", "no": "recommended"},
    )
)
for question_id, title, prompt, legal_basis, yes_status, no_status in [
    (
        "ccpa_cross_border_vendor_contract",
        "4-2. 해외 수령자 계약 기반 여부",
        "해외 수령자에게 제공되는 개인정보 처리가 서비스제공자·계약자 계약에 근거하는가?",
        "CCPA §1798.100(d)",
        "compliant",
        "violation",
    ),
    (
        "ccpa_cross_border_sale_share_classification",
        "4-3. 해외 이전 판매·공유 판별",
        "해외 이전이 판매 또는 공유에 해당하는지 판별·관리하고 있는가?",
        "CCPA §1798.100(d)",
        "compliant",
        "insufficient",
    ),
    (
        "ccpa_cross_border_gpc",
        "4-4. 국외이전에 대한 GPC 적용",
        "GPC 신호 등 옵트아웃 메커니즘이 국외 이전 건에도 동일 적용되는가?",
        "CCPA §1798.135(b)",
        "compliant",
        "insufficient",
    ),
]:
    add(
        single_question(
            question_id,
            "CCPA",
            section,
            title,
            prompt,
            "판단 포인트: 제공 구조, 판매·공유 재분류 위험, GPC 일관 적용 여부를 확인합니다.",
            legal_basis,
            [choice("no", "아니오"), choice("yes", "예")],
            {"yes": yes_status, "no": no_status},
            visible_if=equals("ccpa_cross_border_applies", "yes"),
        )
    )

section = "5. 미성년자"
add(
    single_question(
        "ccpa_minors_sale_share",
        "CCPA",
        section,
        "5-0. 판매 또는 공유 발생 여부",
        "판매 또는 공유가 발생하는가?",
        "판단 포인트: 발생하지 않으면 미성년자 판매·공유 세부진단은 적용 제외입니다.",
        "CCPA §1798.120(c)",
        [choice("no", "발생 안 함"), choice("yes", "발생함")],
        {"yes": "recommended", "no": "recommended"},
    )
)
add(
    checklist_question(
        "ccpa_minors_controls",
        "CCPA",
        section,
        "5. 미성년자 판매·공유 통제",
        "판매 또는 공유가 발생하는 경우, 다음 항목이 갖춰져 있는가?",
        "판단 포인트: 연령 확인, 13세 미만 보호자 opt-in, 13~15세 본인 opt-in, 16세 이상 opt-out, 상회충족 구조, 12개월 재요청 금지를 확인합니다.",
        "CCPA §1798.120(c)",
        [
            choice(
                "age_check", "가입·이용 시 연령 또는 생년월일을 확인하는 절차가 있다"
            ),
            choice(
                "under13",
                "만 13세 미만 이용자의 판매·공유에 대해 부모·법정대리인의 사전 opt-in 동의를 받는다",
            ),
            choice(
                "age13to15",
                "만 13~15세 이용자의 판매·공유에 대해 본인의 사전 opt-in 동의를 받는다",
            ),
            choice("age16plus", "만 16세 이상 이용자에게는 opt-out 방식이 적용된다"),
            choice(
                "higher_standard",
                "개별 연령 구간 대응 대신, 더 높은 연령까지 판매·공유·타겟광고 자체를 제공하지 않는다",
            ),
            choice(
                "no_reask",
                "옵트인 거부 이력이 있는 이용자에게 12개월 내 재요청하지 않는다",
            ),
        ],
        required_values=["age_check", "under13", "age13to15", "age16plus", "no_reask"],
        recommended_values=["higher_standard"],
        visible_if=equals("ccpa_minors_sale_share", "yes"),
    )
)

section = "6. 자동화된 결정"
add(
    single_question(
        "ccpa_admt_exists",
        "CCPA",
        section,
        "6-1. 자동화된 의사결정 기술(ADMT) 사용 여부",
        "자동화된 의사결정 기술(ADMT)을 사용하는가?",
        "판단 포인트: ADMT를 사용하지 않으면 세부진단 대부분은 적용 제외됩니다.",
        "11 CCR §7220~7227, §7150 이하",
        [choice("no", "아니오"), choice("yes", "예")],
        {"yes": "recommended", "no": "recommended"},
    )
)
add(
    single_question(
        "ccpa_admt_significant_decision",
        "CCPA",
        section,
        "6-2. 중대한 결정 사용 여부",
        "금융·주거·교육·고용·의료 5개 영역 중 하나에서 '중대한 결정'에 사용되는가?",
        "판단 포인트: 단순 광고타겟팅을 넘는 중대한 결정인지 확인합니다.",
        "11 CCR §7220~7227",
        [choice("no", "아니오"), choice("yes", "예")],
        {"yes": "recommended", "no": "recommended"},
        visible_if=equals("ccpa_admt_exists", "yes"),
    )
)
add(
    checklist_question(
        "ccpa_admt_controls",
        "CCPA",
        section,
        "6. 자동화된 의사결정 기술(ADMT) 세부 통제",
        "ADMT를 사용하는 경우, 다음 항목이 갖춰져 있는가?",
        "판단 포인트: 직원·구직자 포함 범위, 사전고지, 옵트아웃, 접근권, 위험평가, 실효적 인간 검토, 추론정보 기재를 확인합니다.",
        "CCPA 소비자 정의, 11 CCR §7220~7227, §7150 이하, §1798.140(v)(1)(K)",
        [
            choice(
                "scope",
                "직원·계약자·구직자 대상 도구(이력서 스크리닝 등)도 점검 대상에 포함했다",
            ),
            choice(
                "notice", "사전고지(사용사실·결정방식·산출물·대안절차 포함)를 제공한다"
            ),
            choice("opt_out", "옵트아웃 권리를 제공한다"),
            choice("access", "로직·주요변수·영향에 대한 접근권 절차가 있다"),
            choice("risk", "프라이버시 위험평가를 수행했다"),
            choice(
                "human", "'인간 검토'가 실제로 재검토·변경 가능한 실효적 권한을 갖는다"
            ),
            choice("inference", "추론정보가 개인정보 카테고리로 기재되어 있다"),
        ],
        required_values=["notice", "opt_out", "access", "risk", "inference"],
        recommended_values=["scope", "human"],
        visible_if=equals("ccpa_admt_exists", "yes"),
        action_hint="ADMT 사용사실 고지, 옵트아웃, 접근권, 영향평가를 우선 구축하고 추론정보 카테고리도 방침에 반영하세요.",
    )
)

section = "7. 쿠키"
add(
    checklist_question(
        "ccpa_cookie_controls",
        "CCPA",
        section,
        "7. 쿠키",
        "다음 항목을 모두 충족하고 있는가?",
        "판단 포인트: 고유식별자 기재, 목적·출처·보유기간, 판매·공유 판별, 옵트아웃 링크, GPC 처리를 확인합니다.",
        "CCPA §1798.140(aj), §1798.130(a)(5), §1798.135(a)(b)",
        [
            choice(
                "identifier_category",
                "쿠키·비콘·픽셀·광고식별자를 고유식별자(개인정보)로 카테고리 기재하고 있다",
            ),
            choice(
                "policy_fields",
                "쿠키의 카테고리별 수집목적·출처·보유기간이 기재되어 있다",
            ),
            choice("sale_check", "쿠키 사용이 판매에 해당하는지 판별했다"),
            choice(
                "share_check",
                "쿠키 사용이 공유(share, 교차맥락 행동광고 목적)에 해당하는지 판별했다",
            ),
            choice("opt_out", "'Do Not Sell or Share' 옵트아웃 링크를 게시하고 있다"),
            choice("gpc", "GPC 신호를 유효한 옵트아웃 요청으로 처리하고 있다"),
        ],
        required_values=[
            "identifier_category",
            "policy_fields",
            "sale_check",
            "share_check",
        ],
        recommended_values=["opt_out", "gpc"],
    )
)


QUESTION_INDEX = {question["id"]: question for question in QUESTIONS}


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
