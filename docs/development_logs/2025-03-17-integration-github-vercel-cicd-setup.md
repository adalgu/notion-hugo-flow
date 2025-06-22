# [GitHub Actions & Vercel CI/CD 설정]

- **날짜**: 2025-03-17
- **작성자**: Gunn.kim
- **관련 이슈**: 없음
- **이전 로그**: 없음

## 문제 상황
Notion-Hugo 프로젝트의 콘텐츠 동기화 및 배포 과정을 자동화할 필요가 있었습니다. 수동으로 Notion 콘텐츠를 변환하고 Hugo 사이트를 빌드하여 배포하는 작업은 비효율적이며, 오류 발생 가능성이 높았습니다.

## 해결 전략
GitHub Actions와 Vercel을 연동하여 CI/CD 파이프라인을 구축했습니다. 이 전략의 핵심은 다음과 같습니다:
1.  **콘텐츠 동기화 자동화**: GitHub Actions를 사용하여 주기적으로 Notion의 콘텐츠를 가져와 Hugo가 사용할 수 있는 마크다운 파일로 변환하고, 변경사항을 GitHub 저장소에 자동으로 커밋합니다.
2.  **배포 자동화**: Vercel의 GitHub 통합 기능을 활용하여, 저장소의 특정 브랜치에 새로운 커밋이 푸시될 때마다 자동으로 사이트 빌드 및 배포를 트리거합니다.

## 구현 세부사항
### GitHub Secrets 설정
- 워크플로우가 Notion API에 안전하게 접근할 수 있도록 `NOTION_TOKEN`을 GitHub 저장소의 Secrets에 추가했습니다.
- 설정 방법은 GitHub CLI 또는 웹 인터페이스를 통해 가능합니다.

### GitHub Actions 워크플로우
- `.github/workflows/notion-sync.yml` 워크플로우는 6시간마다 자동으로 실행되도록 `cron` 스케줄을 설정했습니다.
- 워크플로우는 Notion 콘텐츠를 동기화하고, 변경된 내용이 있을 경우 저장소에 커밋합니다.

### Vercel 배포 설정
- Vercel 프로젝트를 GitHub 저장소에 연결했습니다.
- `vercel.json` 파일을 통해 Hugo 프레임워크를 사용하도록 빌드 설정을 구성했습니다.
- 저장소에 새로운 커밋이 발생하면 Vercel이 이를 감지하여 자동으로 배포를 수행합니다.

## 기술적 고려사항
- **실행 주기**: 동기화 주기(cron)는 필요에 따라 조절할 수 있습니다. 너무 잦은 실행은 불필요한 리소스를 사용할 수 있습니다.
- **보안**: Notion API 토큰과 같은 민감한 정보는 반드시 GitHub Secrets를 통해 관리하여 코드에 노출되지 않도록 해야 합니다.
- **문제 해결**: Actions 워크플로우나 Vercel 배포 실패 시, 각 서비스의 대시보드에서 로그를 확인하여 원인을 파악할 수 있습니다.

## 다음 단계
- Vercel 배포 상태 알림 설정 (Slack, 이메일 등)
- 동기화 실패 시 알림 기능 추가

## 참고 자료
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [Vercel 문서](https://vercel.com/docs)
