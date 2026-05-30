"""
Sovereign AI - Production FastAPI Application
API Layer สำหรับ Autonomous Agent
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import sys
from datetime import datetime
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sovereign AI API",
    description="Autonomous Agent API with Pattern-Driven Architecture",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ใน production ควรระบุ domain ที่ชัดเจน
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class QueryRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Input text to process")
    language: Optional[str] = Field(default="th", description="Language code (th, en)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")

class QueryResponse(BaseModel):
    intent: Optional[str] = None
    confidence: Optional[float] = None
    result: Optional[Any] = None
    response: Optional[str] = None
    processing_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    uptime_seconds: Optional[float] = None

# Global variables
start_time = datetime.now()

# Import core components
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Try multiple import paths for backwards compatibility
    try:
        from core.perception_engine import PerceptionEngine
        from core.planner_engine import PlannerEngine
        from core.execution_engine import ExecutionEngine
    except ImportError:
        from engines.perception import PerceptionEngine
        from engines.planner import PlannerEngine
        from engines.execution import ExecutionEngine
    
    from core.wreasoning import WReasoningEngine
    
    # Initialize engines
    perception_engine = PerceptionEngine()
    planner_engine = PlannerEngine()
    execution_engine = ExecutionEngine()
    reasoning_engine = WReasoningEngine()
    
    logger.info("All engines initialized successfully")
except Exception as e:
    logger.warning(f"Could not load all engines: {e}")
    logger.info("Running in minimal mode")
    perception_engine = None
    planner_engine = None
    execution_engine = None
    reasoning_engine = None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    current_time = datetime.now()
    uptime = (current_time - start_time).total_seconds()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=current_time.isoformat(),
        uptime_seconds=uptime
    )


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process user query and return response"""
    import time
    start = time.time()
    
    try:
        # Validate input
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        text = request.text.strip()
        language = request.language or "th"
        
        logger.info(f"Processing query: '{text[:100]}...' (language: {language})")
        
        # If engines are not loaded, return minimal response
        if perception_engine is None:
            return QueryResponse(
                intent="UNKNOWN",
                confidence=0.0,
                response="Service initializing. Please try again.",
                processing_time_ms=(time.time() - start) * 1000
            )
        
        # Step 1: Perception - Detect intent
        try:
            # Different engines have different signatures
            import inspect
            sig = inspect.signature(perception_engine.analyze)
            if len(sig.parameters) > 1:
                intent_result = perception_engine.analyze(text, language)
            else:
                intent_result = perception_engine.analyze(text)
                # Add default confidence if not present
                if isinstance(intent_result, dict) and "confidence" not in intent_result:
                    intent_result["confidence"] = 0.8
        except Exception as e:
            logger.warning(f"Perception error: {e}")
            intent_result = {"intent": "UNKNOWN", "confidence": 0.0}
        
        intent = intent_result.get("intent", "UNKNOWN") if isinstance(intent_result, dict) else "UNKNOWN"
        confidence = intent_result.get("confidence", 0.0) if isinstance(intent_result, dict) else 0.0
        
        logger.info(f"Detected intent: {intent} (confidence: {confidence})")
        
        # Step 2: Reasoning - Advanced logic (if applicable)
        reasoning_result = None
        if reasoning_engine:
            try:
                reasoning_result = reasoning_engine.process(text)
                if reasoning_result and reasoning_result.get("type") != "unknown":
                    logger.info(f"Reasoning engine processed: {reasoning_result.get('type')}")
            except Exception as e:
                logger.warning(f"Reasoning engine error: {e}")
        
        # Step 3: Planning - Create execution plan
        plan = None
        if planner_engine and confidence > 0.5:
            try:
                plan = planner_engine.create_plan(intent, text)
                logger.info(f"Created plan with {len(plan.get('steps', []))} steps")
            except Exception as e:
                logger.warning(f"Planning error: {e}")
        
        # Step 4: Execution - Run tools if plan exists
        execution_result = None
        if execution_engine and plan:
            try:
                execution_result = execution_engine.execute(plan)
                logger.info(f"Execution completed: {execution_result.get('success', False)}")
            except Exception as e:
                logger.warning(f"Execution error: {e}")
        
        # Build response
        response_text = None
        result_data = None
        
        if reasoning_result and reasoning_result.get("type") != "unknown":
            response_text = reasoning_result.get("response", "")
            result_data = reasoning_result.get("result")
        elif execution_result and execution_result.get("success"):
            result_data = execution_result.get("result")
            response_text = str(result_data) if result_data else "Task completed"
        elif intent != "UNKNOWN":
            response_text = f"Detected intent: {intent}. Ready to execute."
        else:
            response_text = "I understand your input but I'm not sure how to help. Could you please rephrase?"
        
        processing_time = (time.time() - start) * 1000
        
        return QueryResponse(
            intent=intent,
            confidence=confidence,
            result=result_data,
            response=response_text,
            processing_time_ms=processing_time,
            metadata={
                "plan_steps": len(plan.get("steps", [])) if plan else 0,
                "reasoning_applied": reasoning_result is not None,
                "execution_completed": execution_result is not None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Sovereign AI API",
        "version": "1.0.0",
        "description": "Autonomous Agent with Pattern-Driven Architecture",
        "endpoints": {
            "health": "/health",
            "query": "/query (POST)",
            "docs": "/docs"
        }
    }


@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    return {
        "uptime_seconds": (datetime.now() - start_time).total_seconds(),
        "status": "operational",
        "engines": {
            "perception": "loaded" if perception_engine else "not_loaded",
            "planner": "loaded" if planner_engine else "not_loaded",
            "execution": "loaded" if execution_engine else "not_loaded",
            "reasoning": "loaded" if reasoning_engine else "not_loaded"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
