import requests

ADZUNA_APP_ID = "c575f87d"
ADZUNA_APP_KEY = "20c7b72ed6d5807d2eedc4da9317f509"

def fetch_live_job_feed(location="india", country_code="in"):
    """
    Fetches global and Indian jobs using Adzuna.
    Country codes: 'in' for India, 'us' for USA, 'gb' for UK.
    """
    try:
        # Adzuna URL structure: /jobs/[country]/search/[page]
        url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
        
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": 15,
            "what": "software engineer", # You can make this a variable later
            "where": location,
            "content-type": "application/json"
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json().get('results', [])
            return data
        return []
    except Exception as e:
        print(f"Adzuna Error: {e}")
        return []
    
def scrape_job_details(url):
    """
    Advanced Semantic Scraper.
    Uses Jina Reader to bypass JavaScript blocks and anti-bot shields.
    """
    try:
        # We prefix the URL to use Jina's high-performance reader
        jina_url = f"https://r.jina.ai/{url}"
        
        headers = {
            "Accept": "text/plain",
            # Optional: Add a Jina API key here if you find you are being rate-limited
            # "Authorization": "Bearer YOUR_JINA_KEY" 
        }
        
        response = requests.get(jina_url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            # Jina returns clean, LLM-friendly Markdown text
            clean_text = response.text
            return clean_text[:6000]  # Return the most relevant 6000 characters
        else:
            return f"Error: Browser simulation failed (Status {response.status_code})"
            
    except Exception as e:
        return f"Error: {str(e)}"
    
    