# 🛠️ 문제 해결 가이드

이 가이드는 Notion-Hugo 사용 중 자주 발생하는 문제들과 해결 방법을 제공합니다.

## 📋 목차

- [배포 관련 문제](#배포-관련-문제)
- [노션 연동 문제](#노션-연동-문제)
- [동기화 문제](#동기화-문제)
- [Hugo 빌드 문제](#hugo-빌드-문제)
- [일반적인 환경 문제](#일반적인-환경-문제)

## 🚀 배포 관련 문제

### Vercel 배포 실패

**문제**: Vercel 배포 버튼을 클릭했는데 배포가 실패함

**해결책**:
1. **NOTION_TOKEN 확인**
   ```bash
   # 노션 토큰이 올바른지 확인
   python -c "
   import requests
   token = 'YOUR_TOKEN'
   headers = {'Authorization': f'Bearer {token}', 'Notion-Version': '2022-06-28'}
   response = requests.get('https://api.notion.com/v1/users/me', headers=headers)
   print('토큰 유효:', response.status_code == 200)
   "
   ```

2. **환경 변수 설정 확인**
   - Vercel 대시보드 → Settings → Environment Variables
   - `NOTION_TOKEN` 변수가 올바르게 설정되었는지 확인

3. **빌드 로그 확인**
   - Vercel 대시보드의 Deployments 탭에서 실패한 배포 클릭
   - 빌드 로그에서 구체적인 오류 메시지 확인

### GitHub Pages 배포 문제

**문제**: GitHub Actions 워크플로우가 실행되지 않음

**해결책**:
1. **GitHub Pages 활성화 확인**
   ```bash
   # Repository Settings → Pages에서 확인
   # Source: GitHub Actions 선택되어 있는지 확인
   ```

2. **GitHub Actions 권한 확인**
   - Settings → Actions → General
   - "Allow all actions and reusable workflows" 선택
   - "Read and write permissions" 활성화

3. **Secret 설정 확인**
   ```bash
   # Repository Settings → Secrets and variables → Actions
   # NOTION_TOKEN이 설정되어 있는지 확인
   ```

**문제**: GitHub Pages 사이트에 접속이 안됨

**해결책**:
1. **DNS 전파 대기**: 최대 10분 정도 기다려보세요
2. **사이트 URL 확인**: `https://username.github.io/repository-name`
3. **브라우저 캐시 삭제**: Ctrl+F5 또는 시크릿 모드로 접속

## 📝 노션 연동 문제

### 노션 API 토큰 문제

**문제**: "Invalid token" 오류

**해결책**:
1. **새 통합 생성**
   - [notion.so/my-integrations](https://notion.so/my-integrations) 방문
   - "New integration" 클릭
   - 이름 입력 후 "Submit" 클릭
   - "Internal Integration Token" 복사

2. **토큰 형식 확인**
   ```bash
   # 올바른 형식: secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   # 길이: 43-50자 정도
   ```

### 노션 데이터베이스 접근 문제

**문제**: "Database not found" 오류

**해결책**:
1. **데이터베이스 공유 확인**
   - 노션 데이터베이스 페이지에서 "Share" 클릭
   - 생성한 통합(Integration) 이름 찾아서 "Invite" 클릭

2. **데이터베이스 ID 확인**
   ```bash
   # URL에서 데이터베이스 ID 추출
   # https://notion.so/your-database-id?v=view-id
   # 32자리 문자열이 데이터베이스 ID
   ```

3. **자동 설정 사용**
   ```bash
   python setup.py -i
   # 대화형 모드로 자동 데이터베이스 생성
   ```

## 🔄 동기화 문제

### 동기화가 되지 않음

**문제**: 노션에서 글을 발행했는데 블로그에 반영되지 않음

**해결책**:
1. **isPublished 속성 확인**
   - 노션 페이지에서 `isPublished` 체크박스가 체크되어 있는지 확인
   - 속성이 없다면 데이터베이스 설정에서 추가

2. **수동 동기화 실행**
   ```bash
   # 전체 동기화
   python notion_hugo_app.py --full-sync
   
   # 변경사항 확인
   python notion_hugo_app.py --dry-run
   ```

3. **캐시 정리**
   ```bash
   # 캐시 파일 삭제
   rm -rf __pycache__/
   rm -rf .cache/
   rm -rf memory-bank/
   
   # 다시 동기화
   python notion_hugo_app.py --full-sync
   ```

### 이미지가 표시되지 않음

**문제**: 노션의 이미지가 블로그에서 깨짐

**해결책**:
1. **이미지 형식 확인**
   - 지원 형식: JPG, PNG, GIF, WebP
   - 최대 크기: 20MB

2. **외부 이미지 사용**
   ```markdown
   # 노션에서 외부 이미지 URL 사용
   ![이미지 설명](https://example.com/image.jpg)
   ```

3. **로컬 이미지 업로드**
   - 노션에 직접 이미지 드래그&드롭
   - 자동으로 노션 CDN에 업로드됨

## 🏗️ Hugo 빌드 문제

### Hugo 빌드 실패

**문제**: "Hugo build failed" 오류

**해결책**:
1. **Hugo 버전 확인**
   ```bash
   hugo version
   # v0.120.0 이상 권장
   ```

2. **설정 파일 확인**
   ```bash
   # config/_default/config.yml 문법 오류 확인
   hugo --config config/_default/config.yml --verbose
   ```

3. **테마 문제 해결**
   ```bash
   # 테마 업데이트
   git submodule update --remote themes/your-theme
   
   # 또는 테마 재설치
   git submodule deinit themes/your-theme
   git submodule add https://github.com/theme-repo themes/your-theme
   ```

### 마크다운 변환 문제

**문제**: 노션 콘텐츠가 올바르게 변환되지 않음

**해결책**:
1. **지원되지 않는 블록 확인**
   ```bash
   # 로그에서 unsupported 블록 찾기
   python notion_hugo_app.py --verbose
   ```

2. **수동 마크다운 편집**
   ```bash
   # content/posts/ 폴더의 마크다운 파일 직접 수정
   ```

3. **노션 콘텐츠 단순화**
   - 복잡한 레이아웃 대신 간단한 구조 사용
   - 지원되는 블록 타입만 사용

## 💻 일반적인 환경 문제

### Python 의존성 문제

**문제**: 모듈을 찾을 수 없다는 오류

**해결책**:
1. **의존성 재설치**
   ```bash
   pip install -r requirements.txt
   
   # 또는 개별 설치
   pip install notion-client pyyaml requests python-frontmatter
   ```

2. **가상환경 사용**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Python 버전 확인**
   ```bash
   python --version
   # Python 3.8 이상 필요
   ```

### Git 관련 문제

**문제**: Git 권한 오류

**해결책**:
1. **GitHub 인증 확인**
   ```bash
   gh auth status
   
   # 로그인이 안되어 있다면
   gh auth login
   ```

2. **SSH 키 설정**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ssh-add ~/.ssh/id_ed25519
   
   # GitHub에 공개 키 등록
   cat ~/.ssh/id_ed25519.pub
   ```

3. **HTTPS 사용**
   ```bash
   git remote set-url origin https://github.com/username/repo.git
   ```

## 🔍 디버깅 팁

### 상세 로그 확인

```bash
# 자세한 로그와 함께 실행
python notion_hugo_app.py --verbose

# 디버그 모드
python notion_hugo_app.py --debug

# 변경사항만 확인 (실제 변경하지 않음)
python notion_hugo_app.py --dry-run
```

### 설정 파일 확인

```bash
# 현재 설정 확인
cat .env
cat notion-hugo.config.yaml

# 샘플 설정과 비교
cat .env.sample
```

### 노션 API 테스트

```bash
# API 연결 테스트
python -c "
from src.notion_api import NotionAPI
api = NotionAPI()
print('API 연결 성공:', api.test_connection())
"
```

## ❓ 추가 도움

문제가 해결되지 않으면:

1. **GitHub Issues**: [프로젝트 이슈 페이지](https://github.com/adalgu/notion-hugo-py/issues)에 문제 신고
2. **로그 첨부**: 오류 메시지와 상세 로그 포함
3. **환경 정보**: OS, Python 버전, 노션 설정 등 명시

문제 신고 시 다음 정보를 포함해주세요:

```bash
# 시스템 정보
python --version
hugo version
git --version

# 프로젝트 상태
python notion_hugo_app.py --version
ls -la .env*
```

---

💡 **팁**: 대부분의 문제는 환경 변수나 권한 설정 문제입니다. `.env` 파일과 GitHub/Vercel 설정을 먼저 확인해보세요!
