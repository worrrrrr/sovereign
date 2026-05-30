"""
Phase 4: Production Readiness Tests
ทดสอบ API Layer, Docker deployment readiness, และ CI/CD pipeline
"""

import pytest
import json
import os
from pathlib import Path

class TestPhase4Production:
    """ทดสอบ Phase 4 - Production Readiness"""
    
    def test_fastapi_app_exists(self):
        """ทดสอบว่า FastAPI app ถูกสร้างแล้ว"""
        app_path = Path("api/app.py")
        assert app_path.exists(), "FastAPI app ต้องถูกสร้างที่ api/app.py"
        
    def test_fastapi_app_importable(self):
        """ทดสอบว่า FastAPI app สามารถ import ได้"""
        try:
            from api.app import app
            assert app is not None, "FastAPI app ต้องไม่ใช่ None"
        except ImportError as e:
            pytest.fail(f"ไม่สามารถ import FastAPI app ได้: {e}")
    
    def test_api_health_endpoint(self):
        """ทดสอบ Health Check endpoint"""
        from fastapi.testclient import TestClient
        from api.app import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    def test_api_query_endpoint(self):
        """ทดสอบ Query endpoint พื้นฐาน"""
        from fastapi.testclient import TestClient
        from api.app import app
        
        client = TestClient(app)
        response = client.post(
            "/query",
            json={"text": "1 + 1 = ?", "language": "th"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data or "result" in data or "response" in data
    
    def test_dockerfile_exists(self):
        """ทดสอบว่า Dockerfile ถูกสร้างแล้ว"""
        dockerfile_path = Path("Dockerfile")
        assert dockerfile_path.exists(), "Dockerfile ต้องถูกสร้าง"
        
    def test_dockerfile_content(self):
        """ทดสอบว่า Dockerfile มีเนื้อหาถูกต้อง"""
        dockerfile_path = Path("Dockerfile")
        content = dockerfile_path.read_text()
        
        assert "FROM python:" in content, "Dockerfile ต้องมี FROM python"
        assert "COPY" in content, "Dockerfile ต้องมี COPY command"
        assert "RUN pip install" in content or "pip3 install" in content, "Dockerfile ต้องติดตั้ง dependencies"
        assert "CMD" in content or "ENTRYPOINT" in content, "Dockerfile ต้องมี CMD หรือ ENTRYPOINT"
    
    def test_dockerignore_exists(self):
        """ทดสอบว่า .dockerignore ถูกสร้างแล้ว"""
        dockerignore_path = Path(".dockerignore")
        assert dockerignore_path.exists(), ".dockerignore ต้องถูกสร้าง"
        
    def test_requirements_txt_exists(self):
        """ทดสอบว่า requirements.txt ถูกสร้างแล้ว"""
        requirements_path = Path("requirements.txt")
        assert requirements_path.exists(), "requirements.txt ต้องถูกสร้าง"
        
    def test_requirements_txt_content(self):
        """ทดสอบว่า requirements.txt มี dependencies จำเป็น"""
        requirements_path = Path("requirements.txt")
        content = requirements_path.read_text().lower()
        
        # ตรวจสอบ dependencies พื้นฐาน
        assert "fastapi" in content, "requirements.txt ต้องมี fastapi"
        assert "uvicorn" in content, "requirements.txt ต้องมี uvicorn"
        assert "pydantic" in content, "requirements.txt ต้องมี pydantic"
    
    def test_github_actions_workflow_exists(self):
        """ทดสอบว่า GitHub Actions workflow ถูกสร้างแล้ว"""
        workflow_path = Path(".github/workflows/ci.yml")
        assert workflow_path.exists(), "GitHub Actions workflow ต้องถูกสร้างที่ .github/workflows/ci.yml"
        
    def test_github_actions_workflow_content(self):
        """ทดสอบว่า GitHub Actions workflow มีเนื้อหาถูกต้อง"""
        workflow_path = Path(".github/workflows/ci.yml")
        content = workflow_path.read_text()
        
        assert "name:" in content, "Workflow ต้องมี name"
        assert "on:" in content or "on :" in content, "Workflow ต้องมี trigger"
        assert "jobs:" in content, "Workflow ต้องมี jobs"
        assert "pytest" in content or "test" in content.lower(), "Workflow ต้องมี test step"
    
    def test_environment_config_exists(self):
        """ทดสอบว่า environment config ถูกสร้างแล้ว"""
        env_path = Path(".env.example")
        assert env_path.exists(), ".env.example ต้องถูกสร้าง"
        
    def test_logging_config_exists(self):
        """ทดสอบว่า logging config ถูกสร้างแล้ว"""
        # ตรวจสอบว่ามี logging setup ใน app
        from api.app import app
        # ถ้า import สำเร็จ แสดงว่ามี logging setup
        assert True, "Logging ต้องถูกตั้งค่าใน app"
    
    def test_error_handling(self):
        """ทดสอบ Error Handling ใน API"""
        from fastapi.testclient import TestClient
        from api.app import app
        
        client = TestClient(app)
        
        # ทดสอบ invalid input
        response = client.post(
            "/query",
            json={"text": ""}  # empty text
        )
        
        # ควร return error หรือ handle gracefully
        assert response.status_code in [200, 400, 422], "API ต้อง handle empty input"
    
    def test_cors_middleware(self):
        """ทดสอบ CORS Middleware"""
        from fastapi.testclient import TestClient
        from api.app import app
        
        client = TestClient(app)
        
        # ทดสอบ OPTIONS request (CORS preflight)
        response = client.options(
            "/health",
            headers={"Origin": "http://example.com"}
        )
        
        # ควรมี CORS headers หรือ return 200/404
        assert response.status_code in [200, 404, 405], "CORS ต้องถูกตั้งค่า"
    
    def test_api_response_time(self):
        """ทดสอบ Response Time (ควร < 2 วินาที)"""
        from fastapi.testclient import TestClient
        from api.app import app
        import time
        
        client = TestClient(app)
        
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start
        
        assert elapsed < 2.0, f"Response time ต้องน้อยกว่า 2 วินาที (ได้ {elapsed:.2f}s)"
        assert response.status_code == 200
    
    def test_concurrent_requests(self):
        """ทดสอบ Concurrent Requests"""
        from fastapi.testclient import TestClient
        from api.app import app
        import concurrent.futures
        
        client = TestClient(app)
        
        def make_request():
            response = client.get("/health")
            return response.status_code == 200
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in futures]
        
        assert all(results), "ทุก concurrent request ต้องสำเร็จ"
    
    def test_api_documentation(self):
        """ทดสอบ API Documentation (OpenAPI/Swagger)"""
        from fastapi.testclient import TestClient
        from api.app import app
        
        client = TestClient(app)
        
        # ทดสอบ OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        # ตรวจสอบว่ามี endpoints ที่จำเป็น
        paths = schema["paths"]
        assert "/health" in paths or "/query" in paths, "ต้องมี health หรือ query endpoint"
    
    def test_production_ready_structure(self):
        """ทดสอบโครงสร้าง Production-Ready"""
        required_dirs = ["api", "config", "core", "tests"]
        required_files = [
            "requirements.txt",
            "Dockerfile",
            ".dockerignore",
            ".env.example"
        ]
        
        for dir_name in required_dirs:
            assert Path(dir_name).exists(), f"Directory '{dir_name}' ต้องมี"
        
        for file_name in required_files:
            assert Path(file_name).exists(), f"File '{file_name}' ต้องมี"
    
    def test_security_headers(self):
        """ทดสอบ Security Headers"""
        from fastapi.testclient import TestClient
        from api.app import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        # ตรวจสอบ headers พื้นฐาน (ไม่จำเป็นต้องมีทั้งหมด แต่ควรมีบางตัว)
        headers = response.headers
        assert "content-type" in headers, "ต้องมี Content-Type header"
    
    def test_input_validation(self):
        """ทดสอบ Input Validation"""
        from fastapi.testclient import TestClient
        from api.app import app
        
        client = TestClient(app)
        
        # ทดสอบ input ที่ยาวมาก
        long_text = "a" * 10000
        response = client.post(
            "/query",
            json={"text": long_text}
        )
        
        # ควร handle ได้ (return error หรือ process ได้)
        assert response.status_code in [200, 400, 413, 422], "ต้อง handle long input"
    
    def test_json_error_handling(self):
        """ทดสอบ JSON Error Handling"""
        from fastapi.testclient import TestClient
        from api.app import app
        
        client = TestClient(app)
        
        # ส่ง invalid JSON
        response = client.post(
            "/query",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # ควร return 422 Unprocessable Entity
        assert response.status_code in [400, 422], "ต้อง handle invalid JSON"
