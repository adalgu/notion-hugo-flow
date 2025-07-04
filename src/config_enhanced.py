#!/usr/bin/env python3
"""
개선된 설정 관리 시스템

주요 개선사항:
1. 환경변수 우선 처리 (Environment Variables First)
2. 동적 데이터베이스 ID 처리 
3. 배포 환경별 설정 분리
4. 설정 검증 및 자동 복구
5. 보안 강화 (민감 정보 마스킹)
"""

import os
import re
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, TypedDict, Any, Union
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError


# 타입 정의 (기존 유지)
class PageMount(TypedDict):
    page_id: str
    target_folder: str


class DatabaseMount(TypedDict):
    database_id: str
    target_folder: str


class Mount(TypedDict):
    databases: List[DatabaseMount]
    pages: List[PageMount]


class FilenameConfig(TypedDict):
    format: str
    date_format: str
    korean_title: str


class DeploymentConfig(TypedDict):
    auto_deploy: bool
    trigger: str
    schedule: Optional[str]
    environment: str


class SecurityConfig(TypedDict):
    use_environment_variables: bool
    mask_sensitive_logs: bool
    token_validation: bool


class Config(TypedDict):
    mount: Mount
    filename: Optional[FilenameConfig]
    deployment: Optional[DeploymentConfig]
    security: Optional[SecurityConfig]


