
import requests
import time
from typing import List, Dict, Optional
import streamlit as st

# Adzuna API Credentials
ADZUNA_APP_ID = "c575f87d"
ADZUNA_APP_KEY = "20c7b72ed6d5807d2eedc4da9317f509"

def fetch_live_job_feed(location="india", country_code="in", job_role="software engineer"):
    """
    Fetches global and Indian jobs using Adzuna with improved efficiency.
    Country codes: 'in' for India, 'us' for USA, 'gb' for UK, 'de' for Germany, 'ca' for Canada, 'au' for Australia.
    
    Args:
        location: City, state, or general location (e.g., "Chennai", "Mumbai", "Bangalore")
        country_code: Two-letter country code
        job_role: Job title or role to search for
    
    Returns:
        List of job postings with enhanced data
    """
    try:
        # Enhanced URL structure with better parameters
        url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
        
        # Build smart location query - handles both cities and general locations
        location_query = location.strip().lower()
        
        # Major Indian cities for better results
        indian_cities = ['mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai', 'kolkata', 
                        'pune', 'ahmedabad', 'jaipur', 'lucknow', 'noida', 'gurgaon']
        
        # If location is just "india", search across major cities
        if location_query in ['india', 'in', '']:
            # Fetch from multiple major cities and combine
            all_jobs = []
            for city in indian_cities[:5]:  # Top 5 cities to avoid rate limits
                city_jobs = _fetch_single_location(url, city, job_role, country_code)
                all_jobs.extend(city_jobs)
                time.sleep(0.2)  # Rate limit protection
            
            # Remove duplicates based on job ID
            unique_jobs = {job.get('id'): job for job in all_jobs}.values()
            return list(unique_jobs)[:15]  # Return top 15 unique jobs
        
        # Single location search
        return _fetch_single_location(url, location, job_role, country_code)
        
    except Exception as e:
        print(f"Adzuna Error: {e}")
        return []


