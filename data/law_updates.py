from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

# ============================================================
# 법률개정 대응 (법령 개정 동향)
# ------------------------------------------------------------
# 서버에서 EUR-Lex SPARQL / CPPA 페이지에서 개정·공지를 실제로 수집하고,
# 수집에 실패한 법령만 정적 레지스트리로 대체합니다(source_status=fallback).
# (브라우저 CSP connect-src 'self' 제약 때문에 클라이언트가 아닌
#  서버에서만 외부 조회를 수행합니다. - app.py 참고)
# ============================================================

FETCH_TIMEOUT_SECONDS = 8
SPARQL_TIMEOUT_SECONDS = 12
CACHE_TTL_SECONDS = 60 * 60  # 1시간

SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
CDM = "http://publications.europa.eu/ontology/cdm#"
GDPR_CELLAR = "http://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1"
CCPA_UPDATES_URL = "https://cppa.ca.gov/regulations/ccpa_updates.html"
EURLEX_CELEX_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}"

_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
}

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


def _http_get(url: str, headers: dict[str, str], timeout: int) -> bytes | None:
    """URL을 조회해 body를 반환합니다. 실패 시 None."""
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status >= 400:
                return None
            return response.read()
    except Exception:
        return None


def _sparql_select(query: str) -> list[dict[str, str]] | None:
    """SPARQL SELECT를 실행해 plain dict 행 목록을 반환합니다. 실패 시 None."""
    url = (
        SPARQL_ENDPOINT
        + "?query="
        + urllib.parse.quote(query)
        + "&format=application%2Fsparql-results%2Bjson"
    )
    headers = {
        **_REQUEST_HEADERS,
        "Accept": "application/sparql-results+json",
    }
    body = _http_get(url, headers, SPARQL_TIMEOUT_SECONDS)
    if body is None:
        return None
    try:
        data = json.loads(body)
        bindings = data["results"]["bindings"]
    except Exception:
        return None
    return [
        {key: cell.get("value", "") for key, cell in row.items()} for row in bindings
    ]


_ISO_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _iso_date(*values: str | None) -> str | None:
    """xsd:date 문자열들에서 첫 YYYY-MM-DD 를 추출합니다."""
    for value in values:
        if not value:
            continue
        match = _ISO_DATE_RE.search(value)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return None


def _celex_id(value: str | None) -> str | None:
    """CELEX URI/리터럴에서 순수 CELEX 식별자를 추출합니다."""
    if not value:
        return None
    candidate = value.rstrip("/").split("/")[-1].split("#")[-1]
    return candidate or None


def _gdpr_update(item: dict[str, Any]) -> dict[str, Any]:
    """SPARQL 집계 행 1건을 updates 엔트리로 변환합니다."""
    date: str = item["date"]
    celex: str = item["celex"]
    kind: str = item["kind"]
    titles: list[str] = item["titles"]
    url = (
        EURLEX_CELEX_URL.format(celex=celex)
        if celex
        else EURLEX_CELEX_URL.format(celex="02016R0679")
    )
    if kind == "corrigendum":
        picked = next(
            (t for t in titles if "corrigendum" in t.lower()),
            titles[0] if titles else "",
        )
        title = picked or (
            f"GDPR 정정 ({celex})" if celex else "GDPR 정정 (Corrigendum)"
        )
        return {
            "date": date,
            "title": title,
            "status": "정정",
            "summary": (
                "EUR-Lex에 GDPR 정정"
                + (f" ({celex})" if celex else "")
                + "이 등재되어 있습니다. 문안 해석 시 통합본과 함께 확인하세요."
            ),
            "details": [
                "등재 유형: Corrigendum",
                f"연관 CELEX: {celex or '02016R0679'}",
            ],
            "source_url": url,
        }
    picked = next(
        (t for t in titles if t.lower().startswith("proposal")),
        titles[0] if titles else "",
    )
    title = picked or (
        f"GDPR 개정 제안 ({celex})" if celex else "GDPR 개정 제안"
    )
    return {
        "date": date,
        "title": title,
        "status": "입법중",
        "summary": (
            "EUR-Lex에 GDPR 개정 제안이 등재되어 있습니다. "
            "제안 단계로 확정 전이며 향후 개정 동향을 지속 확인해야 합니다."
        ),
        "details": [
            "문서 유형: 제안(Proposal)",
            f"CELEX: {celex or '-'}",
        ],
        "source_url": url,
    }


def _fetch_gdpr_live() -> list[dict[str, Any]] | None:
    """EUR-Lex SPARQL에서 GDPR 정정·개정 제안을 수집합니다. 실패 시 None."""
    query = f"""
        SELECT ?kind ?act ?celex ?d ?d2 ?title WHERE {{
          {{
            ?act <{CDM}resource_legal_corrects_resource_legal> <{GDPR_CELLAR}> .
            BIND("corrigendum" AS ?kind)
          }}
          UNION
          {{
            ?act <{CDM}resource_legal_proposes_to_amend_resource_legal> <{GDPR_CELLAR}> .
            BIND("proposal" AS ?kind)
          }}
          OPTIONAL {{ ?act <{CDM}resource_legal_id_celex> ?celex }}
          OPTIONAL {{ ?act <{CDM}work_date_document> ?d }}
          OPTIONAL {{ ?act <{CDM}resource_legal_date_document> ?d2 }}
          OPTIONAL {{ ?act <{CDM}work_title> ?title }}
        }} LIMIT 100
    """
    rows = _sparql_select(query)
    if rows is None:
        return None
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        date = _iso_date(row.get("d"), row.get("d2"))
        if not date:
            continue
        kind = row.get("kind") or "proposal"
        celex = _celex_id(row.get("celex")) or ""
        key = (kind, celex, date)
        title = (row.get("title") or "").strip()
        entry = grouped.get(key)
        if entry is None:
            grouped[key] = {
                "kind": kind,
                "celex": celex,
                "date": date,
                "titles": [title] if title else [],
            }
        elif title and title not in entry["titles"]:
            entry["titles"].append(title)
    updates = [_gdpr_update(entry) for entry in grouped.values()]
    updates.sort(key=lambda entry: entry["date"], reverse=True)
    return updates


