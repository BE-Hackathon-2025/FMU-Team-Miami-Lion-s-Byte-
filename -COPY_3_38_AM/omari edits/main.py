# from flask import Flask
# app = Flask(__name__)
# @app.route('/')
# def home():
#     return "Sup, Berry!"

from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import re

app = Flask(__name__)

# Store location data in memory (replace with database in production)
user_locations = {}

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
                "insurance": ["Aetna", "Blue Cross", "Cigna"]
            },
            # Add more clinics here
        ],
        "insurance_providers": [
            {
                "name": "Florida Health Insurance",
                "coverage_types": ["Individual", "Family", "Medicare"],
                "contact": "1-800-555-0123"
            },
            # Add more providers here
        ],
        "symptoms_database": {
            "headache": ["Migraine", "Tension Headache", "Sinusitis"],
            "fever": ["Flu", "COVID-19", "Common Cold"],
            # Add more symptoms and conditions
        }
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
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
        if search_type in ['all', 'clinics']:
            results['clinics'] = search_clinics(query, location)
            
        if search_type in ['all', 'insurance']:
            results['insurance'] = search_insurance(query)
            
        if search_type in ['all', 'symptoms']:
            results['medical_advice'] = analyze_symptoms(query)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def search_clinics(query, location=None):
    matches = []
    query = query.lower()
    
    for clinic in medical_db['clinics']:
        # Check if clinic matches query and location
        if location and location.lower() not in clinic['location'].lower():
            continue
            
        if (query in clinic['name'].lower() or
            any(query in specialty.lower() for specialty in clinic['specialties']) or
            any(query in insurance.lower() for insurance in clinic['insurance'])):
            matches.append(clinic)
    
    return matches

def search_insurance(query):
    matches = []
    query = query.lower()
    
    for provider in medical_db['insurance_providers']:
        if (query in provider['name'].lower() or
            any(query in coverage.lower() for coverage in provider['coverage_types'])):
            matches.append(provider)
    
    return matches

def analyze_symptoms(query):
    # Clean and process the symptoms text
    symptoms = re.findall(r'\b\w+\b', query.lower())
    
    # Check symptoms against our database
    possible_conditions = set()
    for symptom in symptoms:
        if symptom in medical_db['symptoms_database']:
            possible_conditions.update(medical_db['symptoms_database'][symptom])
    
    # Rule-based fallback analysis (torch/transformers integration removed)
    # Heuristic confidence: base 0.5, increase with number of matched conditions
    base_confidence = 0.5
    boost = min(len(possible_conditions), 4) * 0.12
    confidence = round(min(base_confidence + boost, 0.98), 2)

    ai_analysis = {
        'possible_conditions': list(possible_conditions),
        'confidence_score': confidence,
        'recommendation': get_recommendation(possible_conditions),
        'disclaimer': "This is not a medical diagnosis. Please consult with a healthcare professional for proper medical advice."
    }

    return ai_analysis

def get_recommendation(conditions):
    if not conditions:
        return "No specific conditions identified. Please consult a healthcare provider for proper evaluation."
    
    severity = len(conditions)
    if severity > 3:
        return "Multiple symptoms detected. It's recommended to seek immediate medical attention."
    elif severity > 1:
        return "Consider scheduling an appointment with a healthcare provider for evaluation."
    else:
        return "Monitor your symptoms. If they persist or worsen, consult a healthcare provider."

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