def _fetch_single_location(url: str, location: str, job_role: str, country_code: str) -> List[Dict]:
    """
    Internal helper to fetch jobs from a single location.
    
    Args:
        url: Adzuna API endpoint
        location: Specific location to search
        job_role: Job title/role
        country_code: Country code
    
    Returns:
        List of job postings
    """
    try:
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": 20,  # Increased from 15 for better results
            "what": job_role,
            "where": location,
            "content-type": "application/json",
            "sort_by": "relevance",  # Get most relevant jobs first
            "max_days_old": 30  # Only jobs from last 30 days
        }
        
        # Add retry logic for better reliability
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    # Enhance job data with additional info
                    enhanced_results = []
                    for job in results:
                        # Clean and validate job data
                        if job.get('title') and job.get('company', {}).get('display_name'):
                            enhanced_job = {
                                **job,
                                'search_location': location,  # Track where it was found
                                'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                            enhanced_results.append(enhanced_job)
                    
                    return enhanced_results
                
                elif response.status_code == 429:  # Rate limit
                    print(f"Rate limited, waiting {retry_delay * 2} seconds...")
                    time.sleep(retry_delay * 2)
                    retry_delay *= 2
                    continue
                
                elif response.status_code == 401:
                    print("⚠️ Adzuna API credentials invalid. Check secrets.toml")
                    return []
                
                else:
                    print(f"Adzuna API returned status {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return []
                    
            except requests.Timeout:
                print(f"Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return []
            
            except requests.RequestException as e:
                print(f"Request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return []
        
        return []
        
    except Exception as e:
        print(f"Single location fetch error: {e}")
        return []


def scrape_job_details(url: str, use_fallback: bool = True) -> Optional[str]:
    """
    Advanced Semantic Scraper with fallback mechanism.
    Uses Jina Reader to bypass JavaScript blocks and anti-bot shields.
    
    Args:
        url: Job posting URL to scrape
        use_fallback: If True, attempts direct scraping if Jina fails
    
    Returns:
        Cleaned job description text or error message
    """
    try:
        # Primary method: Jina Reader (best for dynamic content)
        clean_text = _scrape_with_jina(url)
        
        if clean_text and not clean_text.startswith("Error:"):
            return clean_text
        
        # Fallback method: Direct scraping (for simple pages)
        if use_fallback:
            print("Jina failed, trying direct scrape...")
            fallback_text = _scrape_direct(url)
            if fallback_text and not fallback_text.startswith("Error:"):
                return fallback_text
        
        return clean_text  # Return Jina error if both fail
        
    except Exception as e:
        return f"Error: Scraping failed - {str(e)}"


def _scrape_with_jina(url: str) -> str:
    """
    Internal helper to scrape using Jina Reader API.
    
    Args:
        url: Target URL
    
    Returns:
        Cleaned text content
    """
    try:
        # Jina Reader with enhanced configuration
        jina_url = f"https://r.jina.ai/{url}"
        
        headers = {
            "Accept": "text/plain",
            "User-Agent": "Mozilla/5.0 (compatible; JobScraperBot/1.0)",
            "X-Respond-With": "markdown",  # Request markdown format
            "X-Remove-Selector": "nav,footer,header,.ads,.popup",  # Remove noise
            # Uncomment and add your Jina API key if you have one for better rate limits
            # "Authorization": "Bearer YOUR_JINA_KEY"
        }
        
        # Add retry logic
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.get(jina_url, headers=headers, timeout=25)
                
                if response.status_code == 200:
                    clean_text = response.text.strip()
                    
                    # Validate content quality
                    if len(clean_text) < 100:
                        return "Error: Content too short, possibly blocked"
                    
                    # Return optimized length (8000 chars for better context)
                    return clean_text[:8000]
                
                elif response.status_code == 429:
                    print("Jina rate limit hit, waiting...")
                    time.sleep(3)
                    continue
                
                elif response.status_code == 404:
                    return "Error: Page not found (404)"
                
                else:
                    return f"Error: Jina Reader failed (Status {response.status_code})"
                    
            except requests.Timeout:
                print(f"Jina timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return "Error: Request timeout"
        
        return "Error: Max retries exceeded"
        
    except Exception as e:
        return f"Error: Jina scraping failed - {str(e)}"


def _scrape_direct(url: str) -> str:
    """
    Internal fallback method for direct HTML scraping.
    
    Args:
        url: Target URL
    
    Returns:
        Extracted text content
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            # Basic text extraction (you can enhance this with BeautifulSoup if needed)
            text = response.text
            
            # Simple cleaning
            text = text.replace('<br>', '\n').replace('<br/>', '\n')
            
            # Remove script and style tags content
            import re
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)  # Remove all HTML tags
            
            # Clean whitespace
            text = ' '.join(text.split())
            
            return text[:8000]
        
        return f"Error: Direct scrape failed (Status {response.status_code})"
        
    except Exception as e:
        return f"Error: Direct scraping failed - {str(e)}"


def fetch_jobs_multiple_roles(location: str, country_code: str, roles: List[str]) -> List[Dict]:
    """
    Fetch jobs for multiple roles at once.
    
    Args:
        location: Target location
        country_code: Country code
        roles: List of job roles to search
    
    Returns:
        Combined list of jobs from all roles
    """
    all_jobs = []
    
    for role in roles:
        jobs = fetch_live_job_feed(location, country_code, role)
        all_jobs.extend(jobs)
        time.sleep(0.3)  # Rate limit protection
    
    # Remove duplicates
    unique_jobs = {job.get('id'): job for job in all_jobs}.values()
    return list(unique_jobs)


def validate_adzuna_credentials() -> bool:
    """
    Check if Adzuna API credentials are configured.
    
    Returns:
        True if credentials exist, False otherwise
    """
    return bool(ADZUNA_APP_ID and ADZUNA_APP_KEY)


# Example usage and testing
if __name__ == "__main__":
    print("Testing Adzuna API...")
    
    if not validate_adzuna_credentials():
        print("⚠️ Warning: Adzuna credentials not found in secrets.toml")
    else:
        print("✅ Credentials loaded")
    
    # Test single city
    print("\n--- Testing Chennai jobs ---")
    jobs = fetch_live_job_feed("Chennai", "in", "python developer")
    print(f"Found {len(jobs)} jobs in Chennai")
    
    # Test multiple cities (India-wide)
    print("\n--- Testing India-wide search ---")
    india_jobs = fetch_live_job_feed("india", "in", "software engineer")
    print(f"Found {len(india_jobs)} jobs across India")
    
    # Test job scraping
    if jobs and len(jobs) > 0:
        print("\n--- Testing job detail scraping ---")
        test_url = jobs[0].get('redirect_url', '')
        if test_url:
            details = scrape_job_details(test_url)
            print(f"Scraped {len(details)} characters")
            print(f"Preview: {details[:200]}...")