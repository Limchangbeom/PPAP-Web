# Research Memo: Is There a Priority Sector for PPAP?

**Question**: Among Korean SMEs/startups expanding overseas, is there one industry that needs a GDPR/CCPA self-assessment tool like PPAP most, on social-benefit grounds (not just "any company that processes personal data")?

**Bottom line**: Yes — **mobile/online gaming** is the strongest, evidence-backed answer, with **health/wellness ("femtech") apps** as a distinct but weaker-fit secondary candidate. The case rests on three independent lines of evidence converging on gaming; no other sector shows the same triple convergence.

## 1. Enforcement pattern points at consent/legal-basis and children's-data failures — both central to gaming

- CMS's *GDPR Enforcement Tracker Report 2025/2026* finds **"insufficient legal basis" is the single most common violation type (~34% of fines)**, most often manifesting as invalid consent for behavioral-advertising tracking — exactly PPAP's Section 2 (consent) and Section 7 (cookies). ([cms.law](https://cms.law/en/int/publication/gdpr-enforcement-tracker-report/numbers-and-figures))
- Concrete gaming precedents on this exact violation type: **CNIL fined mobile-game publisher Voodoo €3M (2022)** for reading an ad-tracking identifier after users declined consent ([cnil.fr](https://www.cnil.fr/en/mobile-games-cnil-fined-voodoo-3-million-euros-0)); **NOYB's April 2025 GDPR complaint against Ubisoft** (up to €92M exposure) alleges games force always-online connections and data collection with no valid Art. 6 basis ([noyb.eu](https://noyb.eu/sites/default/files/2025-04/Ubisoft_complaint_EN_redacted.pdf)).
- Children's data in gaming is a live, escalating enforcement target: the **FTC's $20M COPPA settlement with Cognosphere (Genshin Impact), May 2025** ([epic.org](https://epic.org)); industry trackers note child-safety-related fines in tech/gaming rose from ~$200M (pre-2022) to over $2B (since 2023) ([heydata.eu](https://heydata.eu/en/magazine/gaming-gdpr-risks-are-rising-and-these-2025-cases-prove-it)). This maps directly to PPAP's Section 5 (minors).
- CCPA's 2025 enforcement priorities (CPPA/AG Bonta) — the location-data investigative sweep and the record **$1.55M Healthline settlement (July 2025)** — target exactly the ad-tech/geolocation-sharing and sale/share-opt-out patterns common to ad-monetized mobile apps, including games. ([oag.ca.gov](https://oag.ca.gov/news/press-releases/attorney-general-bonta-announces-investigative-sweep-location-data-industry), [mayerbrown.com](https://www.mayerbrown.com/en/insights/publications/2025/05/california-privacy-protection-agency-intensifies-enforcement-recent-enforcement-actions-and-trends))

## 2. Vulnerable-population frameworks flag children and sensitive-data subjects, not one named industry

GDPR Art. 8/9 and Art. 35(3), and CCPA's "sensitive PI" definition, are data-category tests, not industry lists. Mapping categories to industries: children's services (edtech, gaming) for Art. 8/COPPA; health/mental-health/femtech for Art. 9 health data (FTC's post-*Dobbs* crackdown: BetterHelp $7.8M, GoodRx $1.5M, Premom, Flo Health); dating apps for sexual-orientation data (Grindr: Norwegian DPA ~€6.5–10M fine 2021 + UK £26M settlement, Sept 2026) — all genuinely high-harm, but each is a narrower or smaller export category for Korean firms than gaming (see below).

## 3. Korean-specific angle: gaming is the one sector where "high enforcement risk" and "under-resourced Korean SME exporter" overlap at scale

- Gaming is **Korea's largest single content export category — 60.4% of content exports in 2024**, and Korea is the world's #4 game market (7.2% global share) per KOCCA's *2025 Korea Game White Paper*. Total K-content exports (~$15B) exceed K-beauty (~$10.4B). No other Korean overseas-expansion sector approaches this scale. ([etnews.com](https://www.etnews.com/20251009000018), KOCCA game white paper coverage)
- KOCCA's own *Global Game Industry Trend* briefings explicitly discuss GDPR risk for Korean developers entering the EU and recommend Privacy-by-Design/data minimization ([kocca.kr](https://kocca.kr/seriousgame/archives/view.do?bbs=42&nttId=2009282&bbsId=B0158968)).
- Korean industry press (게임플, 게임메카, 경향게임스, ZDNet Korea, multiple years) and KISA repeatedly note that **large Korean publishers (Nexon, Netmarble, NCSoft, Kakao Games) have GDPR programs, but the long tail of small/mid Korean game studios does not** — which is exactly why KISA's GDPR/CCPA consulting program (running since 2019, CCPA added 2021) exists and targets 15 SMEs/year. This SME/startup gap is precisely PPAP's target user.

## Caveats / what would weaken this conclusion

- Health/femtech apps arguably present *higher per-incident harm* (reproductive-health privacy post-*Dobbs*) than gaming, but Korean digital-health exports are far smaller in volume than gaming exports, so the "Korean SME overseas-expansion" leg of the argument is weaker there.
- "Industry and commerce" and "media/telecom" categories carry more total GDPR fine *volume/value* than gaming in the aggregate trackers ([cms.law](https://cms.law/en/int/publication/gdpr-enforcement-tracker-report/numbers-and-figures)) — gaming's case rests on violation-type fit, children's-data trend, and the Korean-export angle, not on being the single largest fined sector overall.
- No Korean game company has yet been publicly fined under GDPR/CCPA (per Korean trade press as of the searches above), so this is a "high compounding risk, not yet realized" case rather than a documented pattern of Korean-company enforcement.

## Sources

- CMS, *GDPR Enforcement Tracker Report 2025/2026* — https://cms.law/en/int/publication/gdpr-enforcement-tracker-report/numbers-and-figures
- CNIL, "Mobile games: the CNIL fined VOODOO 3 million euros" — https://www.cnil.fr/en/mobile-games-cnil-fined-voodoo-3-million-euros-0
- NOYB complaint against Ubisoft (April 2025) — https://noyb.eu/sites/default/files/2025-04/Ubisoft_complaint_EN_redacted.pdf
- EPIC, "FTC Fines Online Therapy Company BetterHelp $7.8 Million" — https://epic.org/ftc-fines-online-therapy-company-betterhelp-7-8-million-for-sharing-health-data/
- HIPAA Journal, GoodRx FTC settlement — https://www.hipaajournal.com/court-approves-ftc-settlement-goodrx/
- Axios, FTC/Premom fertility app — https://www.axios.com/2023/05/18/ftc-cracks-down-fertility-app-premom-after-goodrx-action
- California DOJ, location-data industry investigative sweep (2025) — https://oag.ca.gov/news/press-releases/attorney-general-bonta-announces-investigative-sweep-location-data-industry
- Mayer Brown, CPPA enforcement trends 2025 — https://www.mayerbrown.com/en/insights/publications/2025/05/california-privacy-protection-agency-intensifies-enforcement-recent-enforcement-actions-and-trends
- Norwegian DPA / EDPB, Grindr fine — https://www.edpb.europa.eu/news/national-news/2021/norwegian-dpa-imposes-fine-against-grindr-llc_en
- The Register, Grindr UK £26M settlement (Sept 2026) — https://www.theregister.com/legal/2026/09/08/grindr-pays-26m-to-settle-uk-privacy-class-action/5294935
- heydata.eu, "Gaming GDPR: Risks Are Rising — and These 2025 Cases Prove It" — https://heydata.eu/en/magazine/gaming-gdpr-risks-are-rising-and-these-2025-cases-prove-it
- 전자신문, K-content exports 2025 (games = 60.4% of content exports) — https://www.etnews.com/20251009000018
- KOCCA, Global Game Industry Trend (GDPR discussion) — https://kocca.kr/seriousgame/archives/view.do?bbs=42&nttId=2009282&bbsId=B0158968
- 게임플, "유럽 진출한 한국 게임기업 긴장케 하는 GDPR은 무엇?" — https://www.gameple.co.kr/news/articleView.html?idxno=142309
