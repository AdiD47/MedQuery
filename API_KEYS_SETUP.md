# API Keys Setup Guide

## Where to Put API Keys

Create a file named **`.env`** in the **`backend`** directory.

### Location
```
Techathon-main/
└── backend/
    └── .env    ← Create this file here
```

## Step-by-Step Instructions

### 1. Create the `.env` file

**Windows:**
```bash
cd backend
notepad .env
```

**macOS/Linux:**
```bash
cd backend
nano .env
# or
vim .env
```

### 2. Copy this template into the file:

```env
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=techathon_db

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# API KEYS - REPLACE WITH YOUR ACTUAL KEYS
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Replace the placeholder values with your actual API keys

**Example:**
```env
GEMINI_API_KEY=AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567
TAVILY_API_KEY=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
```

## How to Get API Keys

### Gemini API Key (Google AI)

1. Go to: https://aistudio.google.com/app/apikey
   - Or: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (it starts with `AIza...`)
5. Paste it in your `.env` file

**Note:** The Gemini API has a free tier with generous limits.

### Tavily API Key (Web Search)

1. Go to: https://tavily.com/
2. Click "Sign Up" or "Get Started"
3. Create a free account
4. Navigate to your dashboard/API keys section
5. Copy your API key (it starts with `tvly-...`)
6. Paste it in your `.env` file

**Note:** Tavily offers a free tier for development.

## Important Notes

1. **Never commit `.env` to Git** - It's already in `.gitignore`
2. **Keep your keys secret** - Don't share them publicly
3. **The app will work without keys** - But AI features won't be available
4. **No quotes needed** - Just paste the key directly:
   ```env
   GEMINI_API_KEY=AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567
   ```
   NOT:
   ```env
   GEMINI_API_KEY="AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567"  ❌
   ```

## Verify Your Setup

After creating the `.env` file, you can test if the keys are loaded correctly:

```bash
cd backend
python test_agents.py
```

This will show you if your API keys are detected.

## Troubleshooting

### Keys not working?
- Make sure there are **no spaces** around the `=` sign
- Make sure there are **no quotes** around the key value
- Restart the backend server after adding keys
- Check for typos in the key names (case-sensitive)

### File not found?
- Make sure the `.env` file is in the `backend` directory
- Make sure it's named exactly `.env` (not `.env.txt` or `env`)
- On Windows, if you can't create a file starting with `.`, create it as `env` and rename it to `.env`

### Still having issues?
- Check the backend terminal for error messages
- Verify the keys are correct by testing them on the provider's website
- Make sure you've activated your virtual environment if using one

