#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: database_extractors
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Database Extractors Implementation
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
# MNGA-002: Import organization needs review
import json
import os
import psycopg2
import mysql.connector
import pymongo
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from .base_extractor import BaseExtractor
logger = logging.getLogger(__name__)
class PostgresExtractor(BaseExtractor):
    """
    PostgreSQL database extractor.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None
        self.cursor = None
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5432)
        self.database = config.get('database', 'default')
        self.user = config.get('user', 'postgres')
        self.password = config.get('password', '')
        self.sslmode = config.get('sslmode', 'require')
    def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                sslmode=self.sslmode
            )
            self.cursor = self.connection.cursor()
            logger.info(f"Connected to PostgreSQL: {self.host}:{self.port}/{self.database}")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {str(e)}")
            return False
    def extract(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract data from PostgreSQL."""
        if not self.cursor:
            raise Exception("Not connected to database")
        if not query:
            query = self.config.get('default_query', 'SELECT * FROM user_analytics LIMIT 1000')
        try:
            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description]
            rows = self.cursor.fetchall()
            data = []
            for row in rows:
                record = dict(zip(columns, row))
                for key, value in record.items():
                    if isinstance(value, datetime):
                        record[key] = value.isoformat()
                data.append(record)
            logger.info(f"Extracted {len(data)} records from PostgreSQL")
            return data
        except Exception as e:
            logger.error(f"PostgreSQL extraction failed: {str(e)}")
            raise
    def disconnect(self) -> bool:
        """Disconnect from PostgreSQL."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("Disconnected from PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL disconnection failed: {str(e)}")
            return False
class MySQLExtractor(BaseExtractor):
    """
    MySQL database extractor.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None
        self.cursor = None
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 3306)
        self.database = config.get('database', 'default')
        self.user = config.get('user', 'root')
        self.password = config.get('password', '')
        ssl_ca = config.get('ssl_ca')
        if not ssl_ca:
            for path in ('/etc/ssl/certs/ca-certificates.crt', '/etc/ssl/cert.pem'):
                if os.path.exists(path):
                    ssl_ca = path
                    break
        self.ssl_ca = ssl_ca
        self.ssl_disabled = config.get('ssl_disabled', False)
    def connect(self) -> bool:
        """Connect to MySQL database."""
        try:
            connection_kwargs = {
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.user,
                'password': self.password
            }
            if self.ssl_ca and not self.ssl_disabled:
                connection_kwargs['ssl_ca'] = self.ssl_ca
            self.connection = mysql.connector.connect(**connection_kwargs)
            self.cursor = self.connection.cursor(dictionary=True)
            logger.info(f"Connected to MySQL: {self.host}:{self.port}/{self.database}")
            return True
        except Exception as e:
            logger.error(f"MySQL connection failed: {str(e)}")
            return False
    def extract(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract data from MySQL."""
        if not self.cursor:
            raise Exception("Not connected to database")
        if not query:
            query = self.config.get('default_query', 'SELECT * FROM user_analytics LIMIT 1000')
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            for row in rows:
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.isoformat()
            logger.info(f"Extracted {len(rows)} records from MySQL")
            return rows
        except Exception as e:
            logger.error(f"MySQL extraction failed: {str(e)}")
            raise
    def disconnect(self) -> bool:
        """Disconnect from MySQL."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("Disconnected from MySQL")
            return True
        except Exception as e:
            logger.error(f"MySQL disconnection failed: {str(e)}")
            return False
class MongoExtractor(BaseExtractor):
    """
    MongoDB extractor.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.db = None
        self.connection_string = config.get('connection_string', 'mongodb://localhost:27017')
        self.database = config.get('database', 'default')
        self.ssl = config.get('ssl', True)
    def connect(self) -> bool:
        """Connect to MongoDB."""
        try:
            self.client = pymongo.MongoClient(self.connection_string, ssl=self.ssl)
            self.db = self.client[self.database]
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.database}")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            return False
    def extract(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract data from MongoDB."""
        if not self.db:
            raise Exception("Not connected to database")
        collection_name = self.config.get('collection', 'user_analytics')
        collection = self.db[collection_name]
        try:
            filter_query = {}
            if query:
                filter_query = json.loads(query)
            limit = self.config.get('limit', 1000)
            cursor = collection.find(filter_query).limit(limit)
            data = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                for key, value in doc.items():
                    if isinstance(value, datetime):
                        doc[key] = value.isoformat()
                data.append(doc)
            logger.info(f"Extracted {len(data)} records from MongoDB")
            return data
        except Exception as e:
            logger.error(f"MongoDB extraction failed: {str(e)}")
            raise
    def disconnect(self) -> bool:
        """Disconnect from MongoDB."""
        try:
            if self.client:
                self.client.close()
            logger.info("Disconnected from MongoDB")
            return True
        except Exception as e:
            logger.error(f"MongoDB disconnection failed: {str(e)}")
            return False
