# Mock API endpoints for IQVIA, EXIM, and USPTO data

MOCK_IQVIA_DATA = {
    "COPD": {
        "disease": "Chronic Obstructive Pulmonary Disease (COPD)",
        "market_size_inr_cr": 2500,
        "growth_rate": 8.5,
        "top_competitors": ["GSK", "AstraZeneca", "Boehringer Ingelheim"],
        "market_share": {
            "GSK": 35,
            "AstraZeneca": 28,
            "Boehringer Ingelheim": 22,
            "Others": 15
        }
    },
    "Asthma": {
        "disease": "Asthma",
        "market_size_inr_cr": 3200,
        "growth_rate": 9.2,
        "top_competitors": ["GSK", "Cipla", "AstraZeneca", "Novartis"],
        "market_share": {
            "GSK": 30,
            "Cipla": 25,
            "AstraZeneca": 20,
            "Novartis": 15,
            "Others": 10
        }
    },
    "ILD": {
        "disease": "Interstitial Lung Disease (ILD)",
        "market_size_inr_cr": 850,
        "growth_rate": 12.3,
        "top_competitors": ["Roche", "Boehringer Ingelheim"],
        "market_share": {
            "Roche": 45,
            "Boehringer Ingelheim": 40,
            "Others": 15
        }
    },
    "Tuberculosis": {
        "disease": "Tuberculosis (TB)",
        "market_size_inr_cr": 1800,
        "growth_rate": 5.5,
        "top_competitors": ["Government Programs", "Lupin", "Macleods"],
        "market_share": {
            "Government Programs": 60,
            "Lupin": 15,
            "Macleods": 12,
            "Others": 13
        }
    },
    "Pneumonia": {
        "disease": "Pneumonia",
        "market_size_inr_cr": 2100,
        "growth_rate": 6.8,
        "top_competitors": ["Pfizer", "GSK", "Cipla"],
        "market_share": {
            "Pfizer": 32,
            "GSK": 28,
            "Cipla": 22,
            "Others": 18
        }
    }
}

MOCK_EXIM_DATA = {
    "COPD": {
        "disease": "COPD",
        "imports_usd_million": 145,
        "exports_usd_million": 32,
        "net_trade": -113,
        "import_growth": 8.2,
        "major_import_countries": ["USA", "Germany", "UK"]
    },
    "Asthma": {
        "disease": "Asthma",
        "imports_usd_million": 178,
        "exports_usd_million": 45,
        "net_trade": -133,
        "import_growth": 9.5,
        "major_import_countries": ["USA", "Switzerland", "Germany"]
    },
    "ILD": {
        "disease": "ILD",
        "imports_usd_million": 68,
        "exports_usd_million": 8,
        "net_trade": -60,
        "import_growth": 15.2,
        "major_import_countries": ["USA", "Germany", "Switzerland"]
    },
    "Tuberculosis": {
        "disease": "Tuberculosis",
        "imports_usd_million": 42,
        "exports_usd_million": 125,
        "net_trade": 83,
        "import_growth": 2.1,
        "major_import_countries": ["USA", "South Africa"]
    },
    "Pneumonia": {
        "disease": "Pneumonia",
        "imports_usd_million": 95,
        "exports_usd_million": 52,
        "net_trade": -43,
        "import_growth": 5.8,
        "major_import_countries": ["USA", "UK", "Belgium"]
    }
}

MOCK_PATENT_DATA = {
    "COPD": {
        "disease": "COPD",
        "active_patents": 145,
        "expiring_soon": 32,
        "expiring_in_2_years": 18,
        "recent_filings": 25,
        "key_patent_holders": ["GSK", "AstraZeneca", "Boehringer"],
        "generic_opportunity": "Medium - Some patents expiring 2025-2027"
    },
    "Asthma": {
        "disease": "Asthma",
        "active_patents": 198,
        "expiring_soon": 15,
        "expiring_in_2_years": 12,
        "recent_filings": 42,
        "key_patent_holders": ["GSK", "Novartis", "AstraZeneca"],
        "generic_opportunity": "Low - Strong patent protection until 2028"
    },
    "ILD": {
        "disease": "ILD",
        "active_patents": 78,
        "expiring_soon": 12,
        "expiring_in_2_years": 25,
        "recent_filings": 18,
        "key_patent_holders": ["Roche", "Boehringer"],
        "generic_opportunity": "High - Major patents expiring 2025-2026"
    },
    "Tuberculosis": {
        "disease": "Tuberculosis",
        "active_patents": 65,
        "expiring_soon": 28,
        "expiring_in_2_years": 15,
        "recent_filings": 8,
        "key_patent_holders": ["Otsuka", "Johnson & Johnson"],
        "generic_opportunity": "High - Many patents expired or expiring"
    },
    "Pneumonia": {
        "disease": "Pneumonia",
        "active_patents": 112,
        "expiring_soon": 22,
        "expiring_in_2_years": 18,
        "recent_filings": 15,
        "key_patent_holders": ["Pfizer", "GSK", "Merck"],
        "generic_opportunity": "Medium - Mixed patent landscape"
    }
}

def get_iqvia_data(disease_name: str):
    """Get IQVIA market data for a disease"""
    return MOCK_IQVIA_DATA.get(disease_name, {
        "disease": disease_name,
        "market_size_inr_cr": 0,
        "growth_rate": 0,
        "top_competitors": [],
        "market_share": {},
        "note": "No data available"
    })

def get_exim_data(disease_name: str):
    """Get EXIM (Export-Import) data for a disease"""
    return MOCK_EXIM_DATA.get(disease_name, {
        "disease": disease_name,
        "imports_usd_million": 0,
        "exports_usd_million": 0,
        "net_trade": 0,
        "import_growth": 0,
        "major_import_countries": [],
        "note": "No data available"
    })

def get_patent_data(disease_name: str):
    """Get patent landscape data for a disease"""
    return MOCK_PATENT_DATA.get(disease_name, {
        "disease": disease_name,
        "active_patents": 0,
        "expiring_soon": 0,
        "expiring_in_2_years": 0,
        "recent_filings": 0,
        "key_patent_holders": [],
        "generic_opportunity": "Unknown",
        "note": "No data available"
    })
