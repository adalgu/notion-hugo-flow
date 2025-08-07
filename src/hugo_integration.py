import os
import shutil
import subprocess
from typing import Dict, List, Any, Optional

# Import config manager for Hugo directory paths
try:
    from .config import ConfigManager
except ImportError:
    from config import ConfigManager


def ensure_hugo_structure(content_dir: str = "content") -> None:
    """
    Hugo 블로그 구조를 확인하고 필요한 디렉토리를 생성합니다.

    Args:
        content_dir: 콘텐츠 디렉토리 경로
    """
    # 콘텐츠 디렉토리 확인 및 생성
    if not os.path.exists(content_dir):
        os.makedirs(content_dir)

    # 기본 섹션 디렉토리 확인 및 생성
    sections = ["posts", "pages"]
    for section in sections:
        section_path = os.path.join(content_dir, section)
        if not os.path.exists(section_path):
            os.makedirs(section_path)


def save_hugo_content(
    title: str, content: str, frontmatter: str, target_folder: str = "posts"
) -> str:
    """
    Hugo 블로그 콘텐츠를 저장합니다.

    Args:
        title: 콘텐츠 제목
        content: 마크다운 콘텐츠
        frontmatter: YAML 프론트매터
        target_folder: 대상 폴더 (기본값: posts)

    Returns:
        저장된 파일 경로
    """
    # 파일명 생성 (제목에서 특수문자 제거 및 공백을 하이픈으로 변환)
    filename = title.lower()
    filename = "".join(c if c.isalnum() or c.isspace() else "-" for c in filename)
    filename = "-".join(filename.split())

    # 대상 디렉토리 설정
    target_dir = os.path.join("content", target_folder)

    # 디렉토리가 존재하는지 확인하고 없으면 생성
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # 파일 경로 설정
    filepath = os.path.join(target_dir, f"{filename}.md")

    # 파일 저장
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{frontmatter}\n\n{content}")

    return filepath


def run_hugo_server(port: int = 1313) -> subprocess.Popen:
    """
    Hugo 서버를 실행합니다.

    Args:
        port: 서버 포트 (기본값: 1313)

    Returns:
        실행된 프로세스 객체
    """
    # Hugo 서버 실행
    process = subprocess.Popen(
        ["hugo", "server", "-D", f"--port={port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return process


def build_hugo_site() -> bool:
    """
    Hugo 사이트를 빌드합니다.

    Returns:
        빌드 성공 여부
    """
    try:
        # 설정에서 Hugo 루트 경로 읽기
        config_manager = ConfigManager()
        hugo_root = config_manager.get_hugo_root_path()

        # Hugo 빌드 실행 (Hugo 루트 폴더에서)
        result = subprocess.run(
            ["hugo", "--minify"],
            cwd=hugo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        return True
    except subprocess.CalledProcessError:
        return False


def clean_hugo_content(content_dir: str = "content") -> int:
    """
    Hugo 콘텐츠 디렉토리를 정리합니다.

    Args:
        content_dir: 콘텐츠 디렉토리 경로

    Returns:
        제거된 파일 수
    """
    removed_count = 0

    # 콘텐츠 디렉토리가 존재하는지 확인
    if not os.path.exists(content_dir):
        return removed_count

    # 모든 마크다운 파일 찾기
    for root, dirs, files in os.walk(content_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                removed_count += 1

    return removed_count
