
import requests
import time
from typing import List, Dict, Optional
import streamlit as st

# Adzuna API Credentials
ADZUNA_APP_ID = "c575f87d"
ADZUNA_APP_KEY = "20c7b72ed6d5807d2eedc4da9317f509"

# Comprehensive Indian city list
INDIAN_CITIES = [
    # Tier 1 Cities (Major Tech Hubs - Priority)
    'bangalore', 'mumbai', 'delhi', 'hyderabad', 'chennai', 'pune', 'kolkata', 'gurgaon', 'noida',
    
    # Tier 2 Cities (Growing Tech Markets)
    'ahmedabad', 'jaipur', 'lucknow', 'kochi', 'indore', 'nagpur', 'visakhapatnam', 'bhopal', 
    'coimbatore', 'chandigarh', 'vadodara', 'thiruvananthapuram',
    
    # Tier 3 Cities (Emerging Markets)
    'kanpur', 'patna', 'ludhiana', 'agartala', 'dehradun', 'dhanbad', 'jamshedpur', 'ranchi', 
    'srinagar', 'varanasi', 'meerut', 'rajkot', 'madurai', 'salem', 'tiruchirappalli', 'gwalior', 
    'jodhpur', 'jabalpur', 'allahabad', 'guntur', 'amritsar', 'nashik', 'faridabad', 'tanjore',
    'tirunelveli', 'thiruvallur', 'durgapur', 'asansol', 'bhubaneswar', 'cuttack', 'mangalore', 
    'mysore', 'thiruvarur', 'tiruppur', 'uluberia', 'bilaspur', 'bhatpara', 'bhilai'
]

# Job roles by domain - CSE roles get priority
JOB_DOMAINS = {
    'cse': [
        'software engineer', 'software developer', 'full stack developer', 'backend developer', 
        'frontend developer', 'python developer', 'java developer', 'devops engineer', 
        'data scientist', 'machine learning engineer', 'ai engineer', 'cloud engineer', 
        'web developer', 'mobile developer', 'react developer', 'nodejs developer'
    ],
    'non_cse': [
        # Engineering & Technical
        'mechanical engineer', 'civil engineer', 'electrical engineer', 'electronics engineer',
        'chemical engineer', 'automobile engineer', 'production engineer', 'quality engineer',
        
        # Business & Management
        'business analyst', 'project manager', 'product manager', 'operations manager',
        'sales manager', 'marketing manager', 'hr manager', 'finance manager',
        
        # Finance & Accounting
        'accountant', 'financial analyst', 'chartered accountant', 'auditor', 'tax consultant',
        
        # Healthcare & Life Sciences
        'nurse', 'pharmacist', 'medical representative', 'lab technician', 'biotechnology',
        
        # Creative & Design
        'graphic designer', 'ui ux designer', 'content writer', 'digital marketer', 'video editor',
        
        # Education & Training
        'teacher', 'trainer', 'lecturer', 'consultant', 'research analyst',
        
        # Customer Service & Support
        'customer support', 'technical support', 'bpo executive', 'call center',
        
        # Others
        'architect', 'interior designer', 'logistics manager', 'supply chain manager'
    ]
}

def fetch_live_job_feed(location="india", country_code="in", job_role="software engineer", 
                        include_all_domains=False, max_results=20):
    """
    Fetches global and Indian jobs using Adzuna with multi-domain support.
    
    Args:
        location: City, state, or general location (e.g., "Chennai", "Mumbai", "Bangalore", "india")
        country_code: Two-letter country code ('in', 'us', 'gb', 'de', 'ca', 'au')
        job_role: Primary job title or role to search for (defaults to software engineer)
        include_all_domains: If True, fetches jobs from all domains (CSE priority), if False only searches given role
        max_results: Maximum number of results to return
    
    Returns:
        List of job postings with enhanced data, CSE roles prioritized
    """
    try:
        url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
        location_query = location.strip().lower()
        
        # Multi-city search for "india" or empty location
        if location_query in ['india', 'in', '']:
            return _fetch_india_wide(url, job_role, country_code, include_all_domains, max_results)
        
        # Single location search
        if include_all_domains:
            return _fetch_all_domains(url, location, country_code, max_results)
        else:
            return _fetch_single_location(url, location, job_role, country_code)
        
    except Exception as e:
        print(f"Adzuna Error: {e}")
        return []


