    return guide


def check_deployment_readiness():
    """배포 준비 상태 체크"""
    checks = {
        "notion_token": bool(os.environ.get("NOTION_TOKEN")),
        "database_id": bool(os.environ.get("NOTION_DATABASE_ID_POSTS")),
        "dependencies": True,  # 이미 설치했으므로 True
    }
    
    if checks["notion_token"] and checks["database_id"]:
        return "ready", checks
    elif checks["notion_token"] and not checks["database_id"]:
        return "needs_db_id", checks
    else:
        return "needs_token", checks


def generate_error_guide(error_type, details=None):
    """에러별 맞춤 가이드 생성"""
    guides = {
        "token_missing": """
❌ NOTION_TOKEN 환경변수가 설정되지 않았습니다.

📋 해결 방법:
1. https://notion.so/my-integrations 에서 새 통합 생성
2. API 키 복사 (ntn_로 시작하는 문자열)
3. Vercel Dashboard → Settings → Environment Variables
4. NOTION_TOKEN 변수 추가 (Production 환경 체크)
""",
        "token_invalid": f"""
❌ Notion 토큰이 유효하지 않습니다.

원인: {details if details else "API 호출 실패"}

📋 해결 방법:
1. https://notion.so/my-integrations 에서 토큰 재확인
2. 토큰이 'ntn_'로 시작하는지 확인
3. 통합에 올바른 권한이 있는지 확인:
   - Read content
   - Insert content
   - Update content
""",
        "permission_denied": """
❌ Notion 통합에 필요한 권한이 없습니다.

📋 해결 방법:
1. https://notion.so/my-integrations → 통합 선택
2. Capabilities 섹션에서 다음 권한 활성화:
   - Read content ✅
   - Insert content ✅
   - Update content ✅
3. 변경 사항 저장 후 재배포
""",
        "database_creation_failed": f"""
❌ 데이터베이스 생성에 실패했습니다.

원인: {details if details else "알 수 없는 오류"}

📋 해결 방법:
1. Notion 워크스페이스에 페이지 하나 이상 있는지 확인
2. 통합이 해당 페이지에 접근 권한이 있는지 확인
3. 네트워크 연결 상태 확인
4. 잠시 후 재시도
"""
    }
    
    return guides.get(error_type, f"알 수 없는 오류: {error_type}")


def test_notion_connection(token):
    """Notion 연결 테스트"""
    try:
        from notion_client import Client
        from notion_client.errors import APIResponseError
        
        notion = Client(auth=token)
        
        # 기본 연결 테스트
        search_result = notion.search(query="", page_size=1)
        
        # 권한 테스트
        if hasattr(search_result, 'results') or isinstance(search_result, dict):
            return True, "연결 성공"
        else:
            return False, "예상하지 못한 응답 형식"
            
    except APIResponseError as e:
        return False, f"API 오류: {str(e)}"
    except Exception as e:
        return False, f"연결 오류: {str(e)}"


def main():
    """
    개선된 Vercel 설정 메인 함수
    
    배포 상태를 추적하고 단계별로 안내합니다.
    """
    load_dotenv()
    install_dependencies()

    # 배포 상태 확인
    deployment_state = create_deployment_state()
    
    print(f"🚀 Vercel 배포 설정 시작 (배포 #{deployment_state['deployment_count']})")
    
    from setup import OneStopInstaller

    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID_POSTS")

    # 배포 준비 상태 체크
    readiness, checks = check_deployment_readiness()
    
    if readiness == "needs_token":
        print(generate_error_guide("token_missing"))
        sys.exit(1)
    
    if readiness == "ready":
        print("✅ 모든 환경변수가 설정되었습니다. 콘텐츠 동기화를 시작합니다.")
        update_deployment_state({
            "deployment_stage": "sync_ready",
            "database_id": database_id
        })
        # 정상적인 동기화 프로세스로 진행
        sys.exit(0)
    
    # needs_db_id 상황: DB 생성 필요
    print("ℹ️ NOTION_DATABASE_ID_POSTS가 설정되지 않았습니다.")
    print("📊 새로운 Notion 데이터베이스를 생성합니다...")

    # 토큰 연결 테스트
    is_connected, connection_message = test_notion_connection(notion_token)
    if not is_connected:
        print(generate_error_guide("token_invalid", connection_message))
        sys.exit(1)
    
    print("✅ Notion 연결 테스트 통과")

    installer = OneStopInstaller(notion_token, interactive=False)

    # 토큰 검증
    is_valid, message = installer.validate_notion_token()
    if not is_valid:
        print(generate_error_guide("token_invalid", message))
        sys.exit(1)

    print("✅ Notion 토큰 검증 완료")

    # 권한 확인
    permissions = installer.detect_notion_permissions()
    if not permissions.get("can_create_database"):
        print(generate_error_guide("permission_denied"))
        sys.exit(1)

    print("✅ Notion 권한 확인 완료")

    # 데이터베이스 생성
    try:
        db_result = installer.create_optimized_database(permissions)
        if not db_result.get("success"):
            error_detail = db_result.get("error", "알 수 없는 오류")
            print(generate_error_guide("database_creation_failed", error_detail))
            sys.exit(1)

        new_db_id = db_result.get("database_id")
        print(f"✅ 새 데이터베이스 생성 완료: {new_db_id}")

    except Exception as e:
        print(generate_error_guide("database_creation_failed", str(e)))
        sys.exit(1)

    # 샘플 포스트 생성
    installer.database_id = new_db_id
    try:
        posts_result = installer.create_sample_posts()
        
        if posts_result.get("success"):
            print(f"✅ 샘플 포스트 {posts_result.get('count', 0)}개 생성 완료")
        else:
            print("⚠️ 샘플 포스트 생성 실패 (데이터베이스는 정상 생성됨)")
            print(f"   원인: {posts_result.get('error', '알 수 없음')}")
    
    except Exception as e:
        print(f"⚠️ 샘플 포스트 생성 중 오류: {str(e)}")
        print("   데이터베이스는 정상적으로 생성되었습니다.")

    # 배포 상태 업데이트
    update_deployment_state({
        "deployment_stage": "database_created",
        "database_created": True,
        "database_id": new_db_id
    })

    # 사용자 가이드 출력
    token_masked = f"{notion_token[:8]}...{notion_token[-4:]}" if len(notion_token) > 12 else "****"
    guide = generate_setup_guide(new_db_id, token_masked)
    print(guide)

    # 추가 도움말
    print("""
💡 추가 도움말:
- 환경변수 설정이 완료되면 자동으로 Notion 콘텐츠가 동기화됩니다
- 생성된 샘플 포스트를 참고하여 새 포스트를 작성할 수 있습니다
- 문제가 발생하면 GitHub Issues에서 도움을 요청하세요

🔗 유용한 링크:
- Vercel 환경변수 가이드: https://vercel.com/docs/projects/environment-variables
- Notion API 가이드: https://developers.notion.com/docs/getting-started
- 프로젝트 문서: https://github.com/your-username/notion-hugo-blog
""")

    # 빌드 실패로 사용자 액션 유도
    print("🛑 현재 빌드를 중단합니다. 위 가이드를 따라 환경변수를 설정한 후 재배포하세요.")
    sys.exit(1)


if __name__ == "__main__":
    main()
