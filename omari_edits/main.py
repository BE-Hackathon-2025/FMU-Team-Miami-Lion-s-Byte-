# from flask import Flask
# app = Flask(__name__)
# @app.route('/')
# def home():
#     return "Sup, Berry!"

from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import re
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
from queue import Queue
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize web scraping components to pick up the healthcare provider data based on location
ua = UserAgent()
chrome_options = Options()
chrome_options.add_argument('--headless')  # Run in headless mode
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Cache for scraped data
scraped_cache = {
    'healthcare': {},
    'insurance': {},
    'last_update': None
}

# Live scraping progress tracking
scraping_progress = {
    'healthcare': {},
    'insurance': {}
}

# Cache expiration time (2 hours)
CACHE_EXPIRATION = 7200  # seconds

# Store location data in memory (replace with database in production)
user_locations = {}

# Store reviews in memory (replace with database in production)
reviews_db = {
    'healthcare': [],
    'insurance': []
}

# Torch/transformers integration removed — using rule-based fallback for symptom analysis
symptom_model = None

# Load medical knowledge base
try:
    with open('medical_data.json', 'r') as f:
        medical_db = json.load(f)
except FileNotFoundError:
    # Fallback dummy data if file doesn't exist
    medical_db = {
        "clinics": [
            {
                "name": "HealthCare Plus",
                "location": "Miami",
                "specialties": ["General Practice", "Pediatrics"],
                "address": "123 Health Ave, Miami, FL",
                "insurance": ["Aetna", "Blue Cross", "Cigna"],
                "phone": "305-555-1234",
                "url": "https://healthcareplusmiami.com"
            }
            # Add more clinics here
        ],
        "insurance_providers": [
            {
                "name": "Florida Health Insurance",
                "coverage_types": ["Individual", "Family", "Medicare"],
                "contact": "1-800-555-0123",
                "phone": "1-800-555-0123",
                "url": "https://floridahealthinsurance.com"
            }
            # Add more providers here
        ],
        "symptoms_database": {
            # Respiratory symptoms
            "cough": ["Common Cold", "Flu", "COVID-19", "Bronchitis", "Pneumonia", "Asthma"],
            "shortness": ["Asthma", "Pneumonia", "Heart Disease", "COVID-19", "Anxiety"],
            "breath": ["Asthma", "Pneumonia", "Heart Disease", "COVID-19", "Anxiety"],
            "breathing": ["Asthma", "Pneumonia", "Heart Disease", "COVID-19", "Anxiety"],
            "wheezing": ["Asthma", "Bronchitis", "Allergies"],
            "congestion": ["Common Cold", "Sinusitis", "Allergies", "Flu"],
            "sore throat": ["Strep Throat", "Common Cold", "Flu", "Tonsillitis"],
            "throat": ["Strep Throat", "Common Cold", "Flu", "Tonsillitis"],
            
            # Pain symptoms
            "headache": ["Migraine", "Tension Headache", "Sinusitis", "Hypertension", "Stress"],
            "chest pain": ["Heart Attack", "Angina", "Anxiety", "Costochondritis", "Pneumonia"],
            "chest": ["Heart Attack", "Angina", "Anxiety", "Costochondritis", "Pneumonia"],
            "abdominal": ["Gastroenteritis", "Appendicitis", "Food Poisoning", "IBS"],
            "stomach": ["Gastroenteritis", "Ulcer", "Food Poisoning", "IBS", "Gastritis"],
            "back": ["Muscle Strain", "Herniated Disc", "Kidney Stones", "Arthritis"],
            "joint": ["Arthritis", "Gout", "Lupus", "Injury"],
            
            # Fever and infection
            "fever": ["Flu", "COVID-19", "Common Cold", "Pneumonia", "Infection"],
            "chills": ["Flu", "COVID-19", "Infection", "Pneumonia"],
            "sweating": ["Flu", "Infection", "Menopause", "Hypoglycemia"],
            "fatigue": ["Anemia", "Depression", "Chronic Fatigue Syndrome", "Diabetes", "Hypothyroidism"],
            "tired": ["Anemia", "Depression", "Chronic Fatigue Syndrome", "Diabetes", "Hypothyroidism"],
            
            # Digestive symptoms
            "nausea": ["Gastroenteritis", "Food Poisoning", "Pregnancy", "Migraine", "Anxiety"],
            "vomiting": ["Gastroenteritis", "Food Poisoning", "Migraine", "Appendicitis"],
            "diarrhea": ["Gastroenteritis", "Food Poisoning", "IBS", "Crohn's Disease"],
            "constipation": ["IBS", "Hypothyroidism", "Dehydration"],
            
            # Neurological
            "dizziness": ["Vertigo", "Low Blood Pressure", "Dehydration", "Anemia", "Inner Ear Infection"],
            "dizzy": ["Vertigo", "Low Blood Pressure", "Dehydration", "Anemia", "Inner Ear Infection"],
            "confusion": ["Dehydration", "Hypoglycemia", "Stroke", "Dementia", "Infection"],
            "numbness": ["Neuropathy", "Stroke", "Multiple Sclerosis", "Pinched Nerve"],
            "tingling": ["Neuropathy", "Pinched Nerve", "Multiple Sclerosis", "Anxiety"],
            
            # Skin
            "rash": ["Allergies", "Eczema", "Psoriasis", "Dermatitis", "Infection"],
            "itching": ["Allergies", "Eczema", "Dry Skin", "Infection"],
            "swelling": ["Allergies", "Injury", "Heart Disease", "Kidney Disease", "Infection"],
            
            # Mental health
            "anxiety": ["Anxiety Disorder", "Panic Disorder", "Depression", "PTSD"],
            "depression": ["Major Depression", "Bipolar Disorder", "Anxiety"],
            "stress": ["Anxiety Disorder", "Depression", "Burnout"],
            "sleep": ["Insomnia", "Sleep Apnea", "Anxiety", "Depression"],
            "insomnia": ["Insomnia", "Anxiety", "Depression", "Stress"]
        },
        "symptom_synonyms": {
            # Breathing
            "cant breathe": "shortness breath",
            "hard to breathe": "shortness breath",
            "difficulty breathing": "shortness breath",
            "trouble breathing": "shortness breath",
            
            # Pain
            "hurts": "pain",
            "ache": "pain",
            "painful": "pain",
            "sore": "pain",
            
            # Digestive
            "upset stomach": "nausea",
            "throwing up": "vomiting",
            "throw up": "vomiting",
            "loose stool": "diarrhea",
            
            # General
            "weak": "fatigue",
            "exhausted": "fatigue",
            "lightheaded": "dizziness",
            "hot": "fever",
            "temperature": "fever"
        },
        "specialty_keywords": {
            "heart": "Cardiology",
            "cardiac": "Cardiology",
            "chest pain": "Cardiology",
            "skin": "Dermatology",
            "rash": "Dermatology",
            "acne": "Dermatology",
            "child": "Pediatrics",
            "children": "Pediatrics",
            "baby": "Pediatrics",
            "kid": "Pediatrics",
            "mental": "Psychiatry",
            "depression": "Psychiatry",
            "anxiety": "Psychiatry",
            "bone": "Orthopedics",
            "joint": "Orthopedics",
            "fracture": "Orthopedics",
            "eye": "Ophthalmology",
            "vision": "Ophthalmology",
            "dental": "Dentistry",
            "tooth": "Dentistry",
            "teeth": "Dentistry",
            "pregnancy": "OB-GYN",
            "pregnant": "OB-GYN",
            "gynecology": "OB-GYN"
        }
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Unified search across clinics, insurance, and symptoms.
    Enhanced with intelligent query classification and better matching.
    """
    query = request.json.get('query', '')
    search_type = request.json.get('type', 'all')
    location = request.json.get('location', None)

    results = {
        'clinics': [],
        'insurance': [],
        'medical_advice': None,
        'error': None
    }

    try:
        # Detect query intent if type is 'all'
        if search_type == 'all':
            intent = detect_query_intent(query)
            logger.info(f"Detected query intent: {intent} for query: '{query}'")
            
            if intent == 'symptom':
                results['medical_advice'] = analyze_symptoms(query)
                results['clinics'] = search_clinics_by_specialty(query, location)
            elif intent == 'insurance':
                results['insurance'] = search_insurance(query, location)
            elif intent == 'clinic':
                results['clinics'] = search_clinics(query, location)
            else:
                # Mixed or unclear - search everything
                results['clinics'] = search_clinics(query, location)
                results['insurance'] = search_insurance(query, location)
                symptoms_result = analyze_symptoms(query)
                if symptoms_result['possible_conditions']:
                    results['medical_advice'] = symptoms_result
        else:
            # Explicit type specified
            if search_type in ['all', 'clinics']:
                results['clinics'] = search_clinics(query, location)

            if search_type in ['all', 'insurance']:
                results['insurance'] = search_insurance(query, location)

            if search_type in ['all', 'symptoms']:
                results['medical_advice'] = analyze_symptoms(query)
        
        # Rank and limit results
        results['clinics'] = rank_clinic_results(results['clinics'])[:10]
        results['insurance'] = results['insurance'][:10]

        return jsonify(results)
    except Exception as e:
        logger.error(f"Search failure: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

def scrape_healthcare_providers(location, live_update=False):
    """Scrape healthcare provider data from multiple sources"""
    providers = []
    driver = None
    
    # Initialize progress tracking for live updates
    if live_update:
        scraping_progress['healthcare'][location] = {
            'status': 'scraping',
            'providers': [],
            'progress': 0,
            'total': 15
        }
    
    try:
        logger.info(f"Starting healthcare provider scraping for {location}")
        
        # Initialize the webdriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Scrape from Google Maps - Updated selectors
        search_query = f"hospitals+clinics+doctors+{location.replace(' ', '+')}"
        maps_url = f"https://www.google.com/maps/search/{search_query}"
        driver.get(maps_url)
        
        # Wait for results to load
        time.sleep(5)
        
        try:
            # Scroll to load more results
            scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            for _ in range(3):
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Could not scroll results: {str(e)}")
        
        # Extract provider information using updated selectors
        result_items = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
        
        logger.info(f"Found {len(result_items)} potential providers")
        
        if live_update and location in scraping_progress['healthcare']:
            scraping_progress['healthcare'][location]['total'] = min(len(result_items), 15)
        
        for idx, item in enumerate(result_items[:15]):  # Limit to first 15 results
            try:
                # Click on the item to get details
                item.click()
                time.sleep(2)
                
                # Extract name
                try:
                    name = driver.find_element(By.CSS_SELECTOR, 'h1.DUwDvf').text
                except:
                    name = f"Healthcare Provider {idx + 1}"
                
                # Extract address
                try:
                    address = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]').text
                except:
                    address = f"{location}, FL"
                
                # Extract phone
                try:
                    phone_element = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id^="phone"]')
                    phone = phone_element.get_attribute('aria-label').replace('Phone: ', '')
                except:
                    phone = "(305) 555-" + str(1000 + idx).zfill(4)
                
                # Extract website
                try:
                    website_element = driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
                    website = website_element.get_attribute('href')
                except:
                    website = f"https://healthcare-{idx}.com"
                
                # Extract rating if available
                try:
                    rating_text = driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-hidden="true"]').text
                    rating = float(rating_text.split()[0])
                except:
                    rating = None
                
                # Calculate a mock distance (you can enhance this with real geocoding)
                import random
                distance = round(random.uniform(0.5, 25.0), 1)
                
                provider_data = {
                    "name": name,
                    "location": location,
                    "address": address,
                    "phone": phone,
                    "website": website,
                    "rating": rating,
                    "distance": distance,
                    "source": "Google Maps"
                }
                
                providers.append(provider_data)
                
                # Live update: add provider to progress tracking
                if live_update and location in scraping_progress['healthcare']:
                    scraping_progress['healthcare'][location]['providers'].append(provider_data)
                    scraping_progress['healthcare'][location]['progress'] = idx + 1
                
                logger.info(f"Successfully scraped provider: {name}")
                
            except Exception as e:
                logger.error(f"Error extracting provider #{idx} data: {str(e)}")
                continue
        
        logger.info(f"Successfully scraped {len(providers)} healthcare providers")
        
        # Mark scraping as complete
        if live_update and location in scraping_progress['healthcare']:
            scraping_progress['healthcare'][location]['status'] = 'complete'
        
    except Exception as e:
        logger.error(f"Error in healthcare provider scraping: {str(e)}")
        # Return fallback data
        providers = generate_fallback_healthcare_providers(location)
        
        # Mark scraping as failed
        if live_update and location in scraping_progress['healthcare']:
            scraping_progress['healthcare'][location]['status'] = 'failed'
            scraping_progress['healthcare'][location]['providers'] = providers
    
    finally:
        if driver:
            driver.quit()
    
    return providers

def scrape_insurance_providers(location, live_update=False):
    """Scrape insurance provider data from multiple sources"""
    providers = []
    driver = None
    
    # Initialize progress tracking for live updates
    if live_update:
        scraping_progress['insurance'][location] = {
            'status': 'scraping',
            'providers': [],
            'progress': 0,
            'total': 15
        }
    
    try:
        logger.info(f"Starting insurance provider scraping for {location}")
        
        # Initialize the webdriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Search for insurance providers
        search_query = f"health+insurance+providers+{location.replace(' ', '+')}"
        search_url = f"https://www.google.com/search?q={search_query}"
        driver.get(search_url)
        time.sleep(3)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find search results
        search_results = soup.find_all('div', class_='g')
        
        logger.info(f"Found {len(search_results)} insurance search results")
        
        # List of major insurance providers to look for
        major_insurers = [
            "Aetna", "Blue Cross Blue Shield", "Cigna", "UnitedHealthcare", 
            "Humana", "Kaiser Permanente", "Anthem", "Centene", "Molina Healthcare",
            "WellCare", "Florida Blue", "Ambetter", "Oscar Health", "Bright Health"
        ]
        
        if live_update and location in scraping_progress['insurance']:
            scraping_progress['insurance'][location]['total'] = min(len(search_results), 15)
        
        for idx, result in enumerate(search_results[:15]):
            try:
                # Extract name
                title_elem = result.find('h3')
                if not title_elem:
                    continue
                    
                name = title_elem.get_text()
                
                # Check if it's a real insurance provider
                is_insurance = any(insurer.lower() in name.lower() for insurer in major_insurers)
                if not is_insurance and idx < len(major_insurers):
                    name = major_insurers[idx]
                
                # Extract link
                link_elem = result.find('a')
                url = link_elem.get('href', '#') if link_elem else '#'
                
                # Extract description/snippet
                snippet_elem = result.find('div', class_='VwiC3b')
                description = snippet_elem.get_text() if snippet_elem else "Health insurance provider"
                
                # Generate phone number (in production, scrape from provider websites)
                phone = f"1-800-{str(100 + idx).zfill(3)}-{str(1000 + idx).zfill(4)}"
                
                provider_data = {
                    "name": name,
                    "url": url,
                    "phone": phone,
                    "address": f"{location}, FL",
                    "location": location,
                    "description": description[:100],
                    "website": url,
                    "source": "Web Search"
                }
                
                providers.append(provider_data)
                
                # Live update: add provider to progress tracking
                if live_update and location in scraping_progress['insurance']:
                    scraping_progress['insurance'][location]['providers'].append(provider_data)
                    scraping_progress['insurance'][location]['progress'] = idx + 1
                
                logger.info(f"Successfully scraped insurance provider: {name}")
                
            except Exception as e:
                logger.error(f"Error extracting insurance provider #{idx}: {str(e)}")
                continue
        
        # If we didn't get enough results, add major insurers
        if len(providers) < 10:
            for idx, insurer in enumerate(major_insurers[:10]):
                if not any(p['name'] == insurer for p in providers):
                    provider_data = {
                        "name": insurer,
                        "url": f"https://www.{insurer.lower().replace(' ', '')}.com",
                        "phone": f"1-800-{str(200 + idx).zfill(3)}-{str(2000 + idx).zfill(4)}",
                        "address": f"{location}, FL",
                        "location": location,
                        "description": "Major health insurance provider",
                        "website": f"https://www.{insurer.lower().replace(' ', '')}.com",
                        "source": "Database"
                    }
                    providers.append(provider_data)
                    
                    # Live update
                    if live_update and location in scraping_progress['insurance']:
                        scraping_progress['insurance'][location]['providers'].append(provider_data)
        
        logger.info(f"Successfully scraped {len(providers)} insurance providers")
        
        # Mark scraping as complete
        if live_update and location in scraping_progress['insurance']:
            scraping_progress['insurance'][location]['status'] = 'complete'
        
    except Exception as e:
        logger.error(f"Error in insurance provider scraping: {str(e)}")
        # Return fallback data
        providers = generate_fallback_insurance_providers(location)
        
        # Mark scraping as failed
        if live_update and location in scraping_progress['insurance']:
            scraping_progress['insurance'][location]['status'] = 'failed'
            scraping_progress['insurance'][location]['providers'] = providers
    
    finally:
        if driver:
            driver.quit()
    
    return providers

def generate_fallback_healthcare_providers(location):
    """Generate fallback healthcare provider data when scraping fails"""
    import random
    
    provider_names = [
        "Memorial Healthcare System", "Baptist Health", "Cleveland Clinic Florida",
        "Mount Sinai Medical Center", "Aventura Hospital", "Jackson Health System",
        "Nicklaus Children's Hospital", "Holy Cross Health", "Broward Health",
        "Joe DiMaggio Children's Hospital", "University of Miami Health System",
        "Kendall Regional Medical Center", "Palmetto General Hospital"
    ]
    
    providers = []
    for idx, name in enumerate(provider_names[:10]):
        providers.append({
            "name": name,
            "location": location,
            "address": f"{100 + idx * 10} Medical Plaza, {location}, FL 33{130 + idx}",
            "phone": f"(305) 555-{1000 + idx}",
            "website": f"https://{name.lower().replace(' ', '')}.com",
            "rating": round(random.uniform(3.5, 5.0), 1),
            "distance": round(random.uniform(0.5, 20.0), 1),
            "source": "Local Database"
        })
    
    return providers

def generate_fallback_insurance_providers(location):
    """Generate fallback insurance provider data when scraping fails"""
    
    insurance_companies = [
        {"name": "Florida Blue", "phone": "1-800-352-2583"},
        {"name": "Aetna", "phone": "1-800-872-3862"},
        {"name": "UnitedHealthcare", "phone": "1-800-328-5979"},
        {"name": "Cigna", "phone": "1-800-244-6224"},
        {"name": "Humana", "phone": "1-800-448-6262"},
        {"name": "Blue Cross Blue Shield", "phone": "1-800-262-2583"},
        {"name": "Anthem", "phone": "1-800-331-1476"},
        {"name": "Kaiser Permanente", "phone": "1-800-464-4000"},
        {"name": "Molina Healthcare", "phone": "1-800-526-8196"},
        {"name": "Ambetter", "phone": "1-877-687-1197"}
    ]
    
    providers = []
    for idx, company in enumerate(insurance_companies):
        providers.append({
            "name": company["name"],
            "url": f"https://{company['name'].lower().replace(' ', '')}.com",
            "phone": company["phone"],
            "address": f"{location}, FL",
            "location": location,
            "description": "Health insurance provider serving Florida",
            "website": f"https://{company['name'].lower().replace(' ', '')}.com",
            "source": "Local Database"
        })
    
    return providers

def update_provider_cache(location, live_update=False):
    """Update the cache with fresh provider data"""
    try:
        if live_update:
            # Run scraping in background thread for live updates
            def scrape_in_background():
                healthcare_providers = scrape_healthcare_providers(location, live_update=True)
                insurance_providers = scrape_insurance_providers(location, live_update=True)
                
                scraped_cache['healthcare'][location] = healthcare_providers
                scraped_cache['insurance'][location] = insurance_providers
                scraped_cache['last_update'] = time.time()
            
            thread = threading.Thread(target=scrape_in_background)
            thread.daemon = True
            thread.start()
            return True
        else:
            # Run synchronously
            healthcare_providers = scrape_healthcare_providers(location, live_update=False)
            insurance_providers = scrape_insurance_providers(location, live_update=False)
            
            scraped_cache['healthcare'][location] = healthcare_providers
            scraped_cache['insurance'][location] = insurance_providers
            scraped_cache['last_update'] = time.time()
            
            return True
    except Exception as e:
        logger.error(f"Error updating provider cache: {str(e)}")
        return False

def get_cached_providers(provider_type, location):
    """Get providers from cache, update if necessary"""
    current_time = time.time()
    
    # Check if cache needs updating
    if (location not in scraped_cache[provider_type] or 
        scraped_cache['last_update'] is None or
        current_time - scraped_cache['last_update'] > CACHE_EXPIRATION):
        update_provider_cache(location)
    
    return scraped_cache[provider_type].get(location, [])

def detect_query_intent(query):
    """Detect if the query is about symptoms, insurance, or clinic search"""
    q = query.lower()
    
    # Insurance keywords
    insurance_keywords = ['insurance', 'coverage', 'plan', 'premium', 'policy', 'aetna', 'cigna', 
                          'blue cross', 'humana', 'medicare', 'medicaid']
    if any(keyword in q for keyword in insurance_keywords):
        return 'insurance'
    
    # Symptom indicators
    symptom_indicators = ['pain', 'ache', 'hurt', 'feel', 'symptoms', 'sick', 'ill', 'fever', 
                          'cough', 'nausea', 'vomit', 'dizzy', 'tired', 'fatigue', 'rash', 
                          'swelling', 'headache', 'sore', 'breathing', 'chest']
    symptom_phrases = ['i have', 'i feel', 'experiencing', 'suffering from']
    
    if any(phrase in q for phrase in symptom_phrases):
        return 'symptom'
    
    # Count symptom keywords
    symptom_count = sum(1 for word in symptom_indicators if word in q)
    if symptom_count >= 2:
        return 'symptom'
    
    # Check against symptom database
    words = q.split()
    for word in words:
        if word in medical_db.get('symptoms_database', {}):
            return 'symptom'
    
    # Clinic/provider keywords
    clinic_keywords = ['doctor', 'clinic', 'hospital', 'physician', 'specialist', 'dentist', 
                       'pediatrician', 'dermatologist', 'cardiologist']
    if any(keyword in q for keyword in clinic_keywords):
        return 'clinic'
    
    # Default to mixed if unclear
    return 'mixed'

def normalize_query(query):
    """Normalize query by applying synonyms and expanding terms"""
    q = query.lower()
    
    # Apply symptom synonyms
    for synonym, replacement in medical_db.get('symptom_synonyms', {}).items():
        if synonym in q:
            q = q.replace(synonym, replacement)
    
    return q

def search_clinics(query, location=None):
    """Enhanced clinic search with better matching and scoring"""
    matches = []
    query_normalized = normalize_query(query)
    query_lower = query.lower()
    
    # Get providers from cache/web scraping
    if location:
        providers = get_cached_providers('healthcare', location)
    else:
        providers = []
        for loc_providers in scraped_cache['healthcare'].values():
            if isinstance(loc_providers, list):
                providers.extend(loc_providers)
    
    # Search scraped providers with relevance scoring
    for provider in providers:
        score = 0
        provider_name = provider.get('name', '').lower()
        provider_address = provider.get('address', '').lower()
        
        # Name match (highest weight)
        if query_lower in provider_name:
            score += 10
            provider['relevance_score'] = score
            matches.append(provider)
            continue
        
        # Address/location match
        if query_lower in provider_address:
            score += 5
            provider['relevance_score'] = score
            matches.append(provider)
            continue
        
        # Partial word matches
        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 3:  # Only meaningful words
                if word in provider_name:
                    score += 3
                if word in provider_address:
                    score += 1
        
        if score > 0:
            provider['relevance_score'] = score
            matches.append(provider)
    
    # Add local database results as fallback
    for clinic in medical_db['clinics']:
        if location and location.lower() not in clinic['location'].lower():
            continue
        
        score = 0
        clinic_name = clinic['name'].lower()
        
        # Direct name match
        if query_lower in clinic_name:
            score += 10
        
        # Specialty match
        if 'specialties' in clinic:
            for specialty in clinic['specialties']:
                if query_lower in specialty.lower():
                    score += 8
        
        # Insurance match
        if 'insurance' in clinic:
            for insurance in clinic['insurance']:
                if query_lower in insurance.lower():
                    score += 3
        
        if score > 0:
            clinic['relevance_score'] = score
            # Avoid duplicates
            if not any(m.get('name') == clinic['name'] for m in matches):
                matches.append(clinic)
    
    return matches

def search_clinics_by_specialty(query, location=None):
    """Search clinics based on symptoms/conditions to suggest appropriate specialties"""
    matches = []
    query_normalized = normalize_query(query)
    
    # Analyze symptoms to determine needed specialties
    symptom_analysis = analyze_symptoms(query)
    suggested_specialties = set()
    
    # Map conditions to specialties
    for condition in symptom_analysis.get('possible_conditions', []):
        condition_lower = condition.lower()
        # Add specialty mapping logic
        if any(term in condition_lower for term in ['heart', 'cardiac', 'angina']):
            suggested_specialties.add('Cardiology')
        elif any(term in condition_lower for term in ['skin', 'rash', 'eczema', 'psoriasis']):
            suggested_specialties.add('Dermatology')
        elif any(term in condition_lower for term in ['mental', 'depression', 'anxiety', 'stress']):
            suggested_specialties.add('Psychiatry')
        elif any(term in condition_lower for term in ['child', 'pediatric']):
            suggested_specialties.add('Pediatrics')
        else:
            suggested_specialties.add('General Practice')
    
    # Check specialty keywords in query
    for keyword, specialty in medical_db.get('specialty_keywords', {}).items():
        if keyword in query.lower():
            suggested_specialties.add(specialty)
    
    # Get providers
    if location:
        providers = get_cached_providers('healthcare', location)
    else:
        providers = []
        for loc_providers in scraped_cache['healthcare'].values():
            if isinstance(loc_providers, list):
                providers.extend(loc_providers)
    
    # Add local DB clinics
    all_clinics = list(providers) + medical_db.get('clinics', [])
    
    # Filter by specialties if we found any
    if suggested_specialties:
        for clinic in all_clinics:
            clinic_specialties = clinic.get('specialties', [])
            if isinstance(clinic_specialties, list):
                for specialty in clinic_specialties:
                    if any(sugg.lower() in specialty.lower() for sugg in suggested_specialties):
                        clinic['relevance_score'] = 8
                        clinic['suggested_for'] = list(suggested_specialties)
                        matches.append(clinic)
                        break
    
    # If no specialty matches, return general practitioners
    if not matches:
        for clinic in all_clinics:
            specialties = clinic.get('specialties', [])
            if any('general' in str(s).lower() for s in specialties):
                clinic['relevance_score'] = 5
                matches.append(clinic)
    
    return matches

def rank_clinic_results(clinics):
    """Rank clinic results by relevance, rating, and distance"""
    def get_sort_key(clinic):
        relevance = clinic.get('relevance_score', 0)
        rating = clinic.get('rating', 0) or 0
        distance = clinic.get('distance', 999) or 999
        
        # Weighted scoring: relevance (40%), rating (40%), distance (20%)
        score = (relevance * 0.4) + (rating * 0.4) - (distance * 0.02)
        return -score  # Negative for descending sort
    
    return sorted(clinics, key=get_sort_key)

def search_insurance(query, location=None):
    """Search insurance providers across scraped cache and local DB.
    Returns enriched records with phone, website, coverage_types (if available), and description.
    """
    matches = []
    q = query.lower()

    scraped = []
    if location:
        scraped = get_cached_providers('insurance', location)
    else:
        # aggregate all cached insurance providers
        for loc_vals in scraped_cache['insurance'].values():
            if isinstance(loc_vals, list):
                scraped.extend(loc_vals)

    for provider in scraped:
        name_l = provider.get('name', '').lower()
        desc_l = provider.get('description', '').lower()
        if not q or q in name_l or q in desc_l:
            matches.append({
                'name': provider.get('name'),
                'description': provider.get('description'),
                'phone': provider.get('phone'),
                'website': provider.get('website') or provider.get('url'),
                'coverage_types': provider.get('coverage_types', []),
                'source': provider.get('source', 'scraped')
            })

    # Fallback to local DB
    for provider in medical_db.get('insurance_providers', []):
        name_l = provider.get('name', '').lower()
        coverage_list = provider.get('coverage_types', [])
        if (not q or q in name_l or any(q in c.lower() for c in coverage_list)) and not any(m['name'] == provider['name'] for m in matches):
            matches.append({
                'name': provider.get('name'),
                'description': provider.get('description', ''),
                'phone': provider.get('phone') or provider.get('contact'),
                'website': provider.get('website') or provider.get('url'),
                'coverage_types': coverage_list,
                'source': 'local'
            })

    return matches

@app.route('/providers', methods=['GET'])
def get_providers():
    provider_type = request.args.get('type', 'all')
    location = request.args.get('location', None)
    
    # Initialize response structure
    providers = {
        'healthcare': [],
        'insurance': []
    }
    
    try:
        # Get scraped providers if location is provided
        if location:
            if provider_type in ['all', 'healthcare']:
                healthcare_providers = get_cached_providers('healthcare', location)
                providers['healthcare'] = [provider['name'] for provider in healthcare_providers]
            
            if provider_type in ['all', 'insurance']:
                insurance_providers = get_cached_providers('insurance', location)
                providers['insurance'] = [provider['name'] for provider in insurance_providers]
        
        # Fall back to database providers if no location or no scraped results
        if not providers['healthcare']:
            providers['healthcare'] = [clinic['name'] for clinic in medical_db['clinics']]
        if not providers['insurance']:
            providers['insurance'] = [provider['name'] for provider in medical_db['insurance_providers']]
        
        if provider_type == 'all':
            return jsonify(providers)
        elif provider_type in providers:
            return jsonify(providers[provider_type])
        else:
            return jsonify({'error': 'Invalid provider type'}), 400
            
    except Exception as e:
        logger.error(f"Error getting providers: {str(e)}")
        return jsonify({'error': 'Failed to fetch providers'}), 500
    
@app.route('/healthcare_graph', methods=['GET'])
def healthcare_graph():
    try:
        # Get location from query params
        location = request.args.get('location', None)
        
        # Get providers from cache/scraping
        providers = []
        if location:
            providers.extend(get_cached_providers('healthcare', location))
        
        # If no scraped results, fall back to database
        if not providers:
            providers = medical_db['clinics']
        
        # Build graph data
        graph_data = []
        for provider in providers:
            # Find average score for this provider
            scores = [r['rating'] for r in reviews_db['healthcare'] 
                     if r['provider_name'] == provider['name']]
            avg_score = round(sum(scores)/len(scores), 2) if scores else None
            
            provider_data = {
                'name': provider['name'],
                'address': provider.get('address', 'Address not available'),
                'phone': provider.get('phone', 'Phone not available'),
                'website': provider.get('website', '#'),
                'rating': avg_score,
                'distance': provider.get('distance', 'N/A'),
                'source': provider.get('source', 'Local Database')
            }
            
            graph_data.append(provider_data)
        # Sort providers by distance if available, then by rating
        graph_data.sort(key=lambda x: (
            float('inf') if x['distance'] == 'N/A' else float(x['distance']),
            float('-inf') if x['rating'] is None else -float(x['rating'])
        ))
        
        return jsonify(graph_data)
    except Exception as e:
        logger.error(f"Error generating healthcare graph: {str(e)}")
        return jsonify({'error': 'Failed to generate healthcare graph'}), 500

## Removed /insurance_providers endpoint (insurance now served via unified /search)

@app.route('/get-provider-graph', methods=['GET'])
def get_provider_graph():
    """Alias for healthcare_graph to maintain compatibility"""
    return healthcare_graph()

@app.route('/scraping-progress', methods=['GET'])
def get_scraping_progress():
    """Get live scraping progress for a specific location and type"""
    try:
        location = request.args.get('location', None)
        provider_type = request.args.get('type', 'all')  # 'healthcare', 'insurance', or 'all'
        
        if not location:
            return jsonify({'error': 'Location parameter required'}), 400
        
        progress_data = {}
        
        if provider_type in ['all', 'healthcare']:
            progress_data['healthcare'] = scraping_progress['healthcare'].get(location, {
                'status': 'not_started',
                'providers': [],
                'progress': 0,
                'total': 0
            })
        
        if provider_type in ['all', 'insurance']:
            progress_data['insurance'] = scraping_progress['insurance'].get(location, {
                'status': 'not_started',
                'providers': [],
                'progress': 0,
                'total': 0
            })
        
        return jsonify(progress_data)
    except Exception as e:
        logger.error(f"Error getting scraping progress: {str(e)}")
        return jsonify({'error': 'Failed to get scraping progress'}), 500

@app.route('/start-scraping', methods=['POST'])
def start_scraping():
    """Start live scraping for a specific location"""
    try:
        data = request.json
        location = data.get('location', None)
        
        if not location:
            return jsonify({'error': 'Location parameter required'}), 400
        
        # Check if already scraping
        healthcare_status = scraping_progress['healthcare'].get(location, {}).get('status', 'not_started')
        insurance_status = scraping_progress['insurance'].get(location, {}).get('status', 'not_started')
        
        if healthcare_status == 'scraping' or insurance_status == 'scraping':
            return jsonify({
                'message': 'Scraping already in progress',
                'status': 'in_progress'
            })
        
        # Start scraping with live updates
        update_provider_cache(location, live_update=True)
        
        return jsonify({
            'message': 'Scraping started',
            'status': 'started',
            'location': location
        })
    except Exception as e:
        logger.error(f"Error starting scraping: {str(e)}")
        return jsonify({'error': 'Failed to start scraping'}), 500

@app.route('/reviews', methods=['GET'])
def get_reviews():
    review_type = request.args.get('type', 'all')
    if review_type == 'all':
        return jsonify(reviews_db)
    elif review_type in reviews_db:
        return jsonify(reviews_db[review_type])
    else:
        return jsonify({'error': 'Invalid review type'}), 400

@app.route('/reviews/submit', methods=['POST'])
def submit_review():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['type', 'provider_name', 'rating', 'review_text']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        if data['type'] not in ['healthcare', 'insurance']:
            return jsonify({'error': 'Invalid review type'}), 400
            
        new_review = {
            'id': len(reviews_db[data['type']]) + 1,
            'provider_name': data['provider_name'],
            'rating': data['rating'],
            'review_text': data['review_text'],
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        reviews_db[data['type']].append(new_review)
        return jsonify({'message': 'Review submitted successfully', 'review': new_review})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_symptoms(query):
    """Enhanced symptom analysis with better NLP and multi-word detection"""
    # Normalize the query
    query_normalized = normalize_query(query)
    
    # Extract words and phrases
    words = re.findall(r'\b\w+\b', query_normalized.lower())
    
    # Also check for multi-word symptoms
    query_lower = query_normalized.lower()
    
    # Check symptoms against our database
    possible_conditions = set()
    matched_symptoms = []
    
    # Check multi-word symptoms first
    for symptom, conditions in medical_db['symptoms_database'].items():
        if ' ' in symptom:  # Multi-word symptom
            if symptom in query_lower:
                possible_conditions.update(conditions)
                matched_symptoms.append(symptom)
        else:  # Single word
            if symptom in words:
                possible_conditions.update(conditions)
                matched_symptoms.append(symptom)
    
    # Enhanced confidence calculation
    base_confidence = 0.3
    
    # Boost confidence based on number of matched symptoms
    symptom_boost = min(len(matched_symptoms), 5) * 0.12
    
    # Boost confidence based on number of conditions
    condition_boost = min(len(possible_conditions), 4) * 0.08
    
    # Check for severity keywords
    severity_keywords = ['severe', 'intense', 'unbearable', 'extreme', 'terrible', 'sharp', 
                         'chronic', 'constant', 'persistent', 'recurring']
    has_severity = any(keyword in query_lower for keyword in severity_keywords)
    severity_boost = 0.1 if has_severity else 0
    
    confidence = round(min(base_confidence + symptom_boost + condition_boost + severity_boost, 0.95), 2)
    
    # Generate more detailed recommendations
    recommendation = get_detailed_recommendation(possible_conditions, matched_symptoms, query_lower)
    
    ai_analysis = {
        'possible_conditions': list(possible_conditions),
        'matched_symptoms': matched_symptoms,
        'confidence_score': confidence,
        'recommendation': recommendation,
        'urgency': assess_urgency(matched_symptoms, query_lower),
        'disclaimer': "This is not a medical diagnosis. Please consult with a healthcare professional for proper medical advice."
    }

    return ai_analysis

def assess_urgency(symptoms, query):
    """Assess urgency level based on symptoms"""
    emergency_keywords = ['chest pain', 'cant breathe', 'difficulty breathing', 'severe', 
                          'bleeding', 'unconscious', 'seizure', 'stroke', 'heart attack',
                          'suicide', 'overdose', 'severe pain']
    
    urgent_keywords = ['fever', 'vomiting', 'severe headache', 'confusion', 'dizziness']
    
    # Check for emergency symptoms
    for keyword in emergency_keywords:
        if keyword in query:
            return 'emergency'
    
    # Check for urgent symptoms
    urgent_count = sum(1 for keyword in urgent_keywords if keyword in query)
    if urgent_count >= 2:
        return 'urgent'
    
    # Check symptom count
    if len(symptoms) > 4:
        return 'moderate'
    
    return 'routine'

def get_detailed_recommendation(conditions, symptoms, query):
    """Generate detailed recommendations based on conditions and context"""
    if not conditions and not symptoms:
        return "No specific conditions identified. Please consult a healthcare provider for proper evaluation."
    
    urgency = assess_urgency(symptoms, query)
    
    if urgency == 'emergency':
        return "⚠️ URGENT: Based on your symptoms, seek immediate medical attention. Call 911 or go to the nearest emergency room."
    
    if urgency == 'urgent':
        return "These symptoms may require prompt medical attention. Consider visiting an urgent care center or scheduling a same-day appointment with your healthcare provider."
    
    severity = len(conditions)
    
    if severity > 3:
        return "Multiple conditions may be associated with your symptoms. It's recommended to schedule an appointment with your healthcare provider for proper diagnosis and treatment."
    elif severity > 1:
        recommendation = "Your symptoms may indicate several possible conditions. Consider scheduling an appointment with your healthcare provider for evaluation. "
        
        # Add specialty recommendations
        specialties = []
        conditions_lower = [c.lower() for c in conditions]
        
        if any('heart' in c or 'cardiac' in c for c in conditions_lower):
            specialties.append("cardiology")
        if any('skin' in c or 'rash' in c for c in conditions_lower):
            specialties.append("dermatology")
        if any('mental' in c or 'anxiety' in c or 'depression' in c for c in conditions_lower):
            specialties.append("psychiatry or mental health")
        
        if specialties:
            recommendation += f"You may want to consult with a specialist in {' or '.join(specialties)}."
        
        return recommendation
    else:
        return "Monitor your symptoms over the next 24-48 hours. If they persist, worsen, or new symptoms develop, consult a healthcare provider."

@app.route('/update-location', methods=['POST'])
def update_location():
    try:
        data = request.json
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({'success': False, 'error': 'Invalid location data'}), 400

        # Store location with timestamp and source
        location_data = {
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'accuracy': data.get('accuracy'),
            'is_manual_selection': data.get('isManualSelection', False),
            'timestamp': datetime.now().isoformat()
        }
        
        # In production, you would store this in a database
        # For demo, we're using a simple in-memory dictionary
        user_locations[request.remote_addr] = location_data
        
        return jsonify({
            'success': True,
            'message': 'Location updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)