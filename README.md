# Techathon - Master Agent Intelligence Platform

A pharmaceutical research orchestration platform powered by AI agents.

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install  # or yarn install
npm start    # or yarn start
```

### Environment Variables

**Backend** (`backend/.env`):
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=techathon_db
CORS_ORIGINS=http://localhost:3000
GEMINI_API_KEY=your_key_here  # Optional
TAVILY_API_KEY=your_key_here  # Optional
```

**Frontend** (`frontend/.env`):
```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

## Documentation

- **[SETUP.md](SETUP.md)** - Complete setup instructions and troubleshooting
- **[PROJECT_FRAMEWORK.md](PROJECT_FRAMEWORK.md)** - Comprehensive project architecture and framework
- **[TECHNICAL_DIAGRAMS.md](TECHNICAL_DIAGRAMS.md)** - Visual technical diagrams and architecture
- **[FRAMEWORK_QUICK_REFERENCE.md](FRAMEWORK_QUICK_REFERENCE.md)** - Quick reference guide
- **[API_KEYS_SETUP.md](API_KEYS_SETUP.md)** - API keys configuration guide

## Features

- 🤖 **Master Agent**: Intelligent orchestration of research tasks
- ⚡ **7 Worker Agents**: Specialized agents for clinical trials, market data, patents, web search, and more
- 📄 **PDF Reports**: Automatic generation of professional research reports
- 🔄 **Real-time Updates**: Live status polling for research progress
- 🎨 **Modern UI**: Beautiful React interface with Tailwind CSS

## Project Structure

```
├── backend/          # FastAPI backend with AI agents
├── frontend/         # React frontend application
└── SETUP.md         # Detailed setup guide
```

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Requirements

- Python 3.8+
- Node.js 16+
- MongoDB (optional but recommended)