class ConfigManager:
    """개선된 설정 관리자"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.env_vars_loaded = False
        self._load_environment()
    
    def _get_default_config_path(self) -> str:
        """기본 설정 파일 경로 반환"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_dir, "notion-hugo.config.yaml")
    
    def _load_environment(self):
        """환경변수 로드"""
        if not self.env_vars_loaded:
            load_dotenv()
            self.env_vars_loaded = True
    
    def _mask_sensitive_value(self, value: str, mask_type: str = "token") -> str:
        """민감한 값 마스킹"""
        if not value:
            return "[NOT_SET]"
        
        if mask_type == "token":
            return f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "****"
        elif mask_type == "id":
            return f"{value[:8]}...{value[-8:]}" if len(value) > 16 else "****"
        else:
            return "****"
    
    def validate_notion_token(self, token: str) -> tuple[bool, str]:
        """Notion 토큰 검증"""
        if not token:
            return False, "토큰이 설정되지 않았습니다."
        
        if not token.startswith("ntn_"):
            return False, "올바른 Notion 토큰 형식이 아닙니다. (ntn_로 시작해야 함)"
        
        if len(token) < 50:
            return False, "토큰 길이가 너무 짧습니다."
        
        # API 연결 테스트
        try:
            notion = Client(auth=token)
            notion.search(query="", page_size=1)
            return True, "토큰이 유효합니다."
        except APIResponseError as e:
            return False, f"API 호출 실패: {str(e)}"
        except Exception as e:
            return False, f"연결 테스트 실패: {str(e)}"
    
    def get_database_id_from_env(self, folder_name: str = "posts") -> Optional[str]:
        """환경변수에서 데이터베이스 ID 가져오기"""
        # 여러 가능한 환경변수 이름 확인
        possible_keys = [
            f"NOTION_DATABASE_ID_{folder_name.upper()}",
            f"NOTION_DATABASE_{folder_name.upper()}",
            f"NOTION_{folder_name.upper()}_DB_ID",
            "NOTION_DATABASE_ID_POSTS",  # 기본값
            "NOTION_DATABASE_ID"
        ]
        
        for key in possible_keys:
            value = os.environ.get(key)
            if value and value.strip():
                return value.strip()
        
        return None
    
    def create_default_config_if_missing(self):
        """기본 설정 파일이 없으면 생성"""
        if not os.path.exists(self.config_path):
            default_config = {
                "mount": {
                    "databases": [],
                    "manual": True
                },
                "filename": {
                    "format": "date-title",
                    "date_format": "%Y-%m-%d",
                    "korean_title": "slug"
                },
                "deployment": {
                    "auto_deploy": True,
                    "trigger": "push",
                    "environment": "production"
                },
                "security": {
                    "use_environment_variables": True,
                    "mask_sensitive_logs": True,
                    "token_validation": True
                }
            }
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            
            print(f"✅ 기본 설정 파일 생성: {self.config_path}")
    
    def load_config(self) -> Config:
        """
        개선된 설정 로드 (환경변수 우선)
        
        우선순위:
        1. 환경변수
        2. YAML 설정 파일
        3. 기본값
        """
        self._load_environment()
        self.create_default_config_if_missing()
        
        # YAML 설정 파일 로드
        file_config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️ 설정 파일 로드 실패: {e}")
                file_config = {}
        
        # 기본 설정 구성
        config: Config = {
            "mount": {"databases": [], "pages": []},
            "filename": {
                "format": "date-title",
                "date_format": "%Y-%m-%d", 
                "korean_title": "slug"
            },
            "deployment": {
                "auto_deploy": True,
                "trigger": "push",
                "schedule": None,
                "environment": "production"
            },
            "security": {
                "use_environment_variables": True,
                "mask_sensitive_logs": True,
                "token_validation": True
            }
        }
        
        # 파일 설정 병합
        if "filename" in file_config:
            config["filename"].update(file_config["filename"])
        
        if "deployment" in file_config:
            config["deployment"].update(file_config["deployment"])
        
        if "security" in file_config:
            config["security"].update(file_config["security"])
        
        # 마운트 설정 처리 (환경변수 우선)
        self._process_mount_config(config, file_config)
        
        return config
    
    def _process_mount_config(self, config: Config, file_config: Dict[str, Any]):
        """마운트 설정 처리 (환경변수 우선)"""
        mount_config = file_config.get("mount", {})
        
        if mount_config.get("manual", True):
            # 수동 설정 모드
            if "databases" in mount_config:
                for db_config in mount_config["databases"]:
                    folder = db_config.get("target_folder", "posts")
                    
                    # 1. 환경변수에서 DB ID 찾기 (최우선)
                    env_db_id = self.get_database_id_from_env(folder)
                    
                    # 2. 파일 설정에서 DB ID 찾기 (대체)
                    file_db_id = db_config.get("database_id")
                    
                    # 3. 최종 DB ID 결정
                    final_db_id = env_db_id or file_db_id
                    
                    if final_db_id:
                        config["mount"]["databases"].append({
                            "database_id": final_db_id,
                            "target_folder": folder
                        })
                        
                        if env_db_id:
                            print(f"✅ 환경변수에서 DB ID 로드: {folder} -> {self._mask_sensitive_value(env_db_id, 'id')}")
                        else:
                            print(f"📄 설정파일에서 DB ID 로드: {folder} -> {self._mask_sensitive_value(file_db_id, 'id')}")
                    else:
                        print(f"⚠️ DB ID 없음: {folder} (환경변수 또는 설정파일에 추가 필요)")
            
            if "pages" in mount_config:
                config["mount"]["pages"] = mount_config["pages"]
        
        else:
            # 자동 설정 모드 (페이지 URL 기반)
            self._process_auto_mount_config(config, mount_config)
    
    def _process_auto_mount_config(self, config: Config, mount_config: Dict[str, Any]):
        """자동 마운트 설정 처리"""
        page_url = mount_config.get("page_url")
        if not page_url:
            raise ValueError("mount.manual이 False일 때는 page_url이 설정되어야 합니다.")
        
        # URL에서 페이지 ID 추출
        page_id = page_url.split("/")[-1]
        if len(page_id) < 32:
            raise ValueError(f"페이지 URL {page_url}이 유효하지 않습니다.")
        
        # Notion 토큰 확인
        notion_token = os.environ.get("NOTION_TOKEN")
        if not notion_token:
            raise ValueError("NOTION_TOKEN 환경변수가 설정되지 않았습니다.")
        
        # 토큰 검증
        is_valid, message = self.validate_notion_token(notion_token)
        if not is_valid:
            raise ValueError(f"Notion 토큰 검증 실패: {message}")
        
        # Notion 클라이언트로 자동 탐지
        try:
            notion = Client(auth=notion_token)
            blocks = notion.blocks.children.list(block_id=page_id)
            
            for block in blocks["results"]:
                if block["type"] == "child_database":
                    config["mount"]["databases"].append({
                        "database_id": block["id"],
                        "target_folder": block["child_database"]["title"],
                    })
                elif block["type"] == "child_page":
                    config["mount"]["pages"].append({
                        "page_id": block["id"], 
                        "target_folder": "."
                    })
            
            print(f"✅ 자동 탐지 완료: DB {len(config['mount']['databases'])}개, 페이지 {len(config['mount']['pages'])}개")
                    
        except Exception as e:
            raise ValueError(f"자동 설정 실패: {str(e)}")
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """배포 상태 확인"""
        status = {
            "environment_ready": False,
            "notion_token_valid": False,
            "databases_configured": False,
            "ready_to_deploy": False,
            "missing_items": []
        }
        
        # 환경변수 체크
        notion_token = os.environ.get("NOTION_TOKEN")
        if notion_token:
            is_valid, message = self.validate_notion_token(notion_token)
            status["notion_token_valid"] = is_valid
            if not is_valid:
                status["missing_items"].append(f"Notion 토큰 문제: {message}")
        else:
            status["missing_items"].append("NOTION_TOKEN 환경변수 설정 필요")
        
        # 데이터베이스 설정 체크
        config = self.load_config()
        if config["mount"]["databases"]:
            status["databases_configured"] = True
        else:
            status["missing_items"].append("데이터베이스 설정 필요")
        
        # 환경 준비 상태
        status["environment_ready"] = status["notion_token_valid"] and status["databases_configured"]
        status["ready_to_deploy"] = status["environment_ready"] and len(status["missing_items"]) == 0
        
        return status
    
    def create_env_template(self):
        """환경변수 템플릿 파일 생성"""
        template_content = """# Notion-Hugo 환경변수 설정
# 이 파일을 복사하여 .env 파일을 만들고 실제 값으로 채우세요

# 🔴 필수: Notion API 토큰
NOTION_TOKEN=ntn_your_notion_token_here

# 🟡 자동 생성: 데이터베이스 ID (setup.py 실행 후 자동 설정됨)
NOTION_DATABASE_ID_POSTS=auto_generated_database_id

# 🟢 선택적: Hugo 설정
HUGO_VERSION=0.140.0
HUGO_ENV=production
HUGO_EXTENDED=true

# 🟢 선택적: 배포 설정  
DEPLOY_ENVIRONMENT=production
"""
        
        with open(".env.template", "w", encoding="utf-8") as f:
            f.write(template_content)
        
        print("✅ 환경변수 템플릿 생성: .env.template")