def _fetch_india_wide(url: str, job_role: str, country_code: str, 
                     include_all_domains: bool, max_results: int) -> List[Dict]:
    """
    Fetches jobs from multiple cities across India.
    
    Args:
        url: Adzuna API endpoint
        job_role: Job role to search
        country_code: Country code
        include_all_domains: Whether to search all domains
        max_results: Maximum results
    
    Returns:
        Combined list of jobs from multiple cities
    """
    all_jobs = []
    cities_searched = 0
    max_cities = 15  # Limit to top 15 cities to avoid rate limits
    
    for city in INDIAN_CITIES[:max_cities]:
        try:
            if include_all_domains:
                city_jobs = _fetch_all_domains(url, city, country_code, max_results=5)
            else:
                city_jobs = _fetch_single_location(url, city, job_role, country_code)
            
            all_jobs.extend(city_jobs)
            cities_searched += 1
            
            # Rate limit protection
            time.sleep(0.3)
            
            # Early exit if we have enough jobs
            if len(all_jobs) >= max_results * 2:
                break
                
        except Exception as e:
            print(f"Error fetching jobs from {city}: {e}")
            continue
    
    # Remove duplicates and sort (CSE jobs first)
    unique_jobs = _deduplicate_and_sort(all_jobs, prioritize_cse=True)
    
    print(f"✅ Searched {cities_searched} cities, found {len(unique_jobs)} unique jobs")
    return unique_jobs[:max_results]


def _fetch_all_domains(url: str, location: str, country_code: str, max_results: int = 20) -> List[Dict]:
    """
    Fetches jobs from all domains with CSE priority.
    
    Args:
        url: Adzuna API endpoint
        location: Location to search
        country_code: Country code
        max_results: Maximum results
    
    Returns:
        List of jobs from multiple domains
    """
    all_jobs = []
    
    # First, fetch CSE jobs (Priority)
    cse_jobs_fetched = 0
    for role in JOB_DOMAINS['cse'][:5]:  # Top 5 CSE roles
        jobs = _fetch_single_location(url, location, role, country_code, results_per_page=10)
        all_jobs.extend(jobs)
        cse_jobs_fetched += len(jobs)
        time.sleep(0.25)
        
        if cse_jobs_fetched >= max_results * 0.7:  # 70% CSE jobs
            break
    
    # Then, fetch non-CSE jobs (if space available)
    non_cse_needed = max_results - len(all_jobs)
    if non_cse_needed > 0:
        for role in JOB_DOMAINS['non_cse'][:8]:  # Sample from non-CSE roles
            jobs = _fetch_single_location(url, location, role, country_code, results_per_page=5)
            all_jobs.extend(jobs)
            time.sleep(0.25)
            
            if len(all_jobs) >= max_results * 1.5:
                break
    
    # Deduplicate and return
    unique_jobs = _deduplicate_and_sort(all_jobs, prioritize_cse=True)
    return unique_jobs[:max_results]


