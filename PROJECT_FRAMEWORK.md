# Project Framework & Architecture

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Project Structure](#project-structure)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [API Framework](#api-framework)
6. [Frontend Framework](#frontend-framework)
7. [Agent System Framework](#agent-system-framework)
8. [Development Patterns](#development-patterns)
9. [Code Organization](#code-organization)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  React Application (Port 3000)                          │  │
│  │  - ChatInterface Component                            │  │
│  │  - UI Components (shadcn/ui)                          │  │
│  │  - State Management (React Hooks)                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST API
                            │ (Axios)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend Layer                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  FastAPI Server (Port 8000)                            │  │
│  │  - REST API Endpoints                                  │  │
│  │  - Request Validation (Pydantic)                      │  │
│  │  - Background Tasks                                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Agent Orchestration Layer                             │  │
│  │  - Master Agent                                        │  │
│  │  - Worker Agents (7 specialized agents)                │  │
│  │  - CrewAI Framework                                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Tools & Services Layer                                │  │
│  │  - Clinical Trials API                                  │  │
│  │  - Market Data (IQVIA)                                 │  │
│  │  - Patent Data (USPTO)                                 │  │
│  │  - Web Search (Tavily)                                 │  │
│  │  - Report Generator                                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────────────┐  ┌──────────────────────────┐  │
│  │  MongoDB              │  │  File System              │  │
│  │  - Research Queries   │  │  - PDF Reports           │  │
│  │  - Status Checks      │  │  - Generated Reports     │  │
│  └──────────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

### Directory Organization

```
Techathon-main/
│
├── backend/                          # Backend Application
│   ├── agents/                       # AI Agent Definitions
│   │   ├── __init__.py              # Package initialization
│   │   ├── crew_agents.py          # Agent creation & orchestration
│   │   └── tools.py                 # Agent tools & utilities
│   │
│   ├── server.py                    # FastAPI application entry point
│   ├── mock_apis.py                 # Mock data providers
│   ├── report_generator.py          # PDF report generation
│   ├── test_agents.py                # Agent testing utilities
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Environment variables (create this)
│   └── reports/                     # Generated PDF reports (auto-created)
│
├── frontend/                         # Frontend Application
│   ├── src/
│   │   ├── components/              # React Components
│   │   │   ├── ChatInterface.jsx   # Main chat interface
│   │   │   └── ui/                  # shadcn/ui components
│   │   │
│   │   ├── hooks/                   # Custom React Hooks
│   │   │   └── use-toast.js
│   │   │
│   │   ├── lib/                     # Utility Libraries
│   │   │   └── utils.js
│   │   │
│   │   ├── App.js                   # Main App component
│   │   ├── App.css                  # App styles
│   │   ├── index.js                 # React entry point
│   │   └── index.css                # Global styles
│   │
│   ├── public/                       # Static Assets
│   │   └── index.html              # HTML template
│   │
│   ├── plugins/                     # Build Plugins
│   │   ├── health-check/            # Health check plugin
│   │   └── visual-edits/            # Visual edits plugin
│   │
│   ├── package.json                 # Node dependencies
│   ├── tailwind.config.js           # Tailwind configuration
│   ├── craco.config.js               # CRACO configuration
│   └── .env                         # Environment variables (create this)
│
├── tests/                            # Test Files
│   └── __init__.py
│
├── README.md                         # Project overview
├── SETUP.md                          # Setup instructions
├── API_KEYS_SETUP.md                 # API keys guide
└── PROJECT_FRAMEWORK.md              # This file
```

---

## Component Architecture

### Backend Components

#### 1. **Server Layer** (`server.py`)
- **Responsibility**: HTTP API, request handling, routing
- **Pattern**: RESTful API with FastAPI
- **Key Components**:
  - FastAPI app instance
  - API router (`/api` prefix)
  - Pydantic models for validation
  - Background task management
  - CORS middleware

#### 2. **Agent Layer** (`agents/`)
- **Responsibility**: AI agent orchestration
- **Pattern**: Master-Worker architecture
- **Key Components**:
  - `crew_agents.py`: Agent definitions and crew creation
  - `tools.py`: Agent tools and utilities
  - Master Agent: Orchestrates research
  - 7 Worker Agents: Specialized tasks

#### 3. **Service Layer**
- **`mock_apis.py`**: Mock data providers
- **`report_generator.py`**: PDF generation service
- **Tools**: External API integrations

#### 4. **Data Layer**
- **MongoDB**: Persistent storage (Motor async driver)
- **File System**: PDF report storage

### Frontend Components

#### 1. **Presentation Layer**
- **`ChatInterface.jsx`**: Main application interface
- **UI Components**: shadcn/ui component library
- **Styling**: Tailwind CSS

#### 2. **State Management**
- **React Hooks**: `useState`, `useEffect`, `useCallback`
- **Local State**: Component-level state management
- **API State**: Axios for HTTP requests

#### 3. **Routing**
- **React Router**: Single-page application routing

---

## Data Flow

### Research Query Flow

```
1. User Input
   └─> ChatInterface.jsx
       └─> handleSubmit()
           └─> POST /api/research
               └─> server.py: start_research()
                   ├─> Create research record in MongoDB
                   ├─> Return research_id immediately
                   └─> Background Task: execute_research()
                       │
                       ├─> create_research_crew()
                       │   └─> CrewAI orchestration
                       │       ├─> Master Agent: Plan research
                       │       ├─> Worker Agents: Execute tasks
                       │       │   ├─> Clinical Trials Agent
                       │       │   ├─> Market Intelligence Agent
                       │       │   ├─> Patent Intelligence Agent
                       │       │   ├─> Web Intelligence Agent
                       │       │   ├─> Trade Intelligence Agent
                       │       │   ├─> Internal Knowledge Agent
                       │       │   └─> Synthesis Agent
                       │       └─> Aggregate results
                       │
                       ├─> Generate structured data
                       ├─> generate_research_report() → PDF
                       └─> Update MongoDB: status = "completed"
                           │
                           └─> Frontend polls GET /api/research/{id}
                               └─> Display results & download link
```

### Status Polling Flow

```
Frontend (every 3 seconds)
  └─> GET /api/research/{research_id}
      └─> server.py: get_research_status()
          └─> Query MongoDB
              └─> Return ResearchResponse
                  └─> Update UI state
                      └─> If completed/failed: Stop polling
```

---

## API Framework

### API Design Principles

1. **RESTful Design**: Standard HTTP methods and status codes
2. **Versioning**: All endpoints under `/api` prefix
3. **Validation**: Pydantic models for request/response validation
4. **Error Handling**: Consistent error responses
5. **Documentation**: Auto-generated Swagger/OpenAPI docs

### API Endpoints

#### Base URL: `http://localhost:8000/api`

#### Status Endpoints
```
GET    /api/                    # Health check
POST   /api/status              # Create status check
GET    /api/status              # Get all status checks
```

#### Research Endpoints
```
POST   /api/research            # Start research query
GET    /api/research/{id}       # Get research status
GET    /api/research/{id}/download  # Download PDF report
```

#### Mock Data Endpoints
```
GET    /api/mock/iqvia/{disease}    # Mock IQVIA data
GET    /api/mock/exim/{disease}     # Mock EXIM data
GET    /api/mock/uspto/{disease}    # Mock patent data
```

### Request/Response Models

#### Request Models
```python
class ResearchQuery(BaseModel):
    query: str
```

#### Response Models
```python
class ResearchResponse(BaseModel):
    id: str
    query: str
    status: str  # "processing", "completed", "failed"
    result: Optional[Dict[str, Any]]
    report_path: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
```

### Error Handling

```python
# Standard error response
{
    "detail": "Error message"
}

# HTTP Status Codes
200: Success
400: Bad Request
404: Not Found
500: Internal Server Error
501: Not Implemented
```

---

## Frontend Framework

### Component Structure

#### Main Component: `ChatInterface.jsx`

```javascript
// State Management
const [query, setQuery] = useState('')
const [researches, setResearches] = useState([])
const [loading, setLoading] = useState(false)
const [pollingId, setPollingId] = useState(null)

// API Configuration
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'
const API = `${BACKEND_URL}/api`

// Key Functions
- handleSubmit()      // Submit research query
- checkResearchStatus() // Poll for status updates
- handleDownload()    // Download PDF report
```

### State Management Pattern

```javascript
// Local Component State
useState() for component-specific state

// API State
- Loading states
- Error handling
- Data caching

// Polling Pattern
useEffect(() => {
  if (pollingId) {
    const interval = setInterval(() => {
      checkResearchStatus(pollingId)
    }, 3000)
    return () => clearInterval(interval)
  }
}, [pollingId, checkResearchStatus])
```

### Styling Framework

- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Component library built on Radix UI
- **Responsive Design**: Mobile-first approach

---

## Agent System Framework

### Agent Architecture

```
Master Agent (Orchestrator)
    │
    ├─> Clinical Trials Agent
    │   └─> Tool: search_clinical_trials()
    │
    ├─> Market Intelligence Agent
    │   └─> Tool: iqvia_market_tool()
    │
    ├─> Trade Intelligence Agent
    │   └─> Tool: exim_trade_tool()
    │
    ├─> Patent Intelligence Agent
    │   └─> Tool: patent_landscape_tool()
    │
    ├─> Web Intelligence Agent
    │   └─> Tool: web_search_tool()
    │
    ├─> Internal Knowledge Agent
    │   └─> Tool: internal_knowledge_tool()
    |---> 
    │
    └─> Synthesis Agent
        └─> Synthesize all findings
```

### Agent Definition Pattern

```python
def create_agent():
    return Agent(
        role="Agent Role",
        goal="Agent Goal",
        backstory="Agent Backstory",
        verbose=True,
        allow_delegation=False,
        tools=[tool1, tool2],
        llm=get_llm()
    )
```

### Crew Creation Pattern

```python
def create_research_crew(query: str):
    # Create agents
    master = create_master_agent()
    worker1 = create_worker_agent_1()
    # ... more agents
    
    # Create tasks
    task1 = Task(description="...", agent=worker1)
    # ... more tasks
    
    # Create crew
    crew = Crew(
        agents=[master, worker1, ...],
        tasks=[task1, ...],
        process=Process.sequential,
        verbose=True
    )
    return crew
```

### Tool Definition Pattern

```python
@tool("Tool Name")
def tool_function(param: str) -> str:
    """
    Tool description.
    Useful for specific purpose.
    """
    # Tool implementation
    return json.dumps(result)
```

---

## Development Patterns

### Backend Patterns

#### 1. **Error Handling Pattern**
```python
try:
    # Operation
    result = await db.collection.find_one({})
except Exception as e:
    logger.error(f"Error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
```

#### 2. **Availability Check Pattern**
```python
if not MONGODB_AVAILABLE:
    raise HTTPException(status_code=500, detail="Database not available")
```

#### 3. **Background Task Pattern**
```python
@api_router.post("/research")
async def start_research(query: ResearchQuery, background_tasks: BackgroundTasks):
    # Create record
    research_id = str(uuid.uuid4())
    await db.research_queries.insert_one({...})
    
    # Start background task
    background_tasks.add_task(execute_research, research_id, query.query)
    
    # Return immediately
    return ResearchResponse(id=research_id, ...)
```

#### 4. **Model Validation Pattern**
```python
class ResearchQuery(BaseModel):
    query: str  # Required field
    
class ResearchResponse(BaseModel):
    id: str
    status: str
    result: Optional[Dict[str, Any]] = None  # Optional field
```

### Frontend Patterns

#### 1. **API Call Pattern**
```javascript
const handleSubmit = async (e) => {
  e.preventDefault()
  setLoading(true)
  try {
    const response = await axios.post(`${API}/research`, { query })
    // Handle success
  } catch (error) {
    // Handle error
  } finally {
    setLoading(false)
  }
}
```

#### 2. **Polling Pattern**
```javascript
useEffect(() => {
  if (pollingId) {
    const interval = setInterval(() => {
      checkResearchStatus(pollingId)
    }, 3000)
    return () => clearInterval(interval)
  }
}, [pollingId, checkResearchStatus])
```

#### 3. **State Update Pattern**
```javascript
setResearches(prev =>
  prev.map(r => r.id === id ? updatedResearch : r)
)
```

---

## Code Organization

### File Naming Conventions

- **Python**: `snake_case.py`
- **JavaScript/React**: `PascalCase.jsx` for components, `camelCase.js` for utilities
- **Constants**: `UPPER_SNAKE_CASE`

### Import Organization

#### Python
```python
# Standard library
import os
from pathlib import Path

# Third-party
from fastapi import FastAPI
from pydantic import BaseModel

# Local
from agents.crew_agents import create_research_crew
```

#### JavaScript
```javascript
// React
import React, { useState, useEffect } from 'react'

// Third-party
import axios from 'axios'
import { Send, Download } from 'lucide-react'

// Local
import ChatInterface from './components/ChatInterface'
```

### Code Structure

#### Function Organization
1. Imports
2. Constants
3. Helper functions
4. Main functions
5. Entry point (if applicable)

#### Class Organization
1. Class variables
2. `__init__` method
3. Public methods
4. Private methods

---

## Environment Configuration

### Backend Environment Variables

```env
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=techathon_db

# CORS
CORS_ORIGINS=http://localhost:3000

# API Keys
GEMINI_API_KEY=your_key
TAVILY_API_KEY=your_key
```

### Frontend Environment Variables

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

---

## Testing Framework

### Backend Testing
- **Location**: `backend/test_agents.py`
- **Purpose**: Verify agent system functionality
- **Pattern**: Script-based testing

### Frontend Testing
- **Framework**: React Testing Library (if configured)
- **Pattern**: Component testing

---

## Deployment Considerations

### Backend
- **Server**: Uvicorn/ASGI server
- **Process Manager**: Systemd, PM2, or Docker
- **Environment**: Production `.env` file

### Frontend
- **Build**: `npm run build` or `yarn build`
- **Hosting**: Static file hosting (Nginx, Vercel, Netlify)
- **Environment**: Production `.env` file

---

## Best Practices

### Backend
1. ✅ Always validate input with Pydantic models
2. ✅ Use async/await for I/O operations
3. ✅ Implement proper error handling
4. ✅ Log important events
5. ✅ Use environment variables for configuration
6. ✅ Check service availability before use

### Frontend
1. ✅ Handle loading and error states
2. ✅ Clean up intervals/effects
3. ✅ Use environment variables for API URLs
4. ✅ Implement proper error handling
5. ✅ Optimize re-renders with useCallback/useMemo
6. ✅ Provide user feedback for all actions

### General
1. ✅ Follow consistent naming conventions
2. ✅ Document complex logic
3. ✅ Keep functions focused and small
4. ✅ Use type hints (Python) and PropTypes (React)
5. ✅ Version control all code
6. ✅ Never commit `.env` files

---

## Extension Points

### Adding New Agents
1. Create agent function in `crew_agents.py`
2. Create corresponding tool in `tools.py`
3. Add agent to crew in `create_research_crew()`
4. Create task for the agent

### Adding New API Endpoints
1. Define Pydantic models
2. Create route handler in `server.py`
3. Add to `api_router`
4. Update frontend to use new endpoint

### Adding New Frontend Features
1. Create component in `src/components/`
2. Add routing if needed
3. Integrate with backend API
4. Update state management

---

## Summary

This framework provides:
- **Clear Architecture**: Separation of concerns
- **Consistent Patterns**: Reusable code patterns
- **Scalability**: Easy to extend and maintain
- **Best Practices**: Industry-standard approaches
- **Documentation**: Self-documenting code structure

Use this framework as a guide for development, and refer to it when adding new features or making changes to the codebase.

