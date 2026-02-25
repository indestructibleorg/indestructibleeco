#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: api_extractors
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
API Extractors Implementation
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
# MNGA-002: Import organization needs review
import requests
from typing import Dict, Any, List, Optional
import logging
from .base_extractor import BaseExtractor
logger = logging.getLogger(__name__)
class RestAPIExtractor(BaseExtractor):
    """
    REST API extractor.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session = requests.Session()
        self.base_url = config.get('base_url', '')
        self.api_key = config.get('api_key', '')
        self.timeout = config.get('timeout', 30)
        self.headers = config.get('headers', {})
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
    def connect(self) -> bool:
        """Verify API connectivity."""
        try:
            health_url = f"{self.base_url}/health" if self.base_url else None
            if health_url:
                response = self.session.get(health_url, timeout=self.timeout)
                response.raise_for_status()
            logger.info(f"Connected to API: {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"API connection failed: {str(e)}")
            return False
    def extract(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract data from REST API."""
        if not self.base_url:
            raise Exception("Base URL not configured")
        endpoint = query or self.config.get('default_endpoint', '/api/v1/data')
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                raise Exception("API response is not a valid JSON structure")
            logger.info(f"Extracted {len(data)} records from API")
            return data
        except Exception as e:
            logger.error(f"API extraction failed: {str(e)}")
            raise
    def disconnect(self) -> bool:
        """Close API session."""
        try:
            self.session.close()
            logger.info("Disconnected from API")
            return True
        except Exception as e:
            logger.error(f"API disconnection failed: {str(e)}")
            return False
class GraphQLExtractor(BaseExtractor):
    """
    GraphQL API extractor.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session = requests.Session()
        self.endpoint = config.get('endpoint', '')
        self.api_key = config.get('api_key', '')
        self.timeout = config.get('timeout', 30)
        self.headers = config.get('headers', {'Content-Type': 'application/json'})
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
    def connect(self) -> bool:
        """Verify GraphQL connectivity."""
        try:
            if self.endpoint:
                response = self.session.get(self.endpoint, timeout=self.timeout)
                response.raise_for_status()
            logger.info(f"Connected to GraphQL: {self.endpoint}")
            return True
        except Exception as e:
            logger.error(f"GraphQL connection failed: {str(e)}")
            return False
    def extract(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract data from GraphQL API."""
        if not self.endpoint:
            raise Exception("GraphQL endpoint not configured")
        graphql_query = query or self.config.get('default_query', '{ user_analytics { id name email } }')
        try:
            response = self.session.post(
                self.endpoint,
                json={'query': graphql_query},
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            if 'errors' in result:
                raise Exception(f"GraphQL errors: {result['errors']}")
            data = result.get('data', {})
            if not data:
                return []
            first_key = list(data.keys())[0]
            records = data[first_key]
            if isinstance(records, dict):
                records = [records]
            elif not isinstance(records, list):
                records = []
            logger.info(f"Extracted {len(records)} records from GraphQL")
            return records
        except Exception as e:
            logger.error(f"GraphQL extraction failed: {str(e)}")
            raise
    def disconnect(self) -> bool:
        """Close GraphQL session."""
        try:
            self.session.close()
            logger.info("Disconnected from GraphQL")
            return True
        except Exception as e:
            logger.error(f"GraphQL disconnection failed: {str(e)}")
            return False