def _fetch_single_location(url: str, location: str, job_role: str, country_code: str, 
                          results_per_page: int = 20) -> List[Dict]:
    """
    Internal helper to fetch jobs from a single location for a specific role.
    
    Args:
        url: Adzuna API endpoint
        location: Specific location to search
        job_role: Job title/role
        country_code: Country code
        results_per_page: Number of results per request
    
    Returns:
        List of job postings
    """
    try:
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": results_per_page,
            "what": job_role,
            "where": location,
            "content-type": "application/json",
            "sort_by": "relevance",
            "max_days_old": 30
        }
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    enhanced_results = []
                    for job in results:
                        if job.get('title') and job.get('company', {}).get('display_name'):
                            # Determine job domain
                            job_domain = _classify_job_domain(job.get('title', ''))
                            
                            enhanced_job = {
                                **job,
                                'search_location': location,
                                'search_role': job_role,
                                'job_domain': job_domain,
                                'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                            enhanced_results.append(enhanced_job)
                    
                    return enhanced_results
                
                elif response.status_code == 429:
                    wait_time = retry_delay * 2
                    print(f"Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    retry_delay *= 2
                    continue
                
                elif response.status_code == 401:
                    print("⚠️ Adzuna API credentials invalid")
                    return []
                
                else:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return []
                    
            except requests.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return []
            
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return []
        
        return []
        
    except Exception as e:
        print(f"Single location fetch error: {e}")
        return []


def _classify_job_domain(job_title: str) -> str:
    """
    Classifies a job into CSE or non-CSE domain based on title.
    
    Args:
        job_title: Job title string
    
    Returns:
        'CSE' or 'Non-CSE'
    """
    job_title_lower = job_title.lower()
    
    cse_keywords = [
        'software', 'developer', 'engineer', 'programmer', 'devops', 'data', 'ai', 'ml',
        'cloud', 'full stack', 'backend', 'frontend', 'web', 'mobile', 'app', 'react',
        'python', 'java', 'javascript', 'node', 'api', 'database', 'tech', 'it'
    ]
    
    for keyword in cse_keywords:
        if keyword in job_title_lower:
            return 'CSE'
    
    return 'Non-CSE'


def _deduplicate_and_sort(jobs: List[Dict], prioritize_cse: bool = True) -> List[Dict]:
    """
    Removes duplicate jobs and sorts them (CSE jobs first if prioritized).
    
    Args:
        jobs: List of job dictionaries
        prioritize_cse: Whether to put CSE jobs first
    
    Returns:
        Deduplicated and sorted job list
    """
    # Remove duplicates based on job ID
    unique_jobs_dict = {job.get('id'): job for job in jobs if job.get('id')}
    unique_jobs = list(unique_jobs_dict.values())
    
    if prioritize_cse:
        # Sort: CSE jobs first, then by date
        unique_jobs.sort(key=lambda x: (
            0 if x.get('job_domain') == 'CSE' else 1,  # CSE first
            x.get('created', '')  # Then by date
        ), reverse=True)
    
    return unique_jobs


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
        clean_text = _scrape_with_jina(url)
        
        if clean_text and not clean_text.startswith("Error:"):
            return clean_text
        
        if use_fallback:
            print("Jina failed, trying direct scrape...")
            fallback_text = _scrape_direct(url)
            if fallback_text and not fallback_text.startswith("Error:"):
                return fallback_text
        
        return clean_text
        
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
        jina_url = f"https://r.jina.ai/{url}"
        
        headers = {
            "Accept": "text/plain",
            "User-Agent": "Mozilla/5.0 (compatible; JobScraperBot/1.0)",
            "X-Respond-With": "markdown",
            "X-Remove-Selector": "nav,footer,header,.ads,.popup",
        }
        
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.get(jina_url, headers=headers, timeout=25)
                
                if response.status_code == 200:
                    clean_text = response.text.strip()
                    
                    if len(clean_text) < 100:
                        return "Error: Content too short, possibly blocked"
                    
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
            text = response.text
            text = text.replace('<br>', '\n').replace('<br/>', '\n')
            
            import re
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
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
        time.sleep(0.3)
    
    unique_jobs = _deduplicate_and_sort(all_jobs, prioritize_cse=True)
    return unique_jobs


def validate_adzuna_credentials() -> bool:
    """
    Check if Adzuna API credentials are configured.
    
    Returns:
        True if credentials exist, False otherwise
    """
    return bool(ADZUNA_APP_ID and ADZUNA_APP_KEY)


def get_job_statistics(jobs: List[Dict]) -> Dict:
    """
    Get statistics about fetched jobs.
    
    Args:
        jobs: List of job dictionaries
    
    Returns:
        Dictionary with job statistics
    """
    if not jobs:
        return {"total": 0, "cse": 0, "non_cse": 0, "cities": []}
    
    cse_count = sum(1 for job in jobs if job.get('job_domain') == 'CSE')
    non_cse_count = len(jobs) - cse_count
    cities = list(set(job.get('search_location', 'Unknown') for job in jobs))
    
    return {
        "total": len(jobs),
        "cse": cse_count,
        "non_cse": non_cse_count,
        "cities": cities,
        "cse_percentage": round((cse_count / len(jobs)) * 100, 1) if jobs else 0
    }


# Example usage and testing
if __name__ == "__main__":
    print("🚀 Testing Enhanced Multi-Domain Job Scraper")
    print("=" * 50)
    
    if not validate_adzuna_credentials():
        print("⚠️ Warning: Adzuna credentials not found")
    else:
        print("✅ Credentials loaded\n")
    
    # Test 1: Single city, single role (CSE)
    print("--- Test 1: Chennai - Software Engineer ---")
    jobs = fetch_live_job_feed("Chennai", "in", "software engineer")
    stats = get_job_statistics(jobs)
    print(f"Found {stats['total']} jobs (CSE: {stats['cse']}, Non-CSE: {stats['non_cse']})")
    
    # Test 2: Single city, all domains
    print("\n--- Test 2: Mumbai - All Domains ---")
    jobs = fetch_live_job_feed("Mumbai", "in", include_all_domains=True, max_results=20)
    stats = get_job_statistics(jobs)
    print(f"Found {stats['total']} jobs (CSE: {stats['cse']}, Non-CSE: {stats['non_cse']})")
    print(f"CSE Priority: {stats['cse_percentage']}%")
    
    # Test 3: India-wide search
    print("\n--- Test 3: India-wide - All Domains ---")
    jobs = fetch_live_job_feed("india", "in", include_all_domains=True, max_results=25)
    stats = get_job_statistics(jobs)
    print(f"Found {stats['total']} jobs across {len(stats['cities'])} cities")
    print(f"Cities: {', '.join(stats['cities'][:5])}...")
    print(f"CSE: {stats['cse']}, Non-CSE: {stats['non_cse']}")
    
    # Test 4: Job scraping
    if jobs and len(jobs) > 0:
        print("\n--- Test 4: Job Detail Scraping ---")
        test_url = jobs[0].get('redirect_url', '')
        if test_url:
            details = scrape_job_details(test_url)
            print(f"Scraped {len(details)} characters")
            print(f"Preview: {details[:150]}...")
    
    print("\n✅ All tests completed!")

