#!/usr/bin/env python3
"""
노션 블로그 품질 관리 파이프라인
Author: Gunn Kim
"""

import json
import argparse
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import yaml

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlogPost:
    """블로그 포스트 데이터 클래스"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = ""
        self.frontmatter = {}
        self.body = ""
        self._load_post()
    
    def _load_post(self):
        """마크다운 파일에서 포스트 데이터 로드"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Frontmatter와 본문 분리
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    self.frontmatter = yaml.safe_load(parts[1])
                    self.body = parts[2].strip()
                else:
                    self.body = content
            else:
                self.body = content
                
        except Exception as e:
            logger.error(f"포스트 로드 실패: {self.file_path}, {e}")
    
    @property
    def title(self) -> str:
        return self.frontmatter.get('title', '')
    
    @property
    def author(self) -> str:
        return self.frontmatter.get('author', '')
    
    @property
    def description(self) -> str:
        return self.frontmatter.get('description', '')
    
    @property
    def slug(self) -> str:
        return self.frontmatter.get('slug', '')
    
    @property
    def tags(self) -> List[str]:
        tags = self.frontmatter.get('tags', [])
        if isinstance(tags, str):
            return [tags]
        return tags or []
    
    @property
    def keywords(self) -> List[str]:
        keywords = self.frontmatter.get('keywords', [])
        if isinstance(keywords, str):
            return [keywords]
        return keywords or []
    
    @property
    def date(self) -> str:
        return self.frontmatter.get('date', '')
    
    @property
    def draft(self) -> bool:
        return self.frontmatter.get('draft', False)
    
    @property
    def summary(self) -> str:
        return self.frontmatter.get('summary', '')

class QualityEvaluator:
    """블로그 품질 평가 엔진"""
    
    def __init__(self):
        self.issues = []
        self.auto_fixable = []
    
    def evaluate_post(self, post: BlogPost) -> Dict:
        """포스트 전체 품질 평