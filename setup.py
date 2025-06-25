#!/usr/bin/env python3
"""
Notion-Hugo 통합 설정 스크립트

이 스크립트는 노션 API 키만으로 전체 블로그 시스템을 자동 설정합니다.
- 노션 데이터베이스 자동 생성
- 설정 파일 자동 구성
- 배포 환경 자동 설정 (GitHub Pages 또는 Vercel)

사용법:
    python setup.py --token YOUR_TOKEN --deploy github-pages
    python setup.py --token YOUR_TOKEN --deploy vercel
    python setup.py --interactive
    python setup.py -i
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path


def print_banner():
    """환영 메시지 출력"""
    print(
        """
🚀 Notion-Hugo 통합 설정
========================================
노션 키만으로 3분 안에 블로그 완성!

준비물: 노션 API 키 (https://notion.so/my-integrations)
결과물: 완전히 작동하는 블로그 + 자동 배포
========================================
"""
    )


def validate_notion_token(token):
    """노션 토큰 유효성 검사"""
    if not token:
        return False, "토큰이 비어있습니다."

    if not token.startswith("secret_"):
        return False, "노션 토큰은 'secret_'로 시작해야 합니다."

    if len(token) < 50:
        return False, "토큰이 너무 짧습니다. 올바른 노션 토큰인지 확인하세요."

    return True, "유효한 토큰입니다."


def setup_environment(token):
    """환경 설정"""
    print("📝 환경 설정 중...")

    # .env 파일 생성
    env_content = f"NOTION_TOKEN={token}\n"
    with open(".env", "w") as f:
        f.write(env_content)

    print("✅ .env 파일 생성 완료")

    # 환경변수 설정
    os.environ["NOTION_TOKEN"] = token

    return True


def install_dependencies():
    """Python 의존성 설치"""
    print("📦 Python 의존성 설치 중...")

    dependencies = ["notion-client", "python-dotenv", "pyyaml", "fs", "tabulate"]

    try:
        for dep in dependencies:
            print(f"  - {dep} 설치 중...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                check=True,
                capture_output=True,
                text=True,
            )

        print("✅ 의존성 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 의존성 설치 실패: {e}")
        return False


def setup_notion_database(token, auto_yes=False):
    """노션 데이터베이스 설정"""
    print("🗃️ 노션 데이터베이스 설정 중...")

    try:
        # 기존 notion_setup.py 활용
        if auto_yes:
            # 자동 설정 모드
            result = subprocess.run(
                [sys.executable, "notion_hugo_app.py", "-i"],
                capture_output=True,
                text=True,
                input="\n".join(
                    [
                        "1",  # 새 데이터베이스 생성
                        "Hugo Blog Posts",  # 데이터베이스 이름
                        "",  # 워크스페이스 루트 사용
                        "y",  # 샘플 포스트 생성
                    ]
                ),
            )
        else:
            # 일반 대화형 모드
            result = subprocess.run(
                [sys.executable, "notion_hugo_app.py", "-i"],
                capture_output=True,
                text=True,
                input="\n".join(
                    [
                        "1",  # 새 데이터베이스 생성
                        "Hugo Blog Posts",  # 데이터베이스 이름
                        "",  # 워크스페이스 루트 사용
                        "y",  # 샘플 포스트 생성
                    ]
                ),
            )

        if result.returncode == 0:
            print("✅ 노션 데이터베이스 설정 완료")
            return True
        else:
            print(f"❌ 노션 데이터베이스 설정 실패: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 노션 데이터베이스 설정 중 오류: {e}")
        return False


def setup_vercel_deployment():
    """Vercel 배포 설정"""
    print("🚀 Vercel 배포 설정 중...")

    # vercel.json 최적화
    vercel_config = {
        "build": {
            "env": {
                "HUGO_VERSION": "0.140.0",
                "HUGO_ENV": "production",
                "HUGO_EXTENDED": "true",
            }
        },
        "buildCommand": "pip install notion-client python-dotenv pyyaml fs tabulate && python notion_hugo_app.py && hugo --gc --minify",
        "outputDirectory": "public",
        "framework": "hugo",
    }

    with open("vercel.json", "w") as f:
        json.dump(vercel_config, f, indent=2)

    print("✅ vercel.json 최적화 완료")

    # Vercel CLI 확인
    try:
        subprocess.run(["vercel", "--version"], check=True, capture_output=True)

        print("🔗 Vercel 배포를 시작합니다...")
        print("📋 다음 단계를 따라하세요:")
        print("   1. 브라우저에서 Vercel에 로그인")
        print("   2. 환경변수 NOTION_TOKEN 설정")
        print("   3. 배포 완료 대기")

        # Vercel 배포 실행
        subprocess.run(["vercel", "--prod"], check=False)

        return True

    except FileNotFoundError:
        print("📱 Vercel CLI가 설치되지 않았습니다.")
        print("🔗 Vercel 웹사이트에서 수동 배포:")
        print("   1. https://vercel.com/new 방문")
        print("   2. GitHub 저장소 연결")
        print(
            f"   3. 환경변수 NOTION_TOKEN = {os.environ.get('NOTION_TOKEN', 'YOUR_TOKEN')}"
        )
        print("   4. Deploy 클릭")
        return True


def setup_github_pages():
    """GitHub Pages 배포 설정"""
    print("📄 GitHub Pages 배포 설정 중...")

    # GitHub CLI 확인
    try:
        subprocess.run(["gh", "--version"], check=True, capture_output=True)
    except FileNotFoundError:
        print("❌ GitHub CLI가 설치되지 않았습니다.")
        print("📥 설치 방법:")
        print("   - macOS: brew install gh")
        print("   - Windows: winget install GitHub.CLI")
        print("   - Linux: https://cli.github.com/manual/installation")
        return False

    # 기존 스크립트 실행
    script_path = Path("scripts/github-pages-setup.sh")
    if script_path.exists():
        try:
            subprocess.run(["bash", str(script_path)], check=True)
            print("✅ GitHub Pages 설정 완료")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ GitHub Pages 설정 실패: {e}")
            return False
    else:
        print("❌ GitHub Pages 설정 스크립트를 찾을 수 없습니다.")
        return False


def test_setup():
    """설정 테스트"""
    print("🧪 설정 테스트 중...")

    try:
        # 드라이런 테스트
        result = subprocess.run(
            [sys.executable, "notion_hugo_app.py", "--dry-run"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ 설정 테스트 통과")
            return True
        else:
            print(f"❌ 설정 테스트 실패: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        return False


def show_completion_message(deploy_type):
    """완료 메시지 출력"""
    print(
        """
🎉 설정 완료!
========================================
"""
    )

    if deploy_type == "github-pages":
        print("📄 GitHub Pages 배포 완료")
        print("🔗 블로그 주소: https://YOUR_USERNAME.github.io")
        print("⚡ 자동 동기화: 2시간마다 노션 → 블로그 업데이트")
    elif deploy_type == "vercel":
        print("🚀 Vercel 배포 완료")
        print("🔗 블로그 주소: Vercel 대시보드에서 확인")
        print("⚡ 자동 동기화: Git 푸시할 때마다 업데이트")

    print(
        """
📝 이제 할 일:
1. 노션에서 블로그 포스트 작성
2. 'isPublished' 체크박스 체크
3. 자동으로 블로그에 반영!

📚 도움말:
- 상세 가이드: docs/SETUP_GUIDE.md
- 배포 옵션: docs/DEPLOYMENT_OPTIONS.md
- 문제 해결: docs/TROUBLESHOOTING.md
========================================
"""
    )


def interactive_setup():
    """대화형 설정"""
    print_banner()

    # 노션 토큰 입력
    while True:
        token = input("🔑 노션 API 토큰을 입력하세요: ").strip()
        is_valid, message = validate_notion_token(token)
        if is_valid:
            print(f"✅ {message}")
            break
        else:
            print(f"❌ {message}")
            print("💡 토큰 받는 방법: https://notion.so/my-integrations")

    # 배포 방식 선택
    while True:
        print("\n🚀 배포 방식을 선택하세요:")
        print("1. Vercel (추천) - 클릭 몇 번으로 완료")
        print("2. GitHub Pages - 무료, 안정적")

        choice = input("선택 (1 또는 2): ").strip()
        if choice == "1":
            deploy_type = "vercel"
            break
        elif choice == "2":
            deploy_type = "github-pages"
            break
        else:
            print("❌ 1 또는 2를 입력하세요.")

    return run_setup(token, deploy_type, auto_yes=False)


def run_setup(token, deploy_type, auto_yes=False):
    """실제 설정 실행"""
    print(f"\n🔧 설정 시작 (배포: {deploy_type})")

    # 단계별 설정
    steps = [
        ("환경 설정", lambda: setup_environment(token)),
        ("의존성 설치", install_dependencies),
        ("노션 데이터베이스 설정", lambda: setup_notion_database(token, auto_yes)),
    ]

    if deploy_type == "vercel":
        steps.append(("Vercel 배포 설정", setup_vercel_deployment))
    elif deploy_type == "github-pages":
        steps.append(("GitHub Pages 배포 설정", setup_github_pages))

    steps.append(("설정 테스트", test_setup))

    # 단계 실행
    for i, (step_name, step_func) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {step_name}")
        try:
            if not step_func():
                print(f"❌ {step_name} 실패")
                return False
        except Exception as e:
            print(f"❌ {step_name} 중 오류: {e}")
            return False

    # 완료 메시지
    show_completion_message(deploy_type)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Notion-Hugo 통합 설정 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python setup.py --token secret_abc123 --deploy vercel
  python setup.py --token secret_abc123 --deploy github-pages
  python setup.py --interactive
  python setup.py -i
        """,
    )

    parser.add_argument("--token", help="노션 API 토큰")
    parser.add_argument(
        "--deploy", choices=["vercel", "github-pages"], help="배포 방식 선택"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="대화형 설정 모드"
    )
    parser.add_argument(
        "--auto-yes",
        action="store_true",
        help="모든 질문에 자동으로 yes 응답 (비대화형 모드용)",
    )

    args = parser.parse_args()

    # 대화형 모드
    if args.interactive:
        return interactive_setup()

    # 명령줄 모드
    if not args.token:
        print("❌ --token 또는 --interactive 옵션이 필요합니다.")
        parser.print_help()
        return False

    if not args.deploy:
        print("❌ --deploy 옵션이 필요합니다. (vercel 또는 github-pages)")
        parser.print_help()
        return False

    # 토큰 검증
    is_valid, message = validate_notion_token(args.token)
    if not is_valid:
        print(f"❌ 토큰 오류: {message}")
        return False

    print_banner()
    return run_setup(args.token, args.deploy, args.auto_yes)


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ 사용자가 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        sys.exit(1)
