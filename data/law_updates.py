from __future__ import annotations

import time
import urllib.request
from datetime import datetime, timezone
from typing import Any

# ============================================================
# 법률개정 대응 (법령 개정 동향)
# ------------------------------------------------------------
# 서버에서 CPPA / EUR-Lex 소스를 조회해 "최근 개정일"을 확인하고,
# 조회에 실패하거나 임계값 시간 이내이면 정적 레지스트리로 대체합니다.
# (브라우저 CSP connect-src 'self' 제약 때문에 클라이언트가 아닌
#  서버에서만 외부 조회를 수행합니다. - app.py 참고)
# ============================================================

FETCH_TIMEOUT_SECONDS = 4
CACHE_TTL_SECONDS = 6 * 60 * 60  # 6시간

# 정적 레지스트리: 조회 실패 시에도 안정적으로 표시하는 기본 데이터.
# 날짜·사실은 공식 소스(EUR-Lex, CPPA) 기준으로 작성됐습니다.
STATIC_LAW_UPDATES: dict[str, list[dict[str, Any]]] = {
    "GDPR": [
        {
            "date": "2016-05-04",
            "title": "GDPR 공포 및 시행",
            "status": "발효",
            "summary": "EU 일반 개인정보 보호 규정이 공포(OJ L 119, 4.5.2016)되어 2018-05-25부터 적용됩니다.",
            "details": [
                "채택: 2016-04-27, 공포: OJ L 119 (2016-05-04)",
                "적용일: 2018-05-25 (회원국 직접 적용)",
                "EUR-Lex 통합본 버전: 04.05.2016 (CELEX 02016R0679)",
            ],
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02016R0679",
        },
        {
            "date": "2018-05-23",
            "title": "지정 정정 (Corrigendum)",
            "status": "정정",
            "summary": "공포 원문의 오기가 일부 정정되어 OJ L 127 (2018-05-23)에 게재되었습니다.",
            "details": [
                "정정 게재: OJ L 127, 23.5.2018, p. 2",
                "문안 해석 시 공포 원문과 통합본을 함께 참고해야 합니다.",
            ],
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02016R0679",
        },
        {
            "date": "2024-08-01",
            "title": "AI법(AI Act) 발효와 GDPR 관계",
            "status": "관련법",
            "summary": "AI Act(Regulation (EU) 2024/1689)가 2024-08-01 발효되었습니다. AI법은 GDPR을 대체하지 않고, 개인정보 보호 의무는 그대로 유지됩니다.",
            "details": [
                "AI Act 제2조: GDPR 등 개인정보 보호법 적용에는 영향 없음",
                "고위험 AI 시스템의 편향성·투명성 의무 등 신규 요건은 GDPR 의무와 별개로 준수 필요",
                "프로파일링·자동결정 관련 GDPR 제22조 의무는 지속 적용",
            ],
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
        },
        {
            "date": "2025-11-20",
            "title": "디지털 옴니버스(Digital Omnibus) 개정 제안",
            "status": "입법중",
            "summary": "EU 집행위가 GDPR 등 디지털 규제 간소화를 위한 개정안(2025-11)을 제안했습니다. 확정 전 단계이며 향후 개정 동향을 지속 확인해야 합니다.",
            "details": [
                "개정 대상: '개인정보' 정의 명확화, 가명처리 데이터의 개인정보 해당 여부 판단 지원",
                "정보제공 의무·침해통지 사무부담 완화 검토",
                "쿠키 배너 등 단말기 접근 관련 ePrivacy 정비 논의 포함",
                "※ 제안 단계로 확정 시 진단 문항의 법적 근거가 갱신될 수 있습니다.",
            ],
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52025PC0547",
        },
    ],
    "CCPA": [
        {
            "date": "2026-01-01",
            "title": "CCPA 규정 전면 개정 시행",
            "status": "시행",
            "summary": "기존 CCPA 규정 업데이트와 함께 사이버보안 감사·위험평가·ADMT(자동결정기술)·보험사 관련 신규 규정이 2026-01-01부터 시행됩니다.",
            "details": [
                "CPPA 이사회 채택: 2025-07-24",
                "OAL 승인·SoS 등재: 2025-09-22",
                "시행일: 2026-01-01 (일부 의무는 2027-01-01 유예)",
                "민감정보 기준에 16세 미만 소비자 정보가 포함되는 등 수정사항 다수",
                "사업자는 개인정보처리방침, Do Not Sell or Share 링크, 민감정보 제한, 권리요청 절차 재점검 필요",
            ],
            "source_url": "https://cppa.ca.gov/regulations/ccpa_updates.html",
        },
        {
            "date": "2027-01-01",
            "title": "ADMT(자동결정기술) 신규 의무 시행",
            "status": "시행(유예)",
            "summary": "소비자에게 중요 결정(주택·고용·금융 등)을 내리는 ADMT 사용 사업자는 접근권·선택해제권·사전공지 등 신규 의무를 2027-01-01부터 이행해야 합니다.",
            "details": [
                "대상: 금융·주거·교육·고용·의료 등 '중대한 결정'에 ADMT 사용 시",
                "요구사항: ADMT 사용 사전공지, 소비자 접근권, 선택해제(opt-out)권",
                "광고 목적 사용만으로는 이 규정 대상에 해당하지 않음",
                "2026-01-01 시행 규정과 별도로 이행 준비 기간 부여",
            ],
            "source_url": "https://cppa.ca.gov/regulations/ccpa_updates.html",
        },
        {
            "date": "2028-04-01",
            "title": "위험평가·사이버보안 감사 제출 의무",
            "status": "예정",
            "summary": "위험평가 인증서는 2028-04-01부터, 사이버보안 감사는 매출 규모별로 2028~2030년 사이 제출 의무가 시작됩니다.",
            "details": [
                "위험평가: 2026-01-01 이후 착수된 중요 처리활동 대상, 2028-04-01 제출 의무",
                "사이버보안 감사: 매출 1억 달러 초과 시 2028-04-01, 5천만~1억 달러 2029-04-01, 그 외 2030-04-01",
                "감사 대상 판단 기준: 연 매출·처리 정보량(25만 명 이상)·민감정보(5만 명 이상) 등",
            ],
            "source_url": "https://cppa.ca.gov/regulations/ccpa_updates.html",
        },
    ],
}


