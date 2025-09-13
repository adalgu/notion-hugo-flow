#!/usr/bin/env python3
"""
Hugo 프로세서 모듈

이 모듈은 Hugo 관련 프로세싱을 담당합니다:
1. Hugo 구조 확인 및 디렉토리 생성
2. 콘텐츠 저장
3. 빌드 전 전처리 (오류 파일 처리)
4. Hugo 빌드 실행

사용 방법:
    # 모듈로 사용
    from src.hugo_processor import HugoProcessor
    processor = HugoProcessor()
    processor.ensure_structure()
    processor.preprocess(['server'])
    processor.build()

    # 또는 명령줄에서 전처리 직접 실행
    python -m src.hugo_processor server
"""

import os
import re
import sys
import shutil
import subprocess
import signal
import tempfile
from datetime import datetime
from typing import List, Dict, Tuple, Set, Optional, Any

# Import config manager for Hugo directory paths
try:
    from ..config import ConfigManager
except ImportError:
    from config import ConfigManager

# 오류 패턴 정의
ERROR_PATTERNS = [
    # Shortcode 관련 오류
    (
        r'failed to extract shortcode: template for shortcode "([^"]+)" not found',
        "shortcode",
    ),
    # YAML 구문 오류
    (r"failed to unmarshal YAML", "yaml"),
    # 참조 오류
    (r"REF_NOT_FOUND", "ref"),
    # 트윗 관련 오류
    (r'The "tweet" shortcode requires two named parameters', "tweet"),
    # 일반 오류 패턴
    (r"error building site:", "build_error"),
    # ERROR 패턴
    (r"ERROR", "error"),
]

# 알려진 문제 shortcode 목록
KNOWN_MISSING_SHORTCODES = ["adsense", "staticref", "tweet"]

# 임시 디렉토리 경로
TEMP_DIR = os.path.join("data", "error_temp")


