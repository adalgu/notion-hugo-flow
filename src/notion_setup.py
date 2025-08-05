"""
Notion DB 설정 모듈

이 모듈은 Notion 데이터베이스를 자동으로 설정하고 마이그레이션하는 기능을 제공합니다.
Hugo 블로그 포스트를 위한 데이터베이스를 생성하고 샘플 페이지를 추가할 수 있습니다.
"""

import os
import yaml
import time
from typing import Dict, Any, Optional, List, TypedDict
from notion_client import Client
from notion_client.errors import APIResponseError, HTTPResponseError

class NotionSetupConfig(TypedDict):
    """설정 구성을 위한 타입 정의"""
    parent_page_id: Optional[str]
    database_name: str
    notion_token: Optional[str]

class MigrationConfig(TypedDict):
    """마이그레이션 구성을 위한 타입 정의"""
    source_db_id: str
    parent_page_id: Optional[str]
    target_folder: str

class NotionSetup:
    """노션 데이터베이스 설정을 위한 기본 클래스"""
    
    def __init__(self, config: NotionSetupConfig):
        """
        NotionSetup 클래스 초기화
        
        Args:
            config: 설정 구성 (parent_page_id, database_name, notion_token)
                parent_page_id: 상위 페이지 ID (옵션). 지정하지 않으면 워크스페이스 루트에 생성
                database_name: 데이터베이스 이름
                notion_token: Notion API 토큰 (옵션, 환경 변수에 없으면 필수)
        """
        self.parent_page_id = config.get("parent_page_id")
        self.database_name = config["database_name"]
        
        # 환경 변수 또는 전달된 토큰 사용
        self.notion_token = config.get("notion_token") or os.environ.get("NOTION_TOKEN")
        if not self.notion_token:
            raise ValueError("NOTION_TOKEN이 설정되지 않았습니다. 환경 변수 또는 config를 통해 제공하세요.")
        
        # Notion 클라이언트 생성
        self.notion = Client(auth=self.notion_token)
        
        # 재시도 설정
        self.max_retries = 3
        self.retry_delay = 1.0  # 초
    
    def _retry_api_call(self, func, *args, **kwargs) -> Any:
        """
        API 호출을 재시도합니다.
        
        Args:
            func: 호출할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자
            
        Returns:
            API 호출 결과
            
        Raises:
            마지막 예외
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except (APIResponseError, HTTPResponseError) as e:
                last_exception = e
                
                # 429 (Rate Limit) 또는 일시적 서버 오류의 경우 재시도
                if hasattr(e, 'status') and e.status in [429, 500, 502, 503, 504]:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"API 호출 실패 (재시도 {attempt + 1}/{self.max_retries}), {delay:.1f}초 후 재시도...")
                        time.sleep(delay)
                        continue
                
                # 권한 오류나 다른 클라이언트 오류는 즉시 실패
                raise
            except Exception as e:
                # 네트워크 오류 등은 재시도
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"네트워크 오류 (재시도 {attempt + 1}/{self.max_retries}), {delay:.1f}초 후 재시도...")
                    time.sleep(delay)
                    continue
                raise
        
        # 모든 재시도 실패
        raise last_exception
    
    def _validate_token_permissions(self) -> Dict[str, Any]:
        """
        토큰의 권한을 검증하고 가능한 작업을 확인합니다.
        
        Returns:
            권한 정보 딕셔너리
        """
        permissions = {
            "can_create_pages": False,
            "can_create_databases": False,
            "accessible_pages": [],
            "workspace_access": False
        }
        
        try:
            # 기본 검색으로 접근 가능한 페이지 확인
            search_results = self._retry_api_call(
                self.notion.search,
                filter={"value": "page", "property": "object"},
                page_size=10
            )
            
            accessible_pages = []
            for result in search_results.get("results", []):
                if result.get("object") == "page":
                    accessible_pages.append({
                        "id": result["id"],
                        "title": self._extract_page_title(result),
                        "parent": result.get("parent", {})
                    })
            
            permissions["accessible_pages"] = accessible_pages
            permissions["workspace_access"] = len(accessible_pages) > 0
            
            # 데이터베이스 생성 권한 확인을 위해 테스트 페이지에서 시도
            if accessible_pages:
                permissions["can_create_databases"] = True
                print(f"접근 가능한 페이지 {len(accessible_pages)}개 발견")
            
        except Exception as e:
            print(f"권한 검증 중 오류: {str(e)}")
        
        return permissions
    
    def _extract_page_title(self, page: Dict[str, Any]) -> str:
        """
        페이지에서 제목을 추출합니다.
        
        Args:
            page: 페이지 객체
            
        Returns:
            페이지 제목
        """
        if "properties" in page:
            # 데이터베이스 페이지의 경우
            for prop_name, prop in page["properties"].items():
                if prop.get("type") == "title":
                    title_objects = prop.get("title", [])
                    if title_objects:
                        return "".join(obj.get("plain_text", "") for obj in title_objects)
        
        # 일반 페이지의 경우
        if "title" in page and page["title"]:
            return "".join(obj.get("plain_text", "") for obj in page["title"])
            
        return "Untitled"
    
    def _determine_best_parent_location(self) -> Optional[str]:
        """
        데이터베이스 생성을 위한 최적의 부모 위치를 결정합니다.
        
        Returns:
            부모 페이지 ID 또는 None
        """
        print("데이터베이스 생성을 위한 최적의 위치를 찾는 중...")
        
        # 권한 검증
        permissions = self._validate_token_permissions()
        
        if not permissions["workspace_access"]:
            raise ValueError(
                "워크스페이스에 접근할 수 없습니다. "
                "통합(integration) 권한을 확인하고 페이지를 공유했는지 확인하세요."
            )
        
        accessible_pages = permissions["accessible_pages"]
        
        # 1. 사용자가 지정한 parent_page_id가 있으면 우선 사용
        if self.parent_page_id:
            # 접근 가능한 페이지 목록에서 확인
            for page in accessible_pages:
                if page["id"] == self.parent_page_id:
                    print(f"지정된 부모 페이지 사용: {page['title']}")
                    return self.parent_page_id
            
            # 직접 확인 시도
            try:
                page = self._retry_api_call(self.notion.pages.retrieve, page_id=self.parent_page_id)
                print(f"지정된 부모 페이지 확인됨: {self._extract_page_title(page)}")
                return self.parent_page_id
            except Exception:
                print(f"지정된 부모 페이지 '{self.parent_page_id}'에 접근할 수 없습니다.")
        
        # 2. 워크스페이스 루트 레벨 페이지 찾기
        root_pages = []
        for page in accessible_pages:
            parent = page.get("parent", {})
            if parent.get("type") == "workspace":
                root_pages.append(page)
        
        if root_pages:
            # 첫 번째 루트 페이지 사용
            selected_page = root_pages[0]
            print(f"워크스페이스 루트 페이지 사용: {selected_page['title']}")
            return selected_page["id"]
        
        # 3. 가장 적합한 페이지 선택 (제목 기준)
        if accessible_pages:
            # "Blog", "Posts", "Content" 등의 키워드가 있는 페이지 우선
            blog_keywords = ["blog", "post", "content", "article", "write"]
            
            for keyword in blog_keywords:
                for page in accessible_pages:
                    if keyword.lower() in page["title"].lower():
                        print(f"블로그 관련 페이지 발견, 사용: {page['title']}")
                        return page["id"]
            
            # 키워드가 없으면 첫 번째 페이지 사용
            selected_page = accessible_pages[0]
            print(f"기본 페이지 사용: {selected_page['title']}")
            return selected_page["id"]
        
        # 4. 접근 가능한 페이지가 없으면 오류
        raise ValueError(
            "데이터베이스를 생성할 수 있는 페이지가 없습니다. "
            "통합(integration)에 최소 하나의 페이지를 공유하세요."
        )
    
    def _get_common_database_properties(self) -> Dict[str, Any]:
        """
        Hugo 데이터베이스에 공통적으로 사용되는 속성을 반환합니다.
        
        Returns:
            데이터베이스 속성 정의
        """
        return {
            # 최소한 속성 (필수)
            "Name": {
                "title": {}
            },
            "Date": {
                "date": {}
            },
            
            # 콘텐츠 제어 속성 (추천)
            "skipRendering": {
                "checkbox": {}
            },
            "isPublished": {
                "checkbox": {}
            },
            "expiryDate": {
                "date": {}
            },
            
            # 메타데이터 속성 (추천)
            "Description": {
                "rich_text": {}
            },
            "Summary": {
                "rich_text": {}
            },
            "lastModified": {
                "date": {}
            },
            "slug": {
                "rich_text": {}
            },
            "Author": {
                "rich_text": {}
            },
            "weight": {
                "number": {}
            },
            
            # 분류 속성 (추천)
            "categories": {
                "multi_select": {
                    "options": [
                        {"name": "Web Development", "color": "blue"},
                        {"name": "Programming", "color": "green"},
                        {"name": "Technology", "color": "purple"}
                    ]
                }
            },
            "Tags": {
                "multi_select": {
                    "options": [
                        {"name": "Tutorial", "color": "yellow"},
                        {"name": "Design", "color": "red"},
                        {"name": "API", "color": "orange"},
                        {"name": "Database", "color": "gray"}
                    ]
                }
            },
            "keywords": {
                "rich_text": {}
            },
            
            # 테마 지원 속성 (추천)
            "featured": {
                "checkbox": {}
            },
            "subtitle": {
                "rich_text": {}
            },
            "linkTitle": {
                "rich_text": {}
            },
            "layout": {
                "rich_text": {}
            },
            
            # 시스템 시간 속성 (자동)
            "Created time": {
                "date": {}
            },
            "Last Updated": {
                "last_edited_time": {}
            },
            
            # 추가 속성 (선택)
            "ShowToc": {
                "checkbox": {}
            },
            "HideSummary": {
                "checkbox": {}
            }
        }

    def create_hugo_database(self) -> Dict[str, Any]:
        """
        Hugo 블로그 포스트를 위한 Notion 데이터베이스를 생성합니다.
        자동으로 최적의 위치를 찾아 생성합니다.
        
        Returns:
            생성된 데이터베이스 객체
        """
        print(f"'{self.database_name}' 데이터베이스 생성을 시작합니다...")
        
        # 최적의 부모 위치 결정
        try:
            parent_page_id = self._determine_best_parent_location()
        except Exception as e:
            print(f"부모 위치 결정 실패: {str(e)}")
            raise ValueError(
                f"데이터베이스 생성 위치를 결정할 수 없습니다: {str(e)}\n"
                "해결 방법:\n"
                "1. 통합(integration)에 페이지를 공유하세요\n"
                "2. --parent-page 옵션으로 특정 페이지 ID를 지정하세요\n"
                "3. 대화형 모드(-i)를 사용하세요"
            ) from e
        
        # 데이터베이스 속성 정의
        properties = self._get_common_database_properties()
        
        # 데이터베이스 타이틀 정의
        title = [{"type": "text", "text": {"content": self.database_name}}]
        
        # 데이터베이스 생성 요청 (재시도 로직 포함)
        try:
            print(f"페이지 '{parent_page_id}'에 데이터베이스 생성 중...")
            database = self._retry_api_call(
                self.notion.databases.create,
                parent={"type": "page_id", "page_id": parent_page_id},
                title=title,
                properties=properties
            )
            
            print(f"✅ 데이터베이스가 성공적으로 생성되었습니다!")
            print(f"📄 데이터베이스 ID: {database['id']}")
            print(f"🔗 URL: https://notion.so/{database['id'].replace('-', '')}")
            
            return database
            
        except APIResponseError as e:
            error_msg = self._format_api_error(e)
            raise ValueError(f"데이터베이스 생성 실패: {error_msg}") from e
        except Exception as e:
            raise ValueError(f"예상치 못한 오류로 데이터베이스 생성 실패: {str(e)}") from e
    
    def _format_api_error(self, error: APIResponseError) -> str:
        """
        API 오류를 사용자 친화적인 메시지로 변환합니다.
        
        Args:
            error: API 응답 오류
            
        Returns:
            사용자 친화적인 오류 메시지
        """
        error_code = getattr(error, 'code', None)
        error_message = str(error)
        
        if error_code == "unauthorized":
            return (
                "권한이 없습니다. 노션 API 토큰이 올바른지 확인하세요.\n"
                "토큰 생성: https://www.notion.so/my-integrations"
            )
        elif error_code == "object_not_found":
            return (
                "지정된 페이지를 찾을 수 없습니다. 페이지 ID를 확인하고 "
                "통합(integration)에 해당 페이지가 공유되었는지 확인하세요."
            )
        elif "validation_error" in error_message.lower():
            return (
                "요청 데이터에 오류가 있습니다. 데이터베이스 속성 정의를 확인하세요."
            )
        elif "rate_limited" in error_message.lower():
            return (
                "API 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요."
            )
        else:
            return f"API 오류: {error_message}"

    def create_sample_post(self, database_id: str) -> Dict[str, Any]:
        """
        샘플 블로그 포스트를 데이터베이스에 생성합니다.
        
        Args:
            database_id: 대상 데이터베이스 ID
            
        Returns:
            생성된 페이지 객체
        """
        # 현재 날짜 생성
        from datetime import datetime
        now = datetime.now().isoformat()
        
        # 페이지 속성 정의
        properties = {
            # 최소한 속성 (필수)
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": "시작하기 - 첫 번째 블로그 포스트"
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": now
                }
            },
            
            # 콘텐츠 제어 속성 (추천)
            "skipRendering": {
                "checkbox": False
            },
            "isPublished": {
                "checkbox": True
            },
            "expiryDate": {
                "date": {
                    "start": None  # 만료 날짜 없음
                }
            },
            
            # 메타데이터 속성 (추천)
            "Description": {
                "rich_text": [
                    {
                        "text": {
                            "content": "Notion과 Hugo를 사용한 첫 번째 블로그 포스트입니다."
                        }
                    }
                ]
            },
            "Summary": {
                "rich_text": [
                    {
                        "text": {
                            "content": "Notion을 CMS로 사용하고 Hugo로 정적 사이트를 생성하는 블로그 시스템을 시작하는 방법"
                        }
                    }
                ]
            },
            "slug": {
                "rich_text": [
                    {
                        "text": {
                            "content": "getting-started-first-blog-post"
                        }
                    }
                ]
            },
            "Author": {
                "rich_text": [
                    {
                        "text": {
                            "content": "작성자 이름"
                        }
                    }
                ]
            },
            "weight": {
                "number": 1  # 상위에 표시될 첫 번째 포스트
            },
            
            # 분류 속성 (추천)
            "categories": {
                "multi_select": [
                    {"name": "Technology"}
                ]
            },
            "Tags": {
                "multi_select": [
                    {"name": "Tutorial"},
                    {"name": "Hugo"},
                    {"name": "Notion"}
                ]
            },
            "keywords": {
                "rich_text": [
                    {
                        "text": {
                            "content": "notion,hugo,blog,tutorial,시작하기"
                        }
                    }
                ]
            },
            
            # 테마 지원 속성 (추천)
            "featured": {
                "checkbox": True
            },
            "subtitle": {
                "rich_text": [
                    {
                        "text": {
                            "content": "Notion과 Hugo로 블로그 시작하기"
                        }
                    }
                ]
            },
            
            # 시스템 속성 (자동)
            "Created time": {
                "date": {
                    "start": now
                }
            },
            
            # 추가 속성 (선택)
            "ShowToc": {
                "checkbox": True
            },
            "HideSummary": {
                "checkbox": False
            },
            "linkTitle": {
                "rich_text": [
                    {
                        "text": {
                            "content": "시작하기"
                        }
                    }
                ]
            }
        }
        
        # 페이지 콘텐츠 블록 정의
        children = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "첫 번째 블로그 포스트에 오신 것을 환영합니다!"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Notion을 CMS로 사용하고 Hugo로 정적 사이트를 생성하는 블로그 시스템을 시작했습니다."
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Notion에서 작성하기"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "이 데이터베이스에 새 페이지를 추가하여 블로그 포스트를 작성할 수 있습니다. 'isPublished' 속성을 체크하면 Hugo 사이트에 게시됩니다."
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "마크다운 지원"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Notion은 마크다운 형식을 지원합니다. "
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": "굵은 텍스트"
                            },
                            "annotations": {
                                "bold": True
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": ", "
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": "기울임꼴"
                            },
                            "annotations": {
                                "italic": True
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": ", 그리고 "
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": "코드 블록"
                            },
                            "annotations": {
                                "code": True
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": "도 사용할 수 있습니다."
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "// 코드 예제\nfunction greeting() {\n  console.log('안녕하세요, Notion + Hugo!');\n}"
                            }
                        }
                    ],
                    "language": "javascript"
                }
            }
        ]
        
        # 페이지 생성 요청 (재시도 로직 포함)
        try:
            print("샘플 포스트 생성 중...")
            page = self._retry_api_call(
                self.notion.pages.create,
                parent={"database_id": database_id},
                properties=properties,
                children=children
            )
            
            print(f"✅ 샘플 포스트가 성공적으로 생성되었습니다!")
            print(f"📄 페이지 ID: {page['id']}")
            print(f"🔗 URL: https://notion.so/{page['id'].replace('-', '')}")
            
            return page
            
        except APIResponseError as e:
            error_msg = self._format_api_error(e)
            raise ValueError(f"샘플 포스트 생성 실패: {error_msg}") from e
        except Exception as e:
            raise ValueError(f"예상치 못한 오류로 샘플 포스트 생성 실패: {str(e)}") from e

    def update_config(self, database_id: str, target_folder: str) -> None:
        """
        설정 파일을 업데이트합니다.
        
        Args:
            database_id: 데이터베이스 ID
            target_folder: 대상 폴더 이름
        """
        # 기존 설정 파일이 있으면 로드
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notion-hugo.config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                try:
                    config = yaml.safe_load(file) or {}
                except:
                    config = {}
        else:
            config = {}
        
        # 마운트 설정 업데이트 또는 생성
        if 'mount' not in config:
            config['mount'] = {
                "manual": True,
                "databases": [
                    {
                        "database_id": database_id,
                        "target_folder": target_folder
                    }
                ]
            }
        else:
            config['mount']['manual'] = True
            if 'databases' not in config['mount']:
                config['mount']['databases'] = []
            
            # 동일 데이터베이스가 있는지 확인
            db_exists = False
            for i, db in enumerate(config['mount'].get('databases', [])):
                if db.get('database_id') == database_id:
                    config['mount']['databases'][i]['target_folder'] = target_folder
                    db_exists = True
                    break
            
            # 없으면 추가
            if not db_exists:
                config['mount']['databases'].append({
                    "database_id": database_id,
                    "target_folder": target_folder
                })
        
        # 파일명 설정 업데이트 또는 생성
        if 'filename' not in config:
            config['filename'] = {
                "format": "date-title",
                "date_format": "%Y-%m-%d",
                "korean_title": "slug"
            }
        
        # YAML 파일 작성
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notion-hugo.config.yaml')
        with open(config_path, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        
        print(f"설정 파일이 업데이트되었습니다: {config_path}")
    
    def quick_setup(self, target_folder: str = "posts") -> Dict[str, Any]:
        """
        원스톱 빠른 설정: 노션 키만으로 자동 DB 생성 및 샘플 포스트 생성
        
        Args:
            target_folder: 대상 폴더 (기본값: "posts")
            
        Returns:
            설정 결과
        """
        print("🚀 노션-휴고 원스톱 설정을 시작합니다!")
        print("=" * 60)
        
        setup_result = {
            "success": False,
            "database_id": None,
            "sample_post_id": None,
            "config_updated": False,
            "errors": []
        }
        
        try:
            # 1단계: 데이터베이스 생성
            print("\n📊 1단계: 노션 데이터베이스 생성")
            print("-" * 40)
            
            database = self.create_hugo_database()
            setup_result["database_id"] = database["id"]
            
            # 2단계: 샘플 포스트 생성
            print("\n📝 2단계: 샘플 포스트 생성")
            print("-" * 40)
            
            sample_post = self.create_sample_post(database["id"])
            setup_result["sample_post_id"] = sample_post["id"]
            
            # 3단계: 설정 파일 업데이트
            print("\n⚙️  3단계: 설정 파일 업데이트")
            print("-" * 40)
            
            self.update_config(database["id"], target_folder)
            setup_result["config_updated"] = True
            
            # 완료
            setup_result["success"] = True
            
            print("\n🎉 원스톱 설정 완료!")
            print("=" * 60)
            print("✅ 노션 데이터베이스가 생성되었습니다")
            print("✅ 샘플 포스트가 추가되었습니다")
            print("✅ 설정 파일이 업데이트되었습니다")
            
            print(f"\n🔗 노션에서 확인하기:")
            print(f"   데이터베이스: https://notion.so/{database['id'].replace('-', '')}")
            print(f"   샘플 포스트: https://notion.so/{sample_post['id'].replace('-', '')}")
            
            print(f"\n🚀 다음 단계:")
            print(f"   python notion_hugo_app.py 명령으로 블로그 동기화를 시작하세요!")
            
            return setup_result
            
        except Exception as e:
            error_message = str(e)
            setup_result["errors"].append(error_message)
            
            print(f"\n❌ 설정 중 오류가 발생했습니다:")
            print(f"   {error_message}")
            
            # 부분 성공한 내용 표시
            if setup_result["database_id"]:
                print(f"\n📊 생성된 데이터베이스: {setup_result['database_id']}")
                print(f"   URL: https://notion.so/{setup_result['database_id'].replace('-', '')}")
            
            if setup_result["sample_post_id"]:
                print(f"\n📝 생성된 샘플 포스트: {setup_result['sample_post_id']}")
                print(f"   URL: https://notion.so/{setup_result['sample_post_id'].replace('-', '')}")
            
            # 오류 해결 가이드
            print(f"\n🔧 문제 해결 방법:")
            if "권한" in error_message or "unauthorized" in error_message.lower():
                print("   1. 노션 API 토큰이 올바른지 확인하세요")
                print("   2. 통합(integration)에 페이지를 공유했는지 확인하세요")
                print("   3. 통합 권한에 'Insert content' 권한이 있는지 확인하세요")
            elif "찾을 수 없습니다" in error_message or "not_found" in error_message.lower():
                print("   1. 지정한 페이지 ID가 올바른지 확인하세요")
                print("   2. 해당 페이지가 통합에 공유되었는지 확인하세요")
            else:
                print("   1. 네트워크 연결을 확인하세요")
                print("   2. 노션 서비스 상태를 확인하세요")
                print("   3. 잠시 후 다시 시도하세요")
            
            return setup_result
    
    def validate_setup(self) -> Dict[str, Any]:
        """
        현재 설정을 검증합니다.
        
        Returns:
            검증 결과
        """
        validation_result = {
            "valid": True,
            "token_valid": False,
            "workspace_accessible": False,
            "config_exists": False,
            "database_accessible": False,
            "recommendations": [],
            "errors": []
        }
        
        try:
            print("🔍 노션-휴고 설정을 검증하는 중...")
            
            # 1. 토큰 검증
            try:
                permissions = self._validate_token_permissions()
                validation_result["token_valid"] = True
                validation_result["workspace_accessible"] = permissions["workspace_access"]
                
                if permissions["workspace_access"]:
                    print("✅ 노션 API 토큰이 유효하고 워크스페이스에 접근할 수 있습니다")
                else:
                    print("⚠️  노션 API 토큰은 유효하지만 워크스페이스 접근이 제한됩니다")
                    validation_result["recommendations"].append(
                        "통합(integration)에 최소 하나의 페이지를 공유하세요"
                    )
                    
            except Exception as e:
                validation_result["token_valid"] = False
                validation_result["errors"].append(f"토큰 검증 실패: {str(e)}")
                print(f"❌ 노션 API 토큰 검증 실패: {str(e)}")
            
            # 2. 설정 파일 검증
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notion-hugo.config.yaml')
            if os.path.exists(config_path):
                validation_result["config_exists"] = True
                print("✅ 설정 파일이 존재합니다")
                
                # 설정 파일에서 데이터베이스 ID 확인
                try:
                    with open(config_path, 'r') as file:
                        config = yaml.safe_load(file) or {}
                    
                    databases = config.get('mount', {}).get('databases', [])
                    if databases and databases[0].get('database_id'):
                        database_id = databases[0]['database_id']
                        
                        # 데이터베이스 접근 검증
                        try:
                            db = self._retry_api_call(self.notion.databases.retrieve, database_id=database_id)
                            validation_result["database_accessible"] = True
                            print(f"✅ 설정된 데이터베이스에 접근할 수 있습니다: {self._extract_page_title(db)}")
                        except Exception:
                            validation_result["errors"].append(f"설정된 데이터베이스 '{database_id}'에 접근할 수 없습니다")
                            print(f"❌ 설정된 데이터베이스에 접근할 수 없습니다")
                            validation_result["recommendations"].append(
                                "데이터베이스가 통합에 공유되었는지 확인하거나 새로 설정하세요"
                            )
                    else:
                        validation_result["recommendations"].append("설정 파일에 데이터베이스 ID가 없습니다")
                        
                except Exception as e:
                    validation_result["errors"].append(f"설정 파일 읽기 실패: {str(e)}")
                    print(f"❌ 설정 파일 읽기 실패: {str(e)}")
            else:
                validation_result["config_exists"] = False
                print("⚠️  설정 파일이 없습니다")
                validation_result["recommendations"].append("--setup-db 또는 --quick-setup으로 초기 설정을 진행하세요")
            
            # 3. 전체 유효성 판단
            validation_result["valid"] = (
                validation_result["token_valid"] and
                validation_result["workspace_accessible"] and
                validation_result["config_exists"] and
                (validation_result["database_accessible"] or not databases)
            )
            
            # 결과 요약
            print("\n📋 검증 결과 요약:")
            print(f"   토큰 유효성: {'✅' if validation_result['token_valid'] else '❌'}")
            print(f"   워크스페이스 접근: {'✅' if validation_result['workspace_accessible'] else '❌'}")
            print(f"   설정 파일 존재: {'✅' if validation_result['config_exists'] else '❌'}")
            print(f"   데이터베이스 접근: {'✅' if validation_result['database_accessible'] else '❌'}")
            
            if validation_result["recommendations"]:
                print("\n💡 권장사항:")
                for i, rec in enumerate(validation_result["recommendations"], 1):
                    print(f"   {i}. {rec}")
            
            if validation_result["errors"]:
                print("\n❌ 발견된 문제:")
                for i, error in enumerate(validation_result["errors"], 1):
                    print(f"   {i}. {error}")
            
            if validation_result["valid"]:
                print("\n🎉 모든 검증을 통과했습니다! 노션-휴고를 사용할 준비가 되었습니다.")
            else:
                print("\n⚠️  일부 문제가 발견되었습니다. 위의 권장사항을 참고하여 수정하세요.")
            
            return validation_result
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"검증 중 예상치 못한 오류: {str(e)}")
            print(f"❌ 검증 중 오류 발생: {str(e)}")
            return validation_result

class NotionMigration(NotionSetup):
    """노션 데이터베이스 마이그레이션을 위한 클래스"""
    
    def __init__(self, config: NotionSetupConfig):
        """
        NotionMigration 클래스 초기화
        
        Args:
            config: 설정 구성 (parent_page_id, database_name, notion_token)
        """
        super().__init__(config)
        
        # 옵션별 필드와 기본값 설정
        self.valid_select_options = {
            "Tags": []  # 대상 DB에서 동적으로 채워짐
        }
        self.default_options = {
            "Tags": "Uncategorized"
        }
        
        # 필수 필드 매핑
        self.required_fields = {
            "image": ["external.url"],
            "file": ["external.url"],
            "pdf": ["external.url"],
            "video": ["external.url"],
            "table": ["table_width", "has_column_header", "has_row_header", "children"],
            "column_list": ["children"],
            "column": ["children"],
            "bookmark": ["url"],
            "embed": ["url"],
        }
        
        # 태그 매핑 (필요한 경우 정의)
        self.tag_mappings = {}
    
    def migrate_database(self, source_db_id: str, target_folder: str) -> Dict[str, Any]:
        """
        소스 데이터베이스에서 블로그 포스트 구조로 마이그레이션합니다.
        
        Args:
            source_db_id: 소스 데이터베이스 ID
            target_folder: 대상 폴더 이름
            
        Returns:
            통계와 새 데이터베이스 ID를 포함한 결과
        """
        try:
            # 소스 데이터베이스 구조 검증
            validation_result = self._validate_source_database(source_db_id)
            if validation_result["missingRequired"] or validation_result["incompatibleTypes"]:
                print("\n데이터베이스 검증 실패:")
                
                if validation_result["missingRequired"]:
                    print("\n필수 속성이 누락되었습니다:")
                    for prop in validation_result["missingRequired"]:
                        print(f"- {prop}")
                
                if validation_result["incompatibleTypes"]:
                    print("\n호환되지 않는 속성 유형:")
                    for incompatible in validation_result["incompatibleTypes"]:
                        print(f"- {incompatible['property']}: 예상 {incompatible['expectedType']}, 발견 {incompatible['actualType']}")
                
                raise ValueError("데이터베이스 검증 실패. 문제를 수정하고 다시 시도하세요.")
            
            print("데이터베이스 검증 성공!")
            
            # 새 데이터베이스 생성
            print("새 데이터베이스 생성 중...")
            new_db = self.create_hugo_database()
            
            # 대상 데이터베이스에서 유효한 태그 옵션 로드
            target_db = self.notion.databases.retrieve(database_id=new_db["id"])
            if target_db["properties"]["Tags"]["type"] == "multi_select":
                self.valid_select_options["Tags"] = [
                    option["name"] 
                    for option in target_db["properties"]["Tags"]["multi_select"]["options"]
                ]
            
            # 소스 데이터베이스의 모든 페이지 가져오기
            print("소스 데이터베이스에서 페이지 가져오는 중...")
            pages_response = self.notion.databases.query(database_id=source_db_id)
            pages = pages_response["results"]
            
            # 페이지네이션 처리
            while pages_response.get("has_more", False):
                pages_response = self.notion.databases.query(
                    database_id=source_db_id,
                    start_cursor=pages_response["next_cursor"]
                )
                pages.extend(pages_response["results"])
            
            # 마이그레이션 통계 초기화
            stats = {
                "total": len(pages),
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "errors": {}
            }
            
            print(f"마이그레이션할 페이지 {stats['total']}개를 찾았습니다")
            
            # 각 페이지 마이그레이션
            for page in pages:
                if page["object"] != "page":
                    print(f"페이지 {page['id']} 건너뜀: 페이지 객체가 아님")
                    stats["skipped"] += 1
                    continue
                
                try:
                    # 콘텐츠 및 속성 추출
                    blocks_response = self.notion.blocks.children.list(block_id=page["id"])
                    blocks = blocks_response["results"]
                    
                    # 페이지네이션 처리
                    while blocks_response.get("has_more", False):
                        blocks_response = self.notion.blocks.children.list(
                            block_id=page["id"],
                            start_cursor=blocks_response["next_cursor"]
                        )
                        blocks.extend(blocks_response["results"])
                    
                    # 블록 변환
                    transformed_blocks = []
                    for block in blocks:
                        if block["type"] in self.required_fields and not self._validate_block(block):
                            print(f"유효하지 않은 블록 건너뜀: {block['type']}")
                            continue
                        
                        transformed_block = self._transform_block(block)
                        if transformed_block:
                            if block["type"] == "code" and len(self._get_code_content(block)) > 2000:
                                split_blocks = self._split_code_block(block)
                                transformed_blocks.extend(split_blocks)
                            else:
                                transformed_blocks.append(transformed_block)
                    
                    # 속성 변환 및 페이지 생성
                    properties = self._transform_properties(page["properties"])
                    new_page = self.notion.pages.create(
                        parent={"database_id": new_db["id"]},
                        properties=properties,
                        children=transformed_blocks
                    )
                    
                    print(f"페이지 마이그레이션 완료: {page['id']}")
                    stats["success"] += 1
                    
                except Exception as e:
                    print(f"페이지 {page['id']} 마이그레이션 실패:", str(e))
                    stats["failed"] += 1
                    stats["errors"][page["id"]] = [str(e)]
            
            # 마이그레이션 진행 상황 출력
            self._log_migration_progress(stats)
            
            # 설정 파일 업데이트
            self.update_config(new_db["id"], target_folder)
            
            print("\n마이그레이션 완료!")
            print(f"1. Notion에서 새 데이터베이스 열기: https://notion.so/{new_db['id'].replace('-', '')}")
            print("2. 설정이 자동으로 업데이트되었습니다")
            print("3. 'python notion_hugo_app.py'를 실행하여 동기화 시작")
            
            return {
                "success": True,
                "new_database_id": new_db["id"],
                "stats": stats
            }
            
        except Exception as e:
            print(f"마이그레이션 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_source_database(self, source_db_id: str) -> Dict[str, Any]:
        """
        소스 데이터베이스 구조를 검증합니다.
        
        Args:
            source_db_id: 소스 데이터베이스 ID
            
        Returns:
            검증 결과
        """
        result = {
            "missingRequired": [],
            "incompatibleTypes": []
        }
        
        # 데이터베이스 스키마 가져오기
        database = self.notion.databases.retrieve(database_id=source_db_id)
        
        # 필수 속성 및 예상 유형
        required_properties = {
            "Name": "title",  # 제목은 필수
            "Description": "rich_text",  # 설명은 필수
            "Tags": "multi_select",  # 태그는 필수
            "Created time": "date",  # 생성 시간은 필수
            "Last Updated": "last_edited_time"  # 마지막 수정 시간은 필수
        }
        
        # 필수 속성 확인
        for prop_name, expected_type in required_properties.items():
            if prop_name not in database["properties"]:
                result["missingRequired"].append(prop_name)
            elif database["properties"][prop_name]["type"] != expected_type:
                # 시간 관련 속성 특별 처리
                if (prop_name == "Created time" and database["properties"][prop_name]["type"] in ["date", "created_time"]) or \
                   (prop_name == "Last Updated" and database["properties"][prop_name]["type"] in ["last_edited_time", "date"]):
                    # 이러한 유형은 허용
                    continue
                
                result["incompatibleTypes"].append({
                    "property": prop_name,
                    "expectedType": expected_type,
                    "actualType": database["properties"][prop_name]["type"]
                })
        
        return result
    
    def _validate_block(self, block: Dict[str, Any]) -> bool:
        """
        블록이 필수 필드를 가지고 있는지 검증합니다.
        
        Args:
            block: 검증할 블록
            
        Returns:
            유효성 여부
        """
        block_type = block["type"]
        required_fields = self.required_fields.get(block_type)
        
        if not required_fields:
            return True  # 필수 필드가 정의되지 않은 유형은 통과
        
        for field_path in required_fields:
            field_parts = field_path.split(".")
            value = block.get(block_type)
            
            for key in field_parts:
                if not value or not isinstance(value, dict):
                    return False
                value = value.get(key)
            
            if value is None:
                return False
        
        return True
    
    def _transform_block(self, block: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        블록을 변환합니다.
        
        Args:
            block: 변환할 블록
            
        Returns:
            변환된 블록 또는 None (유효하지 않은 경우)
        """
        block_type = block["type"]
        
        if block_type in ["image", "file", "pdf", "video"]:
            if not self._validate_block(block):
                print(f"유효하지 않은 {block_type} 블록 건너뜀: 외부 URL 누락")
                return None
        
        elif block_type == "table":
            if not self._validate_block(block):
                table_block = block[block_type]
                table_block["table_width"] = table_block.get("table_width", 1)
                table_block["has_column_header"] = table_block.get("has_column_header", False)
                table_block["has_row_header"] = table_block.get("has_row_header", False)
                table_block["children"] = table_block.get("children", [])
        
        elif block_type in ["column_list", "column"]:
            if not self._validate_block(block):
                column_block = block[block_type]
                column_block["children"] = column_block.get("children", [])
        
        return block
    
    def _get_code_content(self, block: Dict[str, Any]) -> str:
        """
        코드 블록의 내용을 가져옵니다.
        
        Args:
            block: 코드 블록
            
        Returns:
            코드 내용
        """
        if block["type"] != "code" or "code" not in block:
            return ""
        
        rich_text = block["code"].get("rich_text", [])
        if not rich_text or "text" not in rich_text[0]:
            return ""
        
        return rich_text[0]["text"].get("content", "")
    
    def _split_code_block(self, block: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        긴 코드 블록을 여러 블록으로 분할합니다.
        
        Args:
            block: 분할할 코드 블록
            
        Returns:
            분할된 블록 목록
        """
        content = self._get_code_content(block)
        if not content or len(content) <= 2000:
            return [block]
        
        MAX_LENGTH = 2000
        blocks = []
        remaining_content = content
        
        while remaining_content:
            chunk = remaining_content[:MAX_LENGTH]
            remaining_content = remaining_content[MAX_LENGTH:]
            
            new_block = {
                "object": "block",
                "type": "code",
                "code": {
                    **block["code"],
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": chunk},
                            "annotations": block["code"]["rich_text"][0].get("annotations", {})
                        }
                    ]
                }
            }
            
            blocks.append(new_block)
        
        return blocks
    
    def _transform_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        페이지 속성을 변환합니다.
        
        Args:
            properties: 변환할 속성
            
        Returns:
            변환된 속성
        """
        from datetime import datetime
        now = datetime.now().isoformat()
        
        # 속성 복사 및 기본값 설정
        transformed = {}
        
        # 필수 속성
        # Name 속성
        if "Name" in properties and properties["Name"]["type"] == "title":
            transformed["Name"] = {
                "title": properties["Name"]["title"]
            }
        else:
            transformed["Name"] = {
                "title": []
            }
        
        # Date 속성 (발행일) - 소스에 date 속성이 있으면 사용, 없으면 Created time 사용
        date_found = False
        for prop_name, prop in properties.items():
            if prop["type"] == "date" and prop_name != "Created time":
                transformed["Date"] = {
                    "date": prop["date"]
                }
                date_found = True
                break
        
        # Date 속성이 없으면 Created time 사용
        if not date_found:
            if "Created time" in properties and properties["Created time"]["type"] == "date":
                transformed["Date"] = {
                    "date": properties["Created time"]["date"]
                }
            else:
                transformed["Date"] = {
                    "date": {
                        "start": now
                    }
                }
        
        # Description 속성
        if "Description" in properties and properties["Description"]["type"] == "rich_text":
            transformed["Description"] = {
                "rich_text": properties["Description"]["rich_text"]
            }
        else:
            transformed["Description"] = {
                "rich_text": []
            }
        
        # 특수 속성
        # isPublished 속성
        if "isPublished" in properties and properties["isPublished"]["type"] == "checkbox":
            transformed["isPublished"] = {
                "checkbox": properties["isPublished"]["checkbox"]
            }
        else:
            transformed["isPublished"] = {
                "checkbox": False
            }
        
        # doNotRendering 속성
        if "doNotRendering" in properties and properties["doNotRendering"]["type"] == "checkbox":
            transformed["doNotRendering"] = {
                "checkbox": properties["doNotRendering"]["checkbox"]
            }
        else:
            transformed["doNotRendering"] = {
                "checkbox": False
            }
        
        # draft 속성 (isPublished의 반대)
        if "draft" in properties and properties["draft"]["type"] == "checkbox":
            transformed["draft"] = {
                "checkbox": properties["draft"]["checkbox"]
            }
        else:
            # isPublished가 True면 draft는 False
            is_published = False
            if "isPublished" in properties and properties["isPublished"]["type"] == "checkbox":
                is_published = properties["isPublished"]["checkbox"]
                
            transformed["draft"] = {
                "checkbox": not is_published
            }
        
        # 시스템 속성
        # Created time 속성
        if "Created time" in properties and properties["Created time"]["type"] == "date":
            transformed["Created time"] = {
                "date": properties["Created time"]["date"]
            }
        else:
            transformed["Created time"] = {
                "date": {
                    "start": now
                }
            }
        
        # 선택적 속성
        # Tags 속성
        if "Tags" in properties and properties["Tags"]["type"] == "multi_select":
            tags = []
            for tag in properties["Tags"]["multi_select"]:
                tag_name = tag["name"]
                # 태그 매핑 적용
                if tag_name in self.tag_mappings:
                    tag_name = self.tag_mappings[tag_name]
                # 유효한 태그 옵션 확인
                if tag_name not in self.valid_select_options["Tags"]:
                    tag_name = self.default_options["Tags"]
                tags.append({"name": tag_name})
            
            transformed["Tags"] = {
                "multi_select": tags
            }
        else:
            transformed["Tags"] = {
                "multi_select": []
            }
        
        # slug 속성
        # 슬러그가 있으면 사용, 없으면 제목에서 생성
        if "slug" in properties and properties["slug"]["type"] == "rich_text" and properties["slug"]["rich_text"]:
            transformed["slug"] = {
                "rich_text": properties["slug"]["rich_text"]
            }
        else:
            # 제목에서 슬러그 생성
            title = "untitled"
            if "Name" in properties and properties["Name"]["type"] == "title" and properties["Name"]["title"]:
                title = "".join(text_obj.get("plain_text", "") for text_obj in properties["Name"]["title"])
            
            # 슬러그 생성 (영문 소문자, 숫자, 하이픈만 사용)
            import re
            slug = re.sub(r'[^\w\s-]', '', title.lower())
            slug = re.sub(r'[\s]+', '-', slug)
            
            transformed["slug"] = {
                "rich_text": [{"type": "text", "text": {"content": slug}}]
            }
        
        # 기타 선택적 속성
        for prop_name, default_value in [
            ("Author", {"rich_text": [{"type": "text", "text": {"content": "작성자 이름"}}]}),
            ("ShowToc", {"checkbox": True}),
            ("HideSummary", {"checkbox": False}),
            ("isFeatured", {"checkbox": False}),
            ("Subtitle", {"rich_text": []})
        ]:
            if prop_name in properties:
                transformed[prop_name] = properties[prop_name]
            else:
                transformed[prop_name] = default_value
        
        return transformed
    
    def _log_migration_progress(self, stats: Dict[str, Any]) -> None:
        """
        마이그레이션 진행 상황을 출력합니다.
        
        Args:
            stats: 마이그레이션 통계
        """
        print(f"""
마이그레이션 진행 상황:
- 전체: {stats['total']}
- 성공: {stats['success']}
- 실패: {stats['failed']}
- 건너뜀: {stats['skipped']}
""")
        
        if stats['failed'] > 0:
            print("\n실패한 페이지:")
            for page_id, errors in stats['errors'].items():
                print(f"\n페이지 {page_id}:")
                for error in errors:
                    print(f"- {error}")