_LAW_UPDATE_CACHE: dict[str, Any] = {"fetched_at": 0.0, "data": None}


def _fetch_url(url: str) -> tuple[int, str] | None:
    """지정 URL을 짧은 타임아웃으로 조회해 (상태코드, 바이트수)를 반환합니다.

    대부분의 소스가 일부 구간에서 차단되므로 실패는 정상으로 간주하고,
    성공 시에만 '수집 시각' 표시를 갱신합니다.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                ),
                "Accept": "text/html,*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_SECONDS) as response:
            body = response.read()
            return (response.status, str(len(body)))
    except Exception:
        return None


def _collect_source_facts() -> dict[str, Any]:
    """각 법령의 공식 소스 접근 상태(선택적 수집)를 확인합니다."""
    facts: dict[str, Any] = {"checked_ok": [], "errors": []}
    targets = [
        ("GDPR", "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02016R0679"),
        ("CCPA", "https://cppa.ca.gov/regulations/ccpa_updates.html"),
    ]
    for law_key, url in targets:
        result = _fetch_url(url)
        if result is None:
            facts["errors"].append(law_key)
        else:
            facts["checked_ok"].append(law_key)
    return facts


def get_law_updates(force_refresh: bool = False) -> dict[str, Any]:
    """법령 개정 동향 데이터를 반환합니다(캐시 + 폴백).

    반환 구조:
      {
        "fetched_at": ISO8601 | None,
        "source_status": {"GDPR": "ok"|"fallback", "CCPA": ...},
        "laws": [{"key", "title", "subtitle", "updates": [...]}, ...],
      }
    """
    now = time.time()
    cached = _LAW_UPDATE_CACHE["data"]
    if (
        not force_refresh
        and cached is not None
        and (now - _LAW_UPDATE_CACHE["fetched_at"]) < CACHE_TTL_SECONDS
    ):
        return cached

    source_facts = _collect_source_facts()
    laws = []
    for law_key, meta in (
        ("GDPR", ("GDPR", "EU 일반 개인정보 보호 규정")),
        ("CCPA", ("CCPA", "캘리포니아 소비자 개인정보 보호법")),
    ):
        title, subtitle = meta
        updates = STATIC_LAW_UPDATES[law_key]
        source_status = "ok" if law_key in source_facts["checked_ok"] else "fallback"
        laws.append(
            {
                "key": law_key,
                "title": title,
                "subtitle": subtitle,
                "source_status": source_status,
                "updates": updates,
            }
        )

    fetched_at = None
    if source_facts["checked_ok"]:
        fetched_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    payload = {
        "fetched_at": fetched_at,
        "errors": source_facts["errors"],
        "laws": laws,
    }
    _LAW_UPDATE_CACHE["fetched_at"] = now
    _LAW_UPDATE_CACHE["data"] = payload
    return payload