_US_MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

_CCPA_DATE_RE = re.compile(
    r"((?:January|February|March|April|May|June|July|August|September"
    r"|October|November|December)\s+\d{1,2},\s+20\d{2})"
    r"\s*(?:&ndash;|&#8211;|&#x2013;|–|-)\s*([^<]{5,150})"
)


def _us_date_to_iso(value: str) -> str | None:
    """'September 22, 2025' 형태를 YYYY-MM-DD 로 변환합니다(로케일 독립)."""
    match = re.match(r"([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})", value.strip())
    if not match:
        return None
    month = _US_MONTHS.get(match.group(1))
    if month is None:
        return None
    return f"{int(match.group(3)):04d}-{month:02d}-{int(match.group(2)):02d}"


def _fetch_ccpa_live() -> list[dict[str, Any]] | None:
    """CPPA 규정 업데이트 페이지에서 문서 이벤트(날짜–제목)를 수집합니다."""
    body = _http_get(CCPA_UPDATES_URL, _REQUEST_HEADERS, FETCH_TIMEOUT_SECONDS)
    if body is None:
        return None
    html = body.decode("utf-8", errors="replace")
    seen: set[tuple[str, str]] = set()
    updates: list[dict[str, Any]] = []
    for match in _CCPA_DATE_RE.finditer(html):
        date = _us_date_to_iso(match.group(1))
        title = re.sub(r"\s+", " ", match.group(2)).strip()
        if not date or not title or (date, title) in seen:
            continue
        seen.add((date, title))
        updates.append(
            {
                "date": date,
                "title": title,
                "status": "공지",
                "summary": f"CPPA 규정 업데이트 페이지에 등재된 문서 이벤트입니다. ({title})",
                "details": [
                    "출처: California Privacy Protection Agency 규정 업데이트 페이지",
                ],
                "source_url": CCPA_UPDATES_URL,
            }
        )
    updates.sort(key=lambda entry: entry["date"], reverse=True)
    return updates


def _merge_updates(
    base: list[dict[str, Any]],
    live: list[dict[str, Any]],
    replace_statuses: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """정적 기본 항목과 실시간 항목을 병합해 최신순으로 정렬합니다.

    live 가 비면 base 를 그대로 두고, replace_statuses 로 시작하는
    정적 항목은 실시간 수집분으로 대체 제거합니다.
    """
    if not live:
        return sorted(
            base, key=lambda entry: str(entry.get("date") or ""), reverse=True
        )
    kept = [entry for entry in base if entry.get("status") not in replace_statuses]
    merged = list(kept)
    seen = {(entry.get("date"), entry.get("status")) for entry in merged}
    for entry in live:
        key = (entry.get("date"), entry.get("status"))
        if key in seen:
            continue
        seen.add(key)
        merged.append(entry)
    merged.sort(key=lambda entry: str(entry.get("date") or ""), reverse=True)
    return merged


def get_law_updates(force_refresh: bool = False) -> dict[str, Any]:
    """법령 개정 동향 데이터를 반환합니다(캐시 + 폴백).

    반환 구조:
      {
        "fetched_at": ISO8601 | None,
        "errors": ["GDPR"|"CCPA", ...],  # 실시간 수집 실패한 법령
        "laws": [
          {"key", "title", "subtitle",
           "source_status": "ok"|"fallback", "updates": [...]},
          ...
        ],
      }
    source_status "ok" = 해당 법령의 공식 소스에서 실제 수집 성공.
    """
    now = time.time()
    cached = _LAW_UPDATE_CACHE["data"]
    if (
        not force_refresh
        and cached is not None
        and (now - _LAW_UPDATE_CACHE["fetched_at"]) < CACHE_TTL_SECONDS
    ):
        return cached

    live_updates: dict[str, list[dict[str, Any]] | None] = {
        "GDPR": _fetch_gdpr_live(),
        "CCPA": _fetch_ccpa_live(),
    }
    errors = [key for key, value in live_updates.items() if value is None]

    laws = []
    for law_key, title, subtitle in (
        ("GDPR", "GDPR", "EU 일반 개인정보 보호 규정"),
        ("CCPA", "CCPA", "캘리포니아 소비자 개인정보 보호법"),
    ):
        live = live_updates[law_key]
        if live is None:
            updates = sorted(
                STATIC_LAW_UPDATES[law_key],
                key=lambda entry: str(entry.get("date") or ""),
                reverse=True,
            )
            source_status = "fallback"
        else:
            replace_statuses = ("정정",) if law_key == "GDPR" else ()
            updates = _merge_updates(
                STATIC_LAW_UPDATES[law_key], live, replace_statuses
            )
            source_status = "ok"
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
    if len(errors) < len(live_updates):
        fetched_at = datetime.now(timezone.utc).astimezone().isoformat(
            timespec="seconds"
        )

    payload = {
        "fetched_at": fetched_at,
        "errors": errors,
        "laws": laws,
    }
    _LAW_UPDATE_CACHE["fetched_at"] = now
    _LAW_UPDATE_CACHE["data"] = payload
    return payload