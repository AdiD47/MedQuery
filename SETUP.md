# Project Setup and Running Instructions

This guide will help you set up and run the Techathon project, which consists of a FastAPI backend and a React frontend.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (for backend)
- **Node.js 16+** and **npm** or **yarn** (for frontend)
- **MongoDB** (optional, but recommended for full functionality)
- **Git** (to clone the repository)

## Step 1: Backend Setup

### 1.1 Navigate to Backend Directory
```bash
cd backend
```

### 1.2 Create a Virtual Environment (Recommended)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 1.3 Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 1.4 Create Environment File
Create a `.env` file in the `backend` directory with the following variables:

```env
# MongoDB Configuration (optional - defaults to localhost:27017)
MONGO_URL=mongodb://localhost:27017
DB_NAME=techathon_db

# CORS Configuration (optional - defaults to *)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# API Keys (optional - for full functionality)
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

**Note:** The project will work without these API keys, but some features (like AI agents) may not be available.

### 1.5 Start the Backend Server
```bash
# Using uvicorn directly
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Or if uvicorn is not in PATH
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: `http://localhost:8000`
API documentation will be at: `http://localhost:8000/docs`

## Step 2: Frontend Setup

### 2.1 Navigate to Frontend Directory
Open a new terminal window and navigate to:
```bash
cd frontend
```

### 2.2 Install Dependencies
```bash
# Using npm
npm install

# Or using yarn (recommended based on package.json)
yarn install
```

### 2.3 Create Environment File (Optional)
Create a `.env` file in the `frontend` directory:

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

**Note:** If you don't create this file, the frontend will default to `http://localhost:8000`.

### 2.4 Start the Frontend Development Server
```bash
# Using npm
npm start

# Or using yarn
yarn start
```

The frontend will be available at: `http://localhost:3000`

## Step 3: MongoDB Setup (Optional but Recommended)

### Option A: Local MongoDB Installation
1. Download and install MongoDB from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Start MongoDB service:
   ```bash
   # Windows
   net start MongoDB
   
   # macOS (if installed via Homebrew)
   brew services start mongodb-community
   
   # Linux
   sudo systemctl start mongod
   ```

### Option B: MongoDB Atlas (Cloud)
1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster and get your connection string
3. Update `MONGO_URL` in `backend/.env` with your Atlas connection string

### Option C: Docker
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## Running the Complete Application

### Terminal 1: Backend
```bash
cd backend
# Activate virtual environment if using one
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Frontend
```bash
cd frontend
npm start
# or
yarn start
```

### Terminal 3: MongoDB (if running locally)
```bash
# Start MongoDB service (see MongoDB setup above)
```

## Verification

1. **Backend Health Check:**
   - Open browser: `http://localhost:8000/api/`
   - Should see: `{"message": "Hello World"}`

2. **Frontend:**
   - Open browser: `http://localhost:3000`
   - Should see the Master Agent Intelligence interface

3. **API Documentation:**
   - Open browser: `http://localhost:8000/docs`
   - Should see Swagger UI with all available endpoints

## Troubleshooting

### Backend Issues

**Port Already in Use:**
```bash
# Change port in uvicorn command
uvicorn server:app --reload --port 8001
```

**MongoDB Connection Failed:**
- The app will still run but database features won't work
- Check MongoDB is running: `mongosh` or `mongo`
- Verify `MONGO_URL` in `.env` file

**Module Import Errors:**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend Issues

**Port Already in Use:**
- React will prompt to use a different port (usually 3001)
- Or set `PORT=3001` in `.env` file

**Backend Connection Failed:**
- Verify backend is running on port 8000
- Check `REACT_APP_BACKEND_URL` in `frontend/.env`
- Check CORS settings in `backend/server.py`

**Dependencies Installation Failed:**
- Clear cache: `npm cache clean --force` or `yarn cache clean`
- Delete `node_modules` and reinstall
- Try using `yarn` instead of `npm` or vice versa

## Project Structure

```
Techathon-main/
├── backend/
│   ├── agents/          # AI agent definitions
│   ├── server.py        # FastAPI application
│   ├── requirements.txt # Python dependencies
│   └── .env            # Environment variables (create this)
├── frontend/
│   ├── src/            # React source code
│   ├── package.json    # Node dependencies
│   └── .env           # Environment variables (create this)
└── README.md
```

## Features

- **Master Agent Intelligence:** AI-powered pharmaceutical research orchestration
- **Multi-Agent System:** 7 specialized worker agents for different research tasks
- **PDF Report Generation:** Automatic generation of research reports
- **Real-time Status Updates:** Polling for research status
- **Mock APIs:** Pre-configured mock data for testing

## Next Steps

1. Configure API keys in `backend/.env` for full AI functionality
2. Set up MongoDB for persistent data storage
3. Customize agent behavior in `backend/agents/crew_agents.py`
4. Modify frontend UI in `frontend/src/components/ChatInterface.jsx`

## Support

For issues or questions, check:
- Backend logs in terminal running uvicorn
- Frontend console in browser DevTools
- API documentation at `http://localhost:8000/docs`

