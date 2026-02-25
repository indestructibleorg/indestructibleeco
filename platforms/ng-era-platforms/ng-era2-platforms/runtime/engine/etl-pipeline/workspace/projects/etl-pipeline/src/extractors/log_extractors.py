#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: log_extractors
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Log Extractors Implementation
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
import re
import gzip
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from pathlib import Path
from .base_extractor import BaseExtractor
logger = logging.getLogger(__name__)
class ApacheLogExtractor(BaseExtractor):
    """
    Apache access log extractor.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.log_file = config.get('log_file', '')
        self.log_format = config.get('log_format', 'combined')
        self.max_lines = config.get('max_lines', 10000)
        self.log_patterns = {
            'common': re.compile(
                r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<path>[^\s]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<size>\d+)'
            ),
            'combined': re.compile(
                r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<path>[^\s]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<size>\d+) "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)"'
            )
        }
    def connect(self) -> bool:
        """Verify log file exists and is readable."""
        try:
            log_path = Path(self.log_file)
            if not log_path.exists():
                logger.error(f"Log file not found: {self.log_file}")
                return False
            if not log_path.is_file():
                logger.error(f"Path is not a file: {self.log_file}")
                return False
            logger.info(f"Connected to log file: {self.log_file}")
            return True
        except Exception as e:
            logger.error(f"Log file connection failed: {str(e)}")
            return False
    def extract(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract data from Apache log file."""
        pattern = self.log_patterns.get(self.log_format, self.log_patterns['combined'])
        try:
            records = []
            line_count = 0
            open_func = gzip.open if self.log_file.endswith('.gz') else open
            with open_func(self.log_file, 'rt', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line_count >= self.max_lines:
                        break
                    match = pattern.match(line.strip())
                    if match:
                        record = match.groupdict()
                        record['timestamp'] = self._parse_timestamp(record['timestamp'])
                        record['status'] = int(record['status'])
                        record['size'] = int(record.get('size', 0))
                        records.append(record)
                    line_count += 1
            logger.info(f"Extracted {len(records)} records from Apache log")
            return records
        except Exception as e:
            logger.error(f"Apache log extraction failed: {str(e)}")
            raise
    def disconnect(self) -> bool:
        """No disconnection needed for file-based extraction."""
        logger.info("Disconnected from Apache log file")
        return True
    def _parse_timestamp(self, timestamp_str: str) -> str:
        """Parse Apache log timestamp."""
        try:
            dt = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
            return dt.isoformat()
        except Exception:
            return timestamp_str
class NginxLogExtractor(BaseExtractor):
    """
    Nginx access log extractor.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.log_file = config.get('log_file', '')
        self.log_format = config.get('log_format', 'combined')
        self.max_lines = config.get('max_lines', 10000)
        self.log_patterns = {
            'combined': re.compile(
                r'(?P<ip>\d+\.\d+\.\d+\.\d+) - (?P<user>[^\s]+) \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<path>[^\s]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<size>\d+) "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)"'
            ),
            'main': re.compile(
                r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<path>[^\s]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<size>\d+)'
            )
        }
    def connect(self) -> bool:
        """Verify log file exists and is readable."""
        try:
            log_path = Path(self.log_file)
            if not log_path.exists():
                logger.error(f"Log file not found: {self.log_file}")
                return False
            logger.info(f"Connected to log file: {self.log_file}")
            return True
        except Exception as e:
            logger.error(f"Log file connection failed: {str(e)}")
            return False
    def extract(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract data from Nginx log file."""
        pattern = self.log_patterns.get(self.log_format, self.log_patterns['combined'])
        try:
            records = []
            line_count = 0
            open_func = gzip.open if self.log_file.endswith('.gz') else open
            with open_func(self.log_file, 'rt', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line_count >= self.max_lines:
                        break
                    match = pattern.match(line.strip())
                    if match:
                        record = match.groupdict()
                        record['timestamp'] = self._parse_timestamp(record['timestamp'])
                        record['status'] = int(record['status'])
                        record['size'] = int(record.get('size', 0))
                        records.append(record)
                    line_count += 1
            logger.info(f"Extracted {len(records)} records from Nginx log")
            return records
        except Exception as e:
            logger.error(f"Nginx log extraction failed: {str(e)}")
            raise
    def disconnect(self) -> bool:
        """No disconnection needed for file-based extraction."""
        logger.info("Disconnected from Nginx log file")
        return True
    def _parse_timestamp(self, timestamp_str: str) -> str:
        """Parse Nginx log timestamp."""
        try:
            dt = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
            return dt.isoformat()
        except Exception:
            return timestamp_str
class ApplicationLogExtractor(BaseExtractor):
    """
    Generic application log extractor.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.log_file = config.get('log_file', '')
        self.log_pattern = config.get('log_pattern', r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<message>.*)')
        self.max_lines = config.get('max_lines', 10000)
        self.compiled_pattern = re.compile(self.log_pattern)
    def connect(self) -> bool:
        """Verify log file exists and is readable."""
        try:
            log_path = Path(self.log_file)
            if not log_path.exists():
                logger.error(f"Log file not found: {self.log_file}")
                return False
            logger.info(f"Connected to log file: {self.log_file}")
            return True
        except Exception as e:
            logger.error(f"Log file connection failed: {str(e)}")
            return False
    def extract(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract data from application log file."""
        try:
            records = []
            line_count = 0
            open_func = gzip.open if self.log_file.endswith('.gz') else open
            with open_func(self.log_file, 'rt', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line_count >= self.max_lines:
                        break
                    match = self.compiled_pattern.match(line.strip())
                    if match:
                        record = match.groupdict()
                        record['timestamp'] = self._parse_timestamp(record['timestamp'])
                        records.append(record)
                    else:
                        records.append({
                            'raw_line': line.strip(),
                            'timestamp': datetime.utcnow().isoformat(),
                            'level': 'UNKNOWN',
                            'message': line.strip()
                        })
                    line_count += 1
            logger.info(f"Extracted {len(records)} records from application log")
            return records
        except Exception as e:
            logger.error(f"Application log extraction failed: {str(e)}")
            raise
    def disconnect(self) -> bool:
        """No disconnection needed for file-based extraction."""
        logger.info("Disconnected from application log file")
        return True
    def _parse_timestamp(self, timestamp_str: str) -> str:
        """Parse application log timestamp."""
        try:
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            return dt.isoformat()
        except Exception:
            return timestamp_str