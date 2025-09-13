#!/usr/bin/env python3
"""
Notion-Hugo Metadata Management

This module provides metadata management functionality to track 
Notion page processing status and support incremental processing.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Set


class MetadataManager:
    """Notion-Hugo metadata management class"""
    
    def __init__(self, file_path: str = "src/config/.notion-hugo-state.json"):
        """
        MetadataManager 클래스 초기화
        
        Args:
            file_path: 메타데이터 파일 경로 (기본값: "src/config/.notion-hugo-state.json")
        """
        self.file_path = file_path
        self.metadata = self._load_or_create()
        
    def _load_or_create(self) -> Dict[str, Any]:
        """
        메타데이터 파일 로드 또는 새로 생성
        
        Returns:
            메타데이터 딕셔너리
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    metadata = json.load(f)
                    # 기본 필드 확인 및 추가
                    if "version" not in metadata:
                        metadata["version"] = "1.0"
                    if "last_sync" not in metadata:
                        metadata["last_sync"] = datetime.utcnow().isoformat() + "Z"
                    if "pages" not in metadata:
                        metadata["pages"] = {}
                    return metadata
            except (json.JSONDecodeError, IOError) as e:
                print(f"[Warn] 메타데이터 파일 손상: {str(e)}, 새로 생성합니다: {self.file_path}")
                
        # 기본 구조 생성
        return {
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "pages": {}
        }
        
    def save(self) -> None:
        """메타데이터 저장 (백업 포함)"""
        # 백업 생성 (이미 파일이 있는 경우)
        if os.path.exists(self.file_path):
            backup_path = f"{self.file_path}.bak"
            try:
                with open(self.file_path, 'r') as src:
                    with open(backup_path, 'w') as dst:
                        dst.write(src.read())
            except IOError:
                print(f"[Warn] 메타데이터 백업 생성 실패")
                
        # 업데이트 시간 갱신
        self.metadata["last_sync"] = datetime.utcnow().isoformat() + "Z"
                
        # 새 메타데이터 저장
        try:
            # 임시 파일에 쓰기
            temp_path = f"{self.file_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
                
            # 원자적 교체
            os.replace(temp_path, self.file_path)
        except IOError as e:
            print(f"[Error] 메타데이터 저장 실패: {str(e)}")
    
    def get_changed_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        변경된 페이지만 필터링
        
        Args:
            pages: 페이지 목록
            
        Returns:
            변경된 페이지 목록
        """
        changed_pages = []
        for page in pages:
            page_id = page["id"]
            last_edited = page.get("last_edited_time")
            
            # 메타데이터에 없거나 수정 시간이 다른 경우
            if (page_id not in self.metadata["pages"] or
                self.metadata["pages"][page_id].get("last_edited") != last_edited):
                changed_pages.append(page)
                
        return changed_pages
    
    def get_processed_page_ids(self) -> Set[str]:
        """
        처리된 페이지 ID 목록 반환
        
        Returns:
            처리된 페이지 ID 집합
        """
        return set(self.metadata["pages"].keys())
        
    def update_page_status(self, page_id: str, **kwargs) -> None:
        """
        페이지 상태 업데이트
        
        Args:
            page_id: 페이지 ID
            **kwargs: 업데이트할 상태 정보
        """
        if page_id not in self.metadata["pages"]:
            self.metadata["pages"][page_id] = {}
            
        # 처리 시간 자동 추가
        if "processed_at" not in kwargs:
            kwargs["processed_at"] = datetime.utcnow().isoformat() + "Z"
            
        # 전달된 속성으로 업데이트
        self.metadata["pages"][page_id].update(kwargs)
        
    def remove_page(self, page_id: str) -> None:
        """
        페이지 메타데이터 제거
        
        Args:
            page_id: 제거할 페이지 ID
        """
        if page_id in self.metadata["pages"]:
            del self.metadata["pages"][page_id]
        
    def get_orphaned_page_ids(self, current_page_ids: List[str]) -> List[str]:
        """
        현재 존재하지 않는 고아 페이지 ID 목록 반환
        
        Args:
            current_page_ids: 현재 존재하는 페이지 ID 목록
            
        Returns:
            고아 페이지 ID 목록
        """
        current_set = set(current_page_ids)
        tracked_set = self.get_processed_page_ids()
        
        return list(tracked_set - current_set)
        
    def compute_content_hash(self, content: str) -> str:
        """
        Content hash calculation
        
        Args:
            content: Content to calculate hash for
            
        Returns:
            SHA-256 hash value
        """
        if content is None:
            content = ""
        
        if not isinstance(content, str):
            content = str(content)
            
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def has_page_changed(self, page: Dict[str, Any]) -> bool:
        """
        Check if a page has changed since last processing.
        
        Args:
            page: Notion page object
            
        Returns:
            True if page has changed, False otherwise
        """
        page_id = page["id"]
        last_edited = page.get("last_edited_time")
        
        # If page is not in metadata, it's new (changed)
        if page_id not in self.metadata["pages"]:
            return True
            
        # Check if last edited time is different
        stored_edited = self.metadata["pages"][page_id].get("last_edited")
        return last_edited != stored_edited
