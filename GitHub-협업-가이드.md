# GitHub 조직(Organization) 협업 가이드 — 명령어와 주의사항

대상 조직: [WHS-PPAP](https://github.com/orgs/WHS-PPAP/repositories) / PPAP-Web 프로젝트용

## 1. 최초 1회 설정

```bash
# 저장소 복제 (조직 저장소: https://github.com/orgs/WHS-PPAP/repositories)
git clone https://github.com/WHS-PPAP/<저장소명>.git
cd <저장소명>

# 본인 확인용 설정 (커밋 작성자)
git config user.name "본인이름"
git config user.email "본인이메일"

# 원격 저장소 확인
git remote -v
```

## 2. 일상 작업 흐름 (브랜치 → 커밋 → 푸시 → PR)

```bash
# 1) 최신 main 반영
git checkout main
git pull origin main

# 2) 작업 브랜치 생성 (main에서 직접 작업 금지)
git checkout -b feature/가이드-모달-수정
# 네이밍 예시: feature/xxx, fix/xxx, docs/xxx

# 3) 변경 확인 후 커밋
git status
git diff
git add <파일>
git commit -m "가이드 팝업을 5단계 순서로 통일"

# 4) 푸시 (첫 푸시는 -u)
git push -u origin feature/가이드-모달-수정

# 5) PR 생성 (GitHub CLI)
gh pr create --title "가이드 팝업 형식 통일" --body "변경 내용 요약"
```

## 3. 리뷰·병합·정리

```bash
# PR 목록·상태 확인
gh pr list
gh pr view <번호>

# 리뷰 반영 후 추가 푸시 (같은 PR에 자동 반영)
git add <파일>
git commit -m "리뷰 반영: ..."
git push

# 병합 후 로컬 정리
git checkout main
git pull origin main
git branch -d feature/가이드-모달-수정
```

- 병합은 가급적 **PR 페이지에서 Squash merge 또는 Merge** (조직 규칙 따름).
- 리뷰 승인(approve) 없이 병합하지 않기 (branch protection 설정 권장).

## 4. 충돌 해결

```bash
# main 최신 변경을 작업 브랜치에 반영
git checkout feature/가이드-모달-수정
git pull origin main
# 충돌 발생 시: 해당 파일을 열어 <<<<<<< 표시 구간을 직접 정리 후
git add <정리한 파일>
git commit -m "main 반영 및 충돌 해결"
git push
```

- 충돌이 나면 당황하지 말고 **충돌 파일만** 수정, 엉뚱한 파일 건드리지 않기.
- 해결이 어려우면 PR에 `conflict` 상태 그대로 두지 말고 팀에 공유.

## 5. 이 프로젝트 전용 주의사항 (필수)

1. **`main` 브랜치에 직접 push 금지** — 모든 변경은 PR 경유.
2. **진단 문항·평가 로직 변경 금지** (`data/questions.py`, `evaluation` 매핑):
   변경이 필요하면 먼저 이슈를 만들고 리서치팀·멘토 확인 후 진행.
3. **비밀·로컬 파일 커밋 금지**:
   - `instance/*.sqlite3` (사용자 진단 DB), `__pycache__/`, `.env`
   - `FLASK_SECRET_KEY` 등 비밀값은 환경변수로만 전달, 코드에 하드코딩 금지.
   - 실수로 올렸다면: `git rm --cached <파일>` 후 `.gitignore` 추가.
4. **임시 검증 파일 커밋 금지**: `qa_*.mjs`, `*_check.html`, `server_*.log` 등은 올리지 않기.
5. **진단 결과 화면 변경 시 스크린샷 첨부**: `result.html`·`diagnosis.html` 수정 PR에는 변경 전/후 캡처 권장.
6. **커밋 메시지**: 한글 1줄 요약 권장 (예: `결과 리포트 줄 간격 조정`), 무엇을·왜 바꿨는지 알 수 있는 수준으로.
7. **CSP·보안 관련 변경은 `취약점패치.md`도 함께 갱신**.
8. **대용량 파일·바이너리 커밋 자제** (스크린샷은 PR 본문에 드래그 첨부, repo에 직접 커밋 지양).

## 6. 권장 `.gitignore` (프로젝트 루트)

```gitignore
__pycache__/
*.pyc
instance/
.env
*.log
qa_*.mjs
*_check.html
```

## 7. 문제 발생 시

```bash
# 마지막 커밋 취소 (푸시 전, 작업내용은 유지)
git reset --soft HEAD~1

# 특정 파일만 이전 상태로 되돌리기
git checkout -- <파일>

# 원격 브랜치 삭제 (병합 완료 후)
git push origin --delete feature/가이드-모달-수정
```

- 이미 `main`에 잘못 병합됐다면 **되돌리기 전에 팀에 먼저 공유** (force-push는 조직 저장소에서 원칙 금지).