# 편의 함수들 (기존 호환성 유지)
def load_config() -> Config:
    """기존 호환성을 위한 래퍼 함수"""
    manager = ConfigManager()
    return manager.load_config()


def create_config_file(config: Dict[str, Any]):
    """기존 호환성을 위한 래퍼 함수"""
    manager = ConfigManager()
    
    with open(manager.config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


# 진단 및 유틸리티 함수
def diagnose_configuration():
    """설정 진단 실행"""
    print("🔍 Notion-Hugo 설정 진단 시작...\n")
    
    manager = ConfigManager()
    
    # 1. 환경변수 체크
    print("1. 환경변수 확인:")
    notion_token = os.environ.get("NOTION_TOKEN")
    if notion_token:
        print(f"   ✅ NOTION_TOKEN: {manager._mask_sensitive_value(notion_token)}")
        
        is_valid, message = manager.validate_notion_token(notion_token)
        if is_valid:
            print(f"   ✅ 토큰 검증: {message}")
        else:
            print(f"   ❌ 토큰 검증: {message}")
    else:
        print("   ❌ NOTION_TOKEN: 설정되지 않음")
    
    # 2. 데이터베이스 ID 체크
    print("\n2. 데이터베이스 설정:")
    db_id = manager.get_database_id_from_env()
    if db_id:
        print(f"   ✅ DB ID: {manager._mask_sensitive_value(db_id, 'id')}")
    else:
        print("   ❌ DB ID: 환경변수에서 찾을 수 없음")
    
    # 3. 설정 파일 체크
    print("\n3. 설정 파일:")
    if os.path.exists(manager.config_path):
        print(f"   ✅ 설정 파일: {manager.config_path}")
        try:
            config = manager.load_config()
            print(f"   ✅ 설정 로드: 성공")
            print(f"   📊 DB 개수: {len(config['mount']['databases'])}개")
        except Exception as e:
            print(f"   ❌ 설정 로드: 실패 - {e}")
    else:
        print(f"   ⚠️ 설정 파일: 없음 - 기본값 사용")
    
    # 4. 배포 상태 체크
    print("\n4. 배포 준비 상태:")
    status = manager.get_deployment_status()
    
    if status["ready_to_deploy"]:
        print("   ✅ 배포 준비 완료!")
    else:
        print("   ❌ 배포 준비 미완료:")
        for item in status["missing_items"]:
            print(f"      - {item}")
    
    print("\n" + "="*50)
    
    return status


if __name__ == "__main__":
    # 진단 실행
    diagnose_configuration()
