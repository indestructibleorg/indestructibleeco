#!/usr/bin/env python3
"""
推理 API 端點
Reasoning API Endpoint

@ECO-governed
@ECO-layer: GL30-39
@ECO-semantic: platform-reasoning-api

提供推理服務的 REST API 端點：
- 雙路檢索查詢
- 仲裁結果獲取
- 反饋提交
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys

# 添加 ecosystem 到路徑
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))


@dataclass
class APIRequest:
    """API 請求"""
    request_id: str
    method: str
    path: str
    query_params: Dict[str, Any]
    body: Optional[Dict[str, Any]]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class APIResponse:
    """API 響應"""
    request_id: str
    status_code: int
    data: Any
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReasoningAPI:
    """
    推理 API 服務
    
    端點：
    - POST /api/v1/query - 執行推理查詢
    - GET /api/v1/results/{query_id} - 獲取查詢結果
    - POST /api/v1/feedback - 提交反饋
    - GET /api/v1/health - 健康檢查
    """
    
    def __init__(self):
        self.queries: Dict[str, Dict] = {}
        self.results: Dict[str, Dict] = {}
        self.feedback: List[Dict] = []
        
        # 嘗試載入推理組件
        self._load_components()
    
    def _load_components(self):
        """載入推理組件"""
        self.arbitrator = None
        self.internal_retrieval = None
        self.external_retrieval = None
        
        try:
            from ecosystem.reasoning.dual_path.arbitration.arbitrator import Arbitrator
            self.arbitrator = Arbitrator()
        except ImportError:
            pass
        
        try:
            from ecosystem.reasoning.dual_path.internal.retrieval import InternalRetrieval
            self.internal_retrieval = InternalRetrieval()
        except ImportError:
            pass
        
        try:
            from ecosystem.reasoning.dual_path.external.retrieval import ExternalRetrieval
            self.external_retrieval = ExternalRetrieval()
        except ImportError:
            pass
    
    def handle_query(self, request: APIRequest) -> APIResponse:
        """處理查詢請求"""
        body = request.body or {}
        query_text = body.get("query", "")
        query_type = body.get("type", "general")
        options = body.get("options", {})
        
        if not query_text:
            return APIResponse(
                request_id=request.request_id,
                status_code=400,
                data=None,
                error="Missing required field: query"
            )
        
        query_id = str(uuid.uuid4())
        
        # 執行查詢
        results = self._execute_query(query_text, query_type, options)
        
        # 存儲結果
        self.queries[query_id] = {
            "query_id": query_id,
            "query_text": query_text,
            "query_type": query_type,
            "options": options,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.results[query_id] = results
        
        return APIResponse(
            request_id=request.request_id,
            status_code=200,
            data={
                "query_id": query_id,
                "results": results,
                "metadata": {
                    "total_results": len(results.get("items", [])),
                    "sources_used": results.get("sources", []),
                    "confidence": results.get("confidence", 0.0)
                }
            }
        )
    
    def _execute_query(self, query_text: str, query_type: str, options: Dict) -> Dict:
        """執行實際查詢"""
        results = {
            "items": [],
            "sources": [],
            "confidence": 0.0,
            "metadata": {}
        }
        
        internal_results = []
        external_results = []
        
        # 內部檢索
        if self.internal_retrieval:
            try:
                internal_results = self.internal_retrieval.search(query_text)
                results["sources"].append("internal")
            except Exception as e:
                results["metadata"]["internal_error"] = str(e)
        
        # 外部檢索
        if self.external_retrieval and options.get("include_external", True):
            try:
                external_results = self.external_retrieval.search(query_text)
                results["sources"].append("external")
            except Exception as e:
                results["metadata"]["external_error"] = str(e)
        
        # 仲裁合併
        if self.arbitrator:
            try:
                merged = self.arbitrator.arbitrate(internal_results, external_results, query_type)
                results["items"] = merged.get("results", [])
                results["confidence"] = merged.get("confidence", 0.5)
            except Exception as e:
                results["metadata"]["arbitration_error"] = str(e)
                results["items"] = internal_results + external_results
                results["confidence"] = 0.5
        else:
            # 簡單合併
            results["items"] = internal_results + external_results
            results["confidence"] = 0.5 if results["items"] else 0.0
        
        return results
    
    def handle_get_results(self, request: APIRequest, query_id: str) -> APIResponse:
        """獲取查詢結果"""
        if query_id not in self.results:
            return APIResponse(
                request_id=request.request_id,
                status_code=404,
                data=None,
                error=f"Query not found: {query_id}"
            )
        
        return APIResponse(
            request_id=request.request_id,
            status_code=200,
            data={
                "query": self.queries.get(query_id, {}),
                "results": self.results[query_id]
            }
        )
    
    def handle_feedback(self, request: APIRequest) -> APIResponse:
        """處理反饋提交"""
        body = request.body or {}
        
        required_fields = ["query_id", "feedback_type", "value"]
        for field in required_fields:
            if field not in body:
                return APIResponse(
                    request_id=request.request_id,
                    status_code=400,
                    data=None,
                    error=f"Missing required field: {field}"
                )
        
        feedback_record = {
            "feedback_id": str(uuid.uuid4()),
            "query_id": body["query_id"],
            "result_id": body.get("result_id"),
            "feedback_type": body["feedback_type"],
            "value": body["value"],
            "user_comment": body.get("comment"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.feedback.append(feedback_record)
        
        return APIResponse(
            request_id=request.request_id,
            status_code=201,
            data={
                "feedback_id": feedback_record["feedback_id"],
                "message": "Feedback recorded successfully"
            }
        )
    
    def handle_health(self, request: APIRequest) -> APIResponse:
        """健康檢查"""
        components = {
            "arbitrator": self.arbitrator is not None,
            "internal_retrieval": self.internal_retrieval is not None,
            "external_retrieval": self.external_retrieval is not None
        }
        
        healthy = any(components.values())
        
        return APIResponse(
            request_id=request.request_id,
            status_code=200 if healthy else 503,
            data={
                "status": "healthy" if healthy else "degraded",
                "components": components,
                "version": "1.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


class ReasoningAPIHandler(BaseHTTPRequestHandler):
    """HTTP 請求處理器"""
    
    api = ReasoningAPI()
    
    def _send_response(self, response: APIResponse):
        """發送響應"""
        self.send_response(response.status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Request-ID", response.request_id)
        self.end_headers()
        
        body = {
            "data": response.data,
            "error": response.error,
            "timestamp": response.timestamp,
            "request_id": response.request_id
        }
        
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode())
    
    def _parse_request(self) -> APIRequest:
        """解析請求"""
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)
        
        body = None
        if self.headers.get("Content-Length"):
            content_length = int(self.headers["Content-Length"])
            body_bytes = self.rfile.read(content_length)
            try:
                body = json.loads(body_bytes.decode())
            except json.JSONDecodeError:
                body = {}
        
        return APIRequest(
            request_id=str(uuid.uuid4()),
            method=self.command,
            path=parsed.path,
            query_params=query_params,
            body=body
        )
    
    def do_GET(self):
        """處理 GET 請求"""
        request = self._parse_request()
        
        if request.path == "/api/v1/health":
            response = self.api.handle_health(request)
        elif request.path.startswith("/api/v1/results/"):
            query_id = request.path.split("/")[-1]
            response = self.api.handle_get_results(request, query_id)
        else:
            response = APIResponse(
                request_id=request.request_id,
                status_code=404,
                data=None,
                error="Endpoint not found"
            )
        
        self._send_response(response)
    
    def do_POST(self):
        """處理 POST 請求"""
        request = self._parse_request()
        
        if request.path == "/api/v1/query":
            response = self.api.handle_query(request)
        elif request.path == "/api/v1/feedback":
            response = self.api.handle_feedback(request)
        else:
            response = APIResponse(
                request_id=request.request_id,
                status_code=404,
                data=None,
                error="Endpoint not found"
            )
        
        self._send_response(response)
    
    def log_message(self, format, *args):
        """自定義日誌格式"""
        print(f"[{datetime.now().isoformat()}] {args[0]}")


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """運行 API 服務器"""
    server = HTTPServer((host, port), ReasoningAPIHandler)
    print(f"🚀 Reasoning API Server running at http://{host}:{port}")
    print(f"   Health check: http://{host}:{port}/api/v1/health")
    print(f"   Query endpoint: POST http://{host}:{port}/api/v1/query")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped")
        server.shutdown()


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reasoning API Server")
    parser.add_argument("--host", default="0.0.0.0", help="綁定地址")
    parser.add_argument("--port", type=int, default=8080, help="端口號")
    
    args = parser.parse_args()
    
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()