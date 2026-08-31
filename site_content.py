PROJECT_NAME = "PPAP"
PROJECT_FULL_NAME = "Privacy Policy Anywhere Passport"
PROJECT_OVERVIEW = "PPAP (Privacy Policy Anywhere Passport): 서비스의 해외 진출을 위한 개인정보 처리방침 진단 도구"

BACKGROUND_CASES = [
    {
        "title": "Meta EU-미국 데이터 이전 제재 사례 (2023)",
        "detail": "Meta Ireland는 EU 이용자 데이터를 미국으로 이전하면서 충분한 보호수단을 입증하지 못해 12억 유로 제재를 받았습니다. 이 사례는 국외이전의 적법근거뿐 아니라 실제 보호조치와 이전영향평가까지 함께 점검해야 함을 보여줍니다.",
        "source": "아일랜드 DPC",
        "url": "https://www.dataprotection.ie/en/news-media/press-releases/Data-Protection-Commission-announces-conclusion-of-inquiry-into-Meta-Ireland",
    },
    {
        "title": "Sephora CCPA 제재 사례 (2022)",
        "detail": "Sephora는 웹사이트에 광고·분석용 추적 도구를 설치해 이용자 정보를 제3자 광고 사업자에게 전달하면서도 이를 판매·공유로 적절히 고지하지 않았고, 옵트아웃 링크와 GPC 신호 처리도 제대로 제공하지 않아 120만 달러 합의와 시정명령을 받았습니다. 이 사례는 쿠키·픽셀 운영이 단순 분석이 아니라 CCPA상 판매·공유로 재분류될 수 있음을 보여줍니다.",
        "source": "California Attorney General",
        "url": "https://oag.ca.gov/news/press-releases/attorney-general-bonta-announces-settlement-sephora-part-ongoing-enforcement",
    },
    {
        "title": "Instagram 아동 개인정보 제재 사례 (2022)",
        "detail": "Instagram은 미성년자 계정의 공개 설정과 연락처 노출 등 보호 설계가 충분하지 않다고 판단되어 4억500만 유로 제재를 받았습니다. 이 사례는 아동 서비스에서 기본 공개설정, 연령 확인, 보호자 동의, 이해하기 쉬운 고지가 처음부터 설계되어야 함을 보여줍니다.",
        "source": "아일랜드 DPC",
        "url": "https://www.dataprotection.ie/en/news-media/press-releases/data-protection-commission-announces-decision-instagram-inquiry",
    },
]

BACKGROUND_STATS = {
    "title": "한국 ICT 서비스 수출액(미달러 기준)",
    "subtitle": "국내 디지털 서비스의 국외 활동 확대 흐름",
    "max_value": 16.5,
    "bars": [
        {"year": "2019", "value": 7.7, "label": "$7.7B"},
        {"year": "2021", "value": 14.8, "label": "$14.8B"},
        {"year": "2023", "value": 15.1, "label": "$15.1B"},
        {"year": "2024", "value": 16.5, "label": "$16.5B"},
    ],
    "summary": "World Bank 집계 기준 한국의 ICT 서비스 수출은 2019년 76.7억 달러에서 2024년 165.2억 달러로 두 배 이상 확대되었습니다.",
    "source": "World Bank, indicator BX.GSR.CCIS.CD",
    "url": "https://api.worldbank.org/v2/country/KOR/indicator/BX.GSR.CCIS.CD?format=json&per_page=20",
}

EXPECTED_EFFECTS = [
    "해외 서비스 출시 전, 어떤 개인정보 처리방침과\n운영 절차를 먼저 점검해야 하는지 빠르게 정리할 수 있습니다.",
    "GDPR과 CCPA를 같은 화면 흐름에서 비교해 지역별 필수 고지,\n권리 대응, 국외이전, 쿠키 통제를 함께 검토할 수 있습니다.",
    "법무·개발·기획이 공통 체크리스트를 공유해 기능 출시 이전에\n누락 위험을 줄이고 내부 커뮤니케이션 비용을 낮출 수 있습니다.",
]

USER_PROCESS_STEPS = [
    {
        "step": "01",
        "title": "규정 선택",
        "detail": "진단 대상 규정을 GDPR, CCPA 중에서 선택하고,\nGDPR은 개인정보처리자 또는 처리수탁자 기준을 함께 정합니다.",
    },
    {
        "step": "02",
        "title": "문항 응답",
        "detail": "페이지별 문항에 응답하면서 개인정보 범위, 처리 근거,\n제3자 제공, 국외이전, 쿠키, 미성년자, 자동결정 항목을 점검합니다.",
    },
    {
        "step": "03",
        "title": "판정 확인",
        "detail": "응답 결과를 바탕으로 위반, 미흡, 충족, 권장 상태를 정리하고 우선 보완 항목을 확인합니다.",
    },
    {
        "step": "04",
        "title": "리포트 정리",
        "detail": "결과 화면과 인쇄형 리포트를 통해 내부\n공유용 진단 결과를 바로 정리합니다.",
    },
]
