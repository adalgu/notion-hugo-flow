import os
from dotenv import load_dotenv
from notion_client import Client
from typing import Optional

# Notion API version - Update this to use the latest API version
NOTION_API_VERSION = "2025-09-03"

def create_notion_client(api_version: Optional[str] = None):
    """
    Notion API 클라이언트를 생성합니다.

    Args:
        api_version: 사용할 Notion API 버전 (기본값: 2025-09-03)

    Returns:
        Notion API 클라이언트 객체

    Raises:
        ValueError: NOTION_TOKEN 환경 변수가 설정되지 않은 경우
    """
    # 환경 변수 로드
    load_dotenv()

    # NOTION_TOKEN 환경 변수 확인
    notion_token = os.environ.get('NOTION_TOKEN')
    if not notion_token:
        raise ValueError("NOTION_TOKEN 환경 변수가 설정되지 않았습니다.")

    # API 버전 설정
    version = api_version or NOTION_API_VERSION

    # Notion 클라이언트 생성 with API version
    return Client(
        auth=notion_token,
        notion_version=version
    )

def get_database_pages(notion_client, database_id, use_data_source=False):
    """
    Notion 데이터베이스의 모든 페이지를 가져옵니다.
    API 2025-09-03부터는 data_source를 사용할 수 있습니다.

    Args:
        notion_client: Notion API 클라이언트
        database_id: 데이터베이스 ID 또는 data_source ID
        use_data_source: data_source API 사용 여부 (기본값: False)

    Returns:
        데이터베이스의 페이지 목록
    """
    pages = []

    # API 버전에 따라 적절한 ID 파라미터 사용
    query_params = {}
    if use_data_source:
        # 2025-09-03 버전: data_source_id 사용
        query_params['data_source_id'] = database_id
    else:
        # 하위 호환성: database_id 사용
        query_params['database_id'] = database_id

    try:
        # 데이터베이스 쿼리
        response = notion_client.databases.query(**query_params)

        # 모든 페이지 수집
        pages.extend(response['results'])

        # 페이지네이션 처리
        while response.get('has_more', False):
            query_params['start_cursor'] = response['next_cursor']
            response = notion_client.databases.query(**query_params)
            pages.extend(response['results'])
    except Exception as e:
        # 만약 data_source를 지원하지 않는 경우 database_id로 폴백
        if use_data_source and "data_source" in str(e):
            return get_database_pages(notion_client, database_id, use_data_source=False)
        raise

    return pages

def get_page_content(notion_client, page_id):
    """
    Notion 페이지의 내용을 가져옵니다.
    
    Args:
        notion_client: Notion API 클라이언트
        page_id: 페이지 ID
    
    Returns:
        페이지 내용 블록 목록
    """
    blocks = []
    
    # 페이지 블록 가져오기
    response = notion_client.blocks.children.list(block_id=page_id)
    
    # 모든 블록 수집
    blocks.extend(response['results'])
    
    # 페이지네이션 처리
    while response.get('has_more', False):
        response = notion_client.blocks.children.list(
            block_id=page_id,
            start_cursor=response['next_cursor']
        )
        blocks.extend(response['results'])
    
    # 중첩된 블록 처리
    for i, block in enumerate(blocks.copy()):
        if block.get('has_children', False):
            child_blocks = get_page_content(notion_client, block['id'])
            # 원래 블록에 자식 블록 정보 추가
            blocks[i]['children'] = child_blocks
    
    return blocks

def get_database_schema(notion_client, database_id, use_data_source=False):
    """
    Notion 데이터베이스의 스키마 정보를 가져옵니다.
    API 2025-09-03부터는 data_source를 사용할 수 있습니다.

    Args:
        notion_client: Notion API 클라이언트
        database_id: 데이터베이스 ID 또는 data_source ID
        use_data_source: data_source API 사용 여부 (기본값: False)

    Returns:
        데이터베이스 스키마 정보
    """
    try:
        if use_data_source:
            # 2025-09-03 버전: data_source 사용
            # 먼저 database를 조회하여 data_sources 목록 얻기
            database = notion_client.databases.retrieve(database_id=database_id)

            # data_sources가 있으면 첫 번째 data_source의 스키마 반환
            if 'data_sources' in database and database['data_sources']:
                # data_source_id를 사용하여 스키마 가져오기
                data_source_id = database['data_sources'][0]['id']
                # 실제 data_source 조회는 /v1/data_sources API를 사용해야 하지만
                # 현재 SDK가 지원하지 않으므로 database 속성 사용
                properties = database.get('properties', {})
            else:
                # data_sources가 없으면 일반 database 속성 사용
                properties = database.get('properties', {})
        else:
            # 데이터베이스 정보 가져오기
            database = notion_client.databases.retrieve(database_id=database_id)

            # 속성 정보 추출
            properties = database.get('properties', {})
    except Exception as e:
        # 오류 발생 시 하위 호환 모드로 폴백
        if use_data_source:
            return get_database_schema(notion_client, database_id, use_data_source=False)
        raise

    schema = {}
    for name, prop in properties.items():
        schema[name] = prop['type']

    return schema

def get_data_sources(notion_client, database_id):
    """
    데이터베이스의 data_source 목록을 가져옵니다.
    API 2025-09-03 이상에서만 사용 가능합니다.

    Args:
        notion_client: Notion API 클라이언트
        database_id: 데이터베이스 ID

    Returns:
        data_source 목록 또는 None (지원하지 않는 경우)
    """
    try:
        database = notion_client.databases.retrieve(database_id=database_id)
        return database.get('data_sources', [])
    except Exception:
        return None
