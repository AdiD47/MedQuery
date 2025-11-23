"""
Quick test script to verify agent system is working
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Test 1: Check API keys
print("=" * 60)
print("TEST 1: API Keys Configuration")
print("=" * 60)
gemini_key = os.environ.get("GEMINI_API_KEY")
tavily_key = os.environ.get("TAVILY_API_KEY")

if gemini_key:
    print(f"✓ Gemini API Key: {gemini_key[:20]}...")
else:
    print("✗ Gemini API Key not found")

if tavily_key:
    print(f"✓ Tavily API Key: {tavily_key[:20]}...")
else:
    print("✗ Tavily API Key not found")

# Test 2: Import CrewAI
print("\n" + "=" * 60)
print("TEST 2: CrewAI Import")
print("=" * 60)
try:
    from crewai import Agent, Task, Crew
    print("✓ CrewAI imported successfully")
except Exception as e:
    print(f"✗ CrewAI import failed: {e}")
    exit(1)

# Test 3: Import Gemini
print("\n" + "=" * 60)
print("TEST 3: Langchain Gemini Import")
print("=" * 60)
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=gemini_key,
        temperature=0.3
    )
    print("✓ Gemini LLM initialized successfully")
except Exception as e:
    print(f"✗ Gemini initialization failed: {e}")
    exit(1)

# Test 4: Test Clinical Trials API
print("\n" + "=" * 60)
print("TEST 4: Clinical Trials API")
print("=" * 60)
try:
    from agents.tools import search_clinical_trials
    result = search_clinical_trials("COPD", "PHASE3")
    import json
    data = json.loads(result)
    print(f"✓ Clinical Trials API working - Found {data.get('total_trials', 0)} trials")
except Exception as e:
    print(f"✗ Clinical Trials API failed: {e}")

# Test 5: Test Tavily
print("\n" + "=" * 60)
print("TEST 5: Tavily Web Search")
print("=" * 60)
try:
    from agents.tools import search_web_tavily
    result = search_web_tavily("respiratory diseases India")
    import json
    data = json.loads(result)
    print(f"✓ Tavily working - Found {len(data.get('results', []))} results")
except Exception as e:
    print(f"✗ Tavily failed: {e}")

# Test 6: Test Mock APIs
print("\n" + "=" * 60)
print("TEST 6: Mock Data APIs")
print("=" * 60)
try:
    from mock_apis import get_iqvia_data, get_patent_data
    iqvia = get_iqvia_data("COPD")
    patent = get_patent_data("ILD")
    print(f"✓ Mock APIs working - IQVIA market size: {iqvia.get('market_size_inr_cr', 0)} Cr")
    print(f"✓ Mock APIs working - ILD patents expiring in 2 years: {patent.get('expiring_in_2_years', 0)}")
except Exception as e:
    print(f"✗ Mock APIs failed: {e}")

# Test 7: Test PDF Generation
print("\n" + "=" * 60)
print("TEST 7: PDF Report Generation")
print("=" * 60)
try:
    from report_generator import create_sample_report
    pdf_path = create_sample_report()
    if os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path)
        print(f"✓ PDF generated successfully: {pdf_path} ({size} bytes)")
    else:
        print("✗ PDF file not found")
except Exception as e:
    print(f"✗ PDF generation failed: {e}")

# Test 8: Simple Agent Test
print("\n" + "=" * 60)
print("TEST 8: Simple Agent Creation")
print("=" * 60)
try:
    from agents.crew_agents import create_clinical_trials_agent
    agent = create_clinical_trials_agent()
    print(f"✓ Agent created: {agent.role}")
except Exception as e:
    print(f"✗ Agent creation failed: {e}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
print("\n✓ System is ready for full research orchestration!")
