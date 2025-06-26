# 🚀 Notion-Hugo: 노션을 블로그로, 3분 안에 완성

> **노션 API 키만 있으면 나머지는 거의 자동화됩니다!**

노션에서 글 쓰고 → 체크박스 클릭 → 자동으로 블로그 배포 ✨

## ⚡ 3분 퀵 스타트

### 1️⃣ 원클릭 배포

#### Vercel로 배포 (추천)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/adalgu/adalgu.github.io)

1. 위 버튼 클릭 → GitHub 연결 → Vercel 배포
2. 환경변수 `NOTION_TOKEN` 설정 ([토큰 받기](https://notion.so/my-integrations))
3. 완료! 🎉

#### GitHub Pages로 배포
```bash
# 원클릭 자동 배포 (추천)
curl -sSL https://raw.githubusercontent.com/adalgu/adalgu.github.io/main/scripts/quick-deploy-github.sh | bash

# 또는 수동 다운로드 후 실행
wget https://raw.githubusercontent.com/adalgu/adalgu.github.io/main/scripts/quick-deploy-github.sh
chmod +x quick-deploy-github.sh
./quick-deploy-github.sh
```

### 2️⃣ 로컬에서 시작

```bash
# 1. 저장소 클론
git clone https://github.com/adalgu/adalgu.github.io.git
cd adalgu.github.io

# 2. 원스톱 설정 실행 (노션 키만 준비하세요!)
# 대화형 모드로 안전하게 설정
python setup.py --interactive

# 또는 명령줄로 바로 실행
# python setup.py --token YOUR_NOTION_TOKEN

# 3. 완료! 블로그가 생성됩니다
```

##  이게 전부예요!

1. **노션 API 키 발급** ([여기서 → ](https://notion.so/my-integrations))
2. **설정 스크립트 실행** (`python setup.py --interactive`)
3. **노션에서 글쓰기** (체크박스만 체크하면 자동 발행!)

## 🎯 주요 특징

- ✅ **3분 설정**: 노션 키 → 스크립트 실행 → 완료
- ✅ **자동 동기화**: 노션 변경사항이 자동으로 블로그에 반영
- ✅ **원클릭 배포**: Vercel/GitHub Pages 즉시 배포
- ✅ **증분 업데이트**: 변경된 포스트만 빠르게 처리
- ✅ **SEO 최적화**: 메타태그, 리디렉션 자동 처리

## 🤔 FAQ

**Q: 어떤 노션 권한이 필요한가요?**
A: `Read content`, `Update content`, `Insert content` 권한만 있으면 됩니다.

**Q: 기존 노션 페이지도 사용할 수 있나요?**
A: 네! 설정 시 "기존 데이터베이스 마이그레이션" 선택하면 됩니다.

**Q: 글 발행은 어떻게 하나요?**
A: 노션에서 `isPublished` 체크박스만 체크하면 자동으로 블로그에 나타납니다.

**Q: 문제가 생기면 어떻게 하나요?**
A: [문제해결 가이드](docs/TROUBLESHOOTING.md)를 확인하세요.

## 📚 더 자세한 가이드

- **[상세 설정 가이드](docs/SETUP_GUIDE.md)** - 고급 설정과 커스터마이징
- **[배포 옵션 비교](docs/DEPLOYMENT_OPTIONS.md)** - Vercel vs GitHub Pages
- **[문제 해결](docs/TROUBLESHOOTING.md)** - 자주 묻는 질문과 해결책

## 🛠️ 로컬 개발

```bash
# 로컬에서 미리보기
python notion_hugo_app.py
hugo server

# 변경사항만 동기화
python notion_hugo_app.py --incremental

# 전체 재빌드 (문제 해결 시)
python notion_hugo_app.py --full-sync
```

## 📄 라이선스

GPL-3.0 License

---

**🎉 이제 노션에서 글을 쓰고 체크박스만 클릭하세요. 나머지는 자동입니다!**