class HugoProcessor:
    """Hugo 프로세서 클래스"""

    def __init__(
        self, content_dir: Optional[str] = None, output_dir: Optional[str] = None
    ):
        """
        초기화

        Args:
            content_dir: 콘텐츠 디렉토리 경로 (None이면 설정에서 읽음)
            output_dir: 출력 디렉토리 경로 (None이면 설정에서 읽음)
        """
        # 설정에서 Hugo 디렉토리 경로 읽기
        self.config_manager = ConfigManager()

        if content_dir is None:
            self.content_dir = self.config_manager.get_hugo_content_path()
        else:
            self.content_dir = content_dir

        if output_dir is None:
            self.output_dir = self.config_manager.get_hugo_public_path()
        else:
            self.output_dir = output_dir

        self.hugo_root = self.config_manager.get_hugo_root_path()
        self.preprocessor = None

    def ensure_structure(self) -> None:
        """
        Hugo 블로그 구조를 확인하고 필요한 디렉토리를 생성합니다.
        """
        # 콘텐츠 디렉토리 확인 및 생성
        if not os.path.exists(self.content_dir):
            os.makedirs(self.content_dir)

        # 기본 섹션 디렉토리 확인 및 생성
        sections = ["posts", "pages"]
        for section in sections:
            section_path = os.path.join(self.content_dir, section)
            if not os.path.exists(section_path):
                os.makedirs(section_path)

    def save_content(
        self, title: str, content: str, frontmatter: str, target_folder: str = "posts"
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
        target_dir = os.path.join(self.content_dir, target_folder)

        # 디렉토리가 존재하는지 확인하고 없으면 생성
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # 파일 경로 설정
        filepath = os.path.join(target_dir, f"{filename}.md")

        # 파일 저장
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{frontmatter}\n\n{content}")

        return filepath

    def preprocess(self, hugo_args: Optional[List[str]] = None) -> int:
        """
        Hugo 빌드 전 전처리를 실행합니다.

        Args:
            hugo_args: Hugo 명령줄 인수

        Returns:
            종료 코드 (0: 성공, 1: 실패)
        """
        if hugo_args is None:
            hugo_args = []

        self.preprocessor = HugoPreprocessor(hugo_args)
        return self.preprocessor.run()

    def build(self, args: Optional[List[str]] = None) -> int:
        """
        Hugo 사이트를 빌드합니다.

        Args:
            args: Hugo 명령줄 인수

        Returns:
            종료 코드 (0: 성공, 1: 실패)
        """
        if args is None:
            args = ["--minify"]

        cmd = ["hugo"] + args

        try:
            process = subprocess.Popen(cmd, cwd=self.hugo_root)
            return process.wait()
        except Exception as e:
            print(f"빌드 중 오류 발생: {str(e)}")
            return 1

    def run_server(self, port: int = 1313) -> subprocess.Popen:
        """
        Hugo 서버를 실행합니다.

        Args:
            port: 서버 포트 (기본값: 1313)

        Returns:
            실행된 프로세스 객체
        """
        # Hugo 서버 실행 (Hugo 루트 폴더에서)
        process = subprocess.Popen(
            ["hugo", "server", "-D", f"--port={port}"],
            cwd=self.hugo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return process

    def clean_content(self) -> int:
        """
        Hugo 콘텐츠 디렉토리를 정리합니다.

        Returns:
            제거된 파일 수
        """
        removed_count = 0

        # 콘텐츠 디렉토리가 존재하는지 확인
        if not os.path.exists(self.content_dir):
            return removed_count

        # 모든 마크다운 파일 찾기
        for root, dirs, files in os.walk(self.content_dir):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
                    removed_count += 1

        return removed_count


class HugoPreprocessor:
    """Hugo 사전 처리기 클래스"""

    def __init__(self, hugo_args: List[str]):
        """
        초기화

        Args:
            hugo_args: Hugo 명령줄 인수
        """
        self.hugo_args = hugo_args
        self.problematic_files = set()
        self.moved_files = {}  # 원본 파일 경로 -> 임시 파일 경로
        self.error_log = []

        # 설정에서 Hugo 디렉토리 경로 읽기
        self.config_manager = ConfigManager()
        self.hugo_root = self.config_manager.get_hugo_root_path()
        self.content_path = self.config_manager.get_hugo_content_path()

    def run(self) -> int:
        """
        전체 프로세스 실행

        Returns:
            종료 코드 (0: 성공, 1: 실패)
        """
        try:
            # 임시 디렉토리 생성
            self._ensure_temp_dir()

            # 테스트 빌드 실행 및 오류 파일 식별
            self._run_test_build()

            if not self.problematic_files:
                print("문제가 있는 파일이 발견되지 않았습니다. 정상 빌드를 실행합니다.")
                return self._run_hugo()

            # 문제 파일 임시 이동
            self._move_problematic_files()

            # 실제 빌드 실행
            result = self._run_hugo()

            # 이동된 파일 복원
            self._restore_files()

            # 오류 로그 저장
            self._save_error_log()

            return result

        except Exception as e:
            print(f"오류 발생: {str(e)}")
            self._restore_files()  # 오류 발생 시에도 파일 복원 시도
            return 1

    def _ensure_temp_dir(self) -> None:
        """임시 디렉토리가 존재하는지 확인하고 없으면 생성"""
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR, exist_ok=True)

    def _run_test_build(self) -> None:
        """
        테스트 빌드를 실행하여 오류가 있는 파일을 식별
        """
        print("테스트 빌드 실행 중...")

        # Hugo 명령 구성 (빌드만 실행하고 서버는 시작하지 않음)
        cmd = ["hugo"]
        args = self.hugo_args.copy()  # 원본 배열 변경 방지를 위해 복사

        # server 명령어가 있다면 제거
        if "server" in args:
            args.remove("server")

        # 테스트 명령 실행 (Hugo 루트 폴더에서)
        process = subprocess.Popen(
            cmd + args,
            cwd=self.hugo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()

        # 오류 출력 결합 (일부 오류는 stdout으로 출력됨)
        full_output = stdout + "\n" + stderr

        # 오류 메시지 분석하여 문제 파일 식별
        self._parse_error_output(full_output)

        # 직접 파일 검사 (shortcode 관련 문제)
        self._scan_for_problematic_shortcodes()

        # 결과 출력
        if self.problematic_files:
            print(f"{len(self.problematic_files)}개의 문제 파일이 발견되었습니다.")
            for file in sorted(self.problematic_files):
                print(f"  - {file}")
        else:
            print("문제가 있는 파일이 발견되지 않았습니다.")

        # 오류 출력이 있지만 파일을 식별하지 못한 경우 경고 출력
        if (
            "Error:" in full_output or "ERROR" in full_output
        ) and not self.problematic_files:
            print("\n주의: 오류가 감지되었지만 관련 파일을 식별하지 못했습니다.")
            print("오류 메시지:")
            for line in full_output.splitlines():
                if "Error:" in line or "ERROR" in line:
                    print(f"  {line.strip()}")

    def _scan_for_problematic_shortcodes(self) -> None:
        """
        컨텐츠 파일을 스캔하여 문제가 있는 shortcode를 사용하는 파일 식별
        """
        print("파일에서 알려진 문제 shortcode 검색 중...")

        if not os.path.exists(self.content_path):
            print(f"경고: {self.content_path} 디렉토리를 찾을 수 없습니다.")
            return

        md_files = []
        for root, _, files in os.walk(self.content_path):
            for file in files:
                if file.endswith(".md"):
                    md_files.append(os.path.join(root, file))

        for md_file in md_files:
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                for shortcode in KNOWN_MISSING_SHORTCODES:
                    # 다양한 shortcode 패턴 검색
                    patterns = [
                        r"\{\{< " + shortcode + r" [^>]*>\}\}",  # {{< shortcode >}}
                        r"\{\{% " + shortcode + r" [^%]*%\}\}",  # {{% shortcode %}}
                    ]

                    for pattern in patterns:
                        if re.search(pattern, content):
                            self.problematic_files.add(md_file)
                            self.error_log.append(
                                {
                                    "file": md_file,
                                    "error": f"파일에서 문제가 있는 shortcode '{shortcode}'를 발견했습니다.",
                                    "type": "shortcode",
                                }
                            )
                            break
            except Exception as e:
                print(f"파일 스캔 중 오류 발생: {md_file} - {str(e)}")

    def _parse_error_output(self, error_output: str) -> None:
        """
        Hugo 오류 출력을 분석하여 문제가 있는 파일 경로 추출

        Args:
            error_output: Hugo 명령의 출력 (stdout + stderr)
        """
        # 오류가 있는 줄의 컨텍스트 저장
        error_lines = []
        for line in error_output.splitlines():
            if "Error:" in line or "ERROR" in line:
                error_lines.append(line)

        # 오류 메시지를 줄 단위로 처리
        for line in error_output.splitlines():
            # 파일 경로 추출 패턴들
            file_matches = [
                # 기본 큰따옴표 패턴
                re.search(r'"([^"]+\.md)(:\d+:\d+)?"', line),
                # 콜론으로 구분된 경로 패턴
                re.search(r"(/[^:]+\.md)(:\d+:\d+)?", line),
                # 대괄호 내의 경로 패턴
                re.search(r"\[([^\]]+\.md)\]", line),
            ]

            file_match = next((m for m in file_matches if m), None)

            if not file_match:
                # 특별한 오류 패턴 - REF_NOT_FOUND 유형의 오류
                ref_match = re.search(r"page not found\s*$", line)
                if ref_match:
                    # 이전 행에서 파일 경로 추출 시도
                    for prev_line in error_lines:
                        file_match = re.search(r'"([^"]+\.md)', prev_line)
                        if file_match:
                            break

            if file_match:
                file_path = file_match.group(1)

                # 절대 경로를 상대 경로로 변환
                if file_path.startswith("/"):
                    content_dir_match = re.search(r"/content/(.+)", file_path)
                    if content_dir_match:
                        file_path = os.path.join("content", content_dir_match.group(1))

                # 오류 유형 식별
                error_type = "unknown"
                for pattern, err_type in ERROR_PATTERNS:
                    if re.search(pattern, line):
                        error_type = err_type
                        break

                # 오류 로그에 추가
                self.error_log.append(
                    {"file": file_path, "error": line.strip(), "type": error_type}
                )

                # 문제 파일 목록에 추가
                if os.path.exists(file_path):
                    self.problematic_files.add(file_path)

    def _move_problematic_files(self) -> None:
        """문제가 있는 파일을 임시 디렉토리로 이동"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for original_path in self.problematic_files:
            if not os.path.exists(original_path):
                continue

            # 파일 이름에 타임스탬프 추가하여 충돌 방지
            filename = os.path.basename(original_path)
            temp_path = os.path.join(TEMP_DIR, f"{timestamp}_{filename}")

            # 파일 이동
            try:
                shutil.move(original_path, temp_path)
                self.moved_files[original_path] = temp_path
                print(f"파일 이동: {original_path} -> {temp_path}")
            except Exception as e:
                print(f"파일 이동 실패: {original_path} - {str(e)}")

    def _restore_files(self) -> None:
        """임시로 이동된 파일을 원래 위치로 복원"""
        if not self.moved_files:
            return

        print("이동된 파일 복원 중...")
        for original_path, temp_path in self.moved_files.items():
            if os.path.exists(temp_path):
                # 원본 경로의 디렉토리가 존재하는지 확인
                original_dir = os.path.dirname(original_path)
                if not os.path.exists(original_dir):
                    os.makedirs(original_dir, exist_ok=True)

                # 파일 복원
                try:
                    shutil.move(temp_path, original_path)
                    print(f"파일 복원: {temp_path} -> {original_path}")
                except Exception as e:
                    print(f"파일 복원 실패: {temp_path} - {str(e)}")

    def _run_hugo(self) -> int:
        """
        실제 Hugo 빌드 실행

        Returns:
            종료 코드
        """
        print("Hugo 빌드 실행 중...")

        # Hugo 명령 구성
        cmd = ["hugo"]
        if self.hugo_args:
            cmd.extend(self.hugo_args)

        # 실행 (Hugo 루트 폴더에서)
        process = subprocess.Popen(cmd, cwd=self.hugo_root)
        return process.wait()

    def _save_error_log(self) -> None:
        """오류 로그를 파일로 저장"""
        if not self.error_log:
            return

        log_path = os.path.join("docs", "build_errors.json")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        import json

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "errors": self.error_log,
                    "excluded_files": list(self.problematic_files),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"오류 로그가 저장되었습니다: {log_path}")


def handle_signal(sig, frame):
    """
    인터럽트 시그널 처리 핸들러
    """
    print("\n인터럽트 시그널을 받았습니다. 종료합니다.")
    sys.exit(130)  # 130은 SIGINT에 의한 종료를 나타내는 표준 종료 코드


def main():
    """메인 함수 - 명령줄에서 실행될 때 사용"""
    # 시그널 핸들러 설정
    signal.signal(signal.SIGINT, handle_signal)

    # 명령줄 인수 처리 (첫 번째 인수는 스크립트 이름이므로 제외)
    hugo_args = sys.argv[1:] if len(sys.argv) > 1 else []

    # 전처리기 실행
    preprocessor = HugoPreprocessor(hugo_args)
    result = preprocessor.run()

    # 종료 코드로 프로세스 종료
    sys.exit(result)


class ContentProcessor:
    """
    Stage 2: notion_markdown/ → hugo_markdown/
    
    Process Notion markdown for Hugo compatibility and optimization.
    """
    
    def __init__(self, input_dir: str = "notion_markdown", output_dir: str = "hugo_markdown"):
        """
        Initialize ContentProcessor.
        
        Args:
            input_dir: Input directory with Notion markdown files
            output_dir: Output directory for Hugo-compatible markdown
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_count = 0
        self.errors = []
        
    def run(self) -> dict:
        """
        Execute Stage 2 processing.
        
        Returns:
            Dictionary with processing results
        """
        import os
        import shutil
        from pathlib import Path
        
        try:
            print(f"[Info] ContentProcessor: {self.input_dir}/ → {self.output_dir}/")
            
            # Ensure output directories exist
            Path(f"{self.output_dir}/posts").mkdir(parents=True, exist_ok=True)
            Path(f"{self.output_dir}/pages").mkdir(parents=True, exist_ok=True)
            
            # Process files in both subdirectories
            for subdir in ['posts', 'pages']:
                input_path = Path(self.input_dir) / subdir
                output_path = Path(self.output_dir) / subdir
                
                if not input_path.exists():
                    continue
                    
                for md_file in input_path.glob("*.md"):
                    try:
                        # Read input file
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Process content for Hugo compatibility
                        processed_content = self._process_content_for_hugo(content)
                        
                        # Write to output
                        output_file = output_path / md_file.name
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(processed_content)
                        
                        self.processed_count += 1
                        print(f"[Info] Processed: {md_file.name}")
                        
                    except Exception as e:
                        error_msg = f"Failed to process {md_file}: {str(e)}"
                        print(f"[Error] {error_msg}")
                        self.errors.append(error_msg)
            
            return {
                "success": len(self.errors) == 0,
                "processed_count": self.processed_count,
                "input_dir": self.input_dir,
                "output_dir": self.output_dir,
                "errors": self.errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processed_count": self.processed_count
            }
    
    def _process_content_for_hugo(self, content: str) -> str:
        """
        Process markdown content for Hugo compatibility.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Hugo-compatible markdown content
        """
        import re
        
        # Hugo-specific processing
        processed = content
        
        # Fix common Hugo issues
        # 1. Clean up empty lines in frontmatter
        processed = re.sub(r'---\n\n+', '---\n', processed)
        
        # 2. Ensure proper spacing after frontmatter
        processed = re.sub(r'---\n([^\n])', r'---\n\n\1', processed)
        
        # 3. Clean up excessive newlines
        processed = re.sub(r'\n{3,}', '\n\n', processed)
        
        # 4. Fix shortcode formatting if needed
        processed = re.sub(r'\{\{<\s+(\w+)', r'{{< \1', processed)
        processed = re.sub(r'(\w+)\s+>\}\}', r'\1 >}}', processed)
        
        return processed


if __name__ == "__main__":
    main()
