from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json

# Load environment variables first
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import optional modules with error handling
try:
    from agents.crew_agents import create_research_crew
    CREW_AGENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Crew agents not available: {e}")
    CREW_AGENTS_AVAILABLE = False

try:
    from report_generator import generate_research_report
    REPORT_GEN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Report generator not available: {e}")
    REPORT_GEN_AVAILABLE = False

try:
    from mock_apis import get_iqvia_data, get_exim_data, get_patent_data
    MOCK_APIS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Mock APIs not available: {e}")
    MOCK_APIS_AVAILABLE = False

# MongoDB connection with error handling
try:
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'techathon_db')]
    MONGODB_AVAILABLE = True
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    MONGODB_AVAILABLE = False
    client = None
    db = None

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Research Query Models
class ResearchQuery(BaseModel):
    query: str
    
class ResearchResponse(BaseModel):
    id: str
    query: str
    status: str  # "processing", "completed", "failed"
    result: Optional[Dict[str, Any]] = None
    report_path: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    if not MONGODB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database not available")
    
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    if not MONGODB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database not available")
    
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Mock API Endpoints - only if available
if MOCK_APIS_AVAILABLE:
    @api_router.get("/mock/iqvia/{disease}")
    async def mock_iqvia(disease: str):
        """Get mock IQVIA market data"""
        return get_iqvia_data(disease)

    @api_router.get("/mock/exim/{disease}")
    async def mock_exim(disease: str):
        """Get mock EXIM trade data"""
        return get_exim_data(disease)

    @api_router.get("/mock/uspto/{disease}")
    async def mock_patent(disease: str):
        """Get mock patent data"""
        return get_patent_data(disease)

# Research Agent Endpoints - only if crew agents available
if CREW_AGENTS_AVAILABLE:
    @api_router.post("/research", response_model=ResearchResponse)
    async def start_research(query: ResearchQuery, background_tasks: BackgroundTasks):
        """
        Start a new research query using the Master Agent and Worker Agents
        """
        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=500, detail="Database not available")
        
        try:
            research_id = str(uuid.uuid4())
            
            # Create initial research record
            research_doc = {
                "id": research_id,
                "query": query.query,
                "status": "processing",
                "result": None,
                "report_path": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None
            }
            
            await db.research_queries.insert_one(research_doc)
            
            # Start research in background
            background_tasks.add_task(execute_research, research_id, query.query)
            
            return ResearchResponse(
                id=research_id,
                query=query.query,
                status="processing",
                created_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error starting research: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @api_router.get("/research/{research_id}", response_model=ResearchResponse)
    async def get_research_status(research_id: str):
        """
        Get the status of a research query
        """
        try:
            research = await db.research_queries.find_one({"id": research_id}, {"_id": 0})
            
            if not research:
                raise HTTPException(status_code=404, detail="Research not found")
            
            # Convert ISO strings to datetime
            research['created_at'] = datetime.fromisoformat(research['created_at'])
            if research.get('completed_at'):
                research['completed_at'] = datetime.fromisoformat(research['completed_at'])
            
            return ResearchResponse(**research)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting research status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @api_router.get("/research/{research_id}/download")
    async def download_report(research_id: str):
        """
        Download the PDF report for a completed research
        """
        try:
            research = await db.research_queries.find_one({"id": research_id}, {"_id": 0})
            
            if not research:
                raise HTTPException(status_code=404, detail="Research not found")
            
            if research['status'] != 'completed':
                raise HTTPException(status_code=400, detail="Research not completed yet")
            
            report_path = research.get('report_path')
            if not report_path or not os.path.exists(report_path):
                raise HTTPException(status_code=404, detail="Report file not found")
            
            return FileResponse(
                path=report_path,
                media_type='application/pdf',
                filename=f"research_report_{research_id}.pdf"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error downloading report: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def execute_research(research_id: str, query: str):
        """
        Background task to execute the research using CrewAI agents
        """
        try:
            logger.info(f"Starting research for ID: {research_id}")
            
            # Create and run the research crew
            crew = create_research_crew(query)
            result = crew.kickoff()
            
            logger.info(f"Research completed for ID: {research_id}")
            
            # Parse the result
            result_text = str(result)
            
            # Create structured data for report
            report_data = {
                'query': query,
                'executive_summary': result_text[:500],  # First 500 chars as summary
                'key_findings': [
                    'Comprehensive analysis of respiratory diseases in Indian market',
                    'Multi-agent intelligence gathering from clinical trials, market data, and patents',
                    'Strategic recommendations based on competition and opportunity assessment'
                ],
                'diseases': [
                    {
                        'name': 'ILD (Interstitial Lung Disease)',
                        'burden': 'High',
                        'competition': 'Low',
                        'market_size': '850 Cr INR',
                        'opportunity': 'High'
                    }
                ],
                'recommendations': [
                    'Focus on diseases with high patient burden and low competition',
                    'Monitor patent expirations for generic opportunities',
                    'Align with internal strategic priorities'
                ],
                'next_steps': [
                    'Conduct detailed feasibility analysis',
                    'Engage with key opinion leaders',
                    'Evaluate partnership opportunities'
                ]
            }
            
            # Generate PDF report
            report_path = None
            if REPORT_GEN_AVAILABLE:
                report_dir = ROOT_DIR / "reports"
                report_dir.mkdir(exist_ok=True)
                report_path = str(report_dir / f"report_{research_id}.pdf")
                
                generate_research_report(report_data, report_path)
            
            # Update database
            await db.research_queries.update_one(
                {"id": research_id},
                {
                    "$set": {
                        "status": "completed",
                        "result": {"raw_output": result_text, "structured_data": report_data},
                        "report_path": report_path,
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            logger.info(f"Report generated: {report_path}")
            
        except Exception as e:
            logger.error(f"Error executing research: {str(e)}")
            
            # Update status to failed
            await db.research_queries.update_one(
                {"id": research_id},
                {
                    "$set": {
                        "status": "failed",
                        "result": {"error": str(e)},
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
else:
    @api_router.post("/research", response_model=ResearchResponse)
    async def start_research(query: ResearchQuery, background_tasks: BackgroundTasks):
        raise HTTPException(status_code=501, detail="Research agents not available")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()