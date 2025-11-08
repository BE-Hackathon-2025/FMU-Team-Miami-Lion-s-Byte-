// Slider functionality
const slides = document.querySelectorAll('.slide');
const nextBtn = document.getElementById('nextBtn');
const prevBtn = document.getElementById('prevBtn');
let currentSlide = 0;

function showSlide(index) {
    slides.forEach((slide, i) => {
        slide.classList.remove('active');
        if (i === index) slide.classList.add('active');
    });
}

if (nextBtn && prevBtn) {
    nextBtn.addEventListener('click', () => {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    });

    prevBtn.addEventListener('click', () => {
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        showSlide(currentSlide);
    });
}

// Smooth scrolling for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Global Variables
let currentLocation = '';
let scrapingInProgress = false;
let progressCheckInterval = null;

// Location Services Handler
function updateLocationData() {
    // Start live scraping and update both healthcare and insurance data
    startLiveScraping();
}

// Start live scraping with progress updates
function startLiveScraping() {
    if (!currentLocation || scrapingInProgress) {
        return;
    }

    scrapingInProgress = true;

    // Show loading indicators
    showLoadingIndicators();

    // Start scraping on backend
    fetch('/start-scraping', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                location: currentLocation
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Scraping started:', data);

            // Start polling for progress updates
            progressCheckInterval = setInterval(() => {
                checkScrapingProgress();
            }, 2000); // Check every 2 seconds
        })
        .catch(error => {
            console.error('Error starting scraping:', error);
            scrapingInProgress = false;
            hideLoadingIndicators();
        });
}

// Check scraping progress and update tables
function checkScrapingProgress() {
    fetch(`/scraping-progress?location=${currentLocation}&type=all`)
        .then(response => response.json())
        .then(data => {
            // Update healthcare providers
            if (data.healthcare) {
                updateHealthcareTable(data.healthcare.providers);

                // Check if healthcare scraping is complete
                if (data.healthcare.status === 'complete' || data.healthcare.status === 'failed') {
                    console.log('Healthcare scraping complete');
                }
            }

            // Insurance provider live table removed (now integrated in search results)

            // Stop polling if both are complete
            if (data.healthcare && data.insurance &&
                (data.healthcare.status === 'complete' || data.healthcare.status === 'failed') &&
                (data.insurance.status === 'complete' || data.insurance.status === 'failed')) {
                clearInterval(progressCheckInterval);
                scrapingInProgress = false;
                hideLoadingIndicators();

                // Final update from cache
                updateProviderData();
            }
        })
        .catch(error => {
            console.error('Error checking progress:', error);
        });
}

// Show loading indicators
function showLoadingIndicators() {
    const healthcareTableBody = document.getElementById('provider-graph-body');

    if (healthcareTableBody) {
        healthcareTableBody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem;"><div class="loading-indicator">Loading healthcare providers... <span class="spinner">⟳</span></div></td></tr>';
    }
}

// Hide loading indicators
function hideLoadingIndicators() {
    // Loading indicators will be replaced by tables
}

// Update healthcare table with live data
function updateHealthcareTable(providers) {
    if (!providers || providers.length === 0) return;

    const tbody = document.getElementById('provider-graph-body');
    if (!tbody) return;

    tbody.innerHTML = ''; // Clear existing content

    // Add data rows
    providers.forEach((provider, index) => {
        const row = document.createElement('tr');
        row.classList.add('fade-in');
        row.style.animationDelay = `${index * 0.05}s`;

        // Medical Professional
        const professionalCell = document.createElement('td');
        professionalCell.textContent = provider.name || 'N/A';
        row.appendChild(professionalCell);

        // Clinic
        const clinicCell = document.createElement('td');
        clinicCell.textContent = provider.source || 'Healthcare Facility';
        row.appendChild(clinicCell);

        // Address
        const addressCell = document.createElement('td');
        addressCell.textContent = provider.address || 'Address not available';
        addressCell.style.maxWidth = '200px';
        addressCell.style.whiteSpace = 'normal';
        row.appendChild(addressCell);

        // Phone
        const phoneCell = document.createElement('td');
        if (provider.phone) {
            const phoneLink = document.createElement('a');
            phoneLink.href = `tel:${provider.phone}`;
            phoneLink.textContent = provider.phone;
            phoneLink.style.color = 'var(--secondary-color)';
            phoneLink.style.textDecoration = 'none';
            phoneCell.appendChild(phoneLink);
        } else {
            phoneCell.textContent = 'N/A';
        }
        row.appendChild(phoneCell);

        // Price
        const priceCell = document.createElement('td');
        priceCell.textContent = 'Call for pricing';
        priceCell.style.fontStyle = 'italic';
        priceCell.style.color = '#666';
        row.appendChild(priceCell);

        // Specialties
        const specialtiesCell = document.createElement('td');
        const specialties = provider.specialties || ['General Practice'];
        specialtiesCell.textContent = Array.isArray(specialties) ? specialties.join(', ') : specialties;
        specialtiesCell.style.maxWidth = '180px';
        specialtiesCell.style.whiteSpace = 'normal';
        row.appendChild(specialtiesCell);

        // Avg. Score
        const scoreCell = document.createElement('td');
        if (provider.rating) {
            scoreCell.innerHTML = `<span style="color: #ffd700;">★</span> ${provider.rating.toFixed(1)}`;
        } else {
            scoreCell.textContent = 'Not rated';
            scoreCell.style.color = '#999';
        }
        row.appendChild(scoreCell);

        // Distance
        const distanceCell = document.createElement('td');
        if (provider.distance) {
            distanceCell.textContent = `${provider.distance.toFixed(1)} mi`;
        } else {
            distanceCell.textContent = 'N/A';
        }
        row.appendChild(distanceCell);

        tbody.appendChild(row);
    });
}

// Update insurance table with live data
function updateInsuranceTable(providers) {
    if (!providers || providers.length === 0) return;

    const container = document.getElementById('insurance-provider-graph');
    if (!container) return;

    container.innerHTML = ''; // Clear existing content

    // Create table
    const table = document.createElement('table');
    table.classList.add('provider-table');

    // Create header row
    const headerRow = document.createElement('tr');
    ['Insurance Provider', 'Description', 'Phone', 'Website'].forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);

    // Add data rows
    providers.forEach(provider => {
        const row = document.createElement('tr');
        row.classList.add('fade-in'); // Add animation class

        // Provider Name
        const nameCell = document.createElement('td');
        nameCell.textContent = provider.name;
        row.appendChild(nameCell);

        // Description
        const descCell = document.createElement('td');
        descCell.textContent = provider.description || 'Health insurance provider';
        row.appendChild(descCell);

        // Phone
        const phoneCell = document.createElement('td');
        const phoneLink = document.createElement('a');
        phoneLink.href = `tel:${provider.phone}`;
        phoneLink.textContent = provider.phone;
        phoneCell.appendChild(phoneLink);
        row.appendChild(phoneCell);

        // Website
        const websiteCell = document.createElement('td');
        const websiteLink = document.createElement('a');
        websiteLink.href = provider.website || provider.url;
        websiteLink.textContent = 'Visit Website';
        websiteLink.target = '_blank';
        websiteCell.appendChild(websiteLink);
        row.appendChild(websiteCell);

        table.appendChild(row);
    });

    container.appendChild(table);
}

// Reviews functionality
// Function to create star rating display
function createStarRating(rating) {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
        stars.push(`<span class="star ${i <= rating ? '' : 'empty'}">★</span>`);
    }
    return `<div class="star-rating-display">${stars.join('')}</div>`;
}

// Function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Healthcare Provider Graph
// Function to update provider data based on current location
function updateProviderData() {
    if (!currentLocation) {
        // No location selected yet
        const tbody = document.getElementById('provider-graph-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem;">Please select a location to view healthcare providers</td></tr>';
        }
        return;
    }

    // Show loading state
    const tbody = document.getElementById('provider-graph-body');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem;"><div class="loading-indicator">Loading healthcare providers... <span class="spinner">⟳</span></div></td></tr>';
    }

    // Fetch healthcare provider graph data
    fetch(`/get-provider-graph?location=${currentLocation}`)
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('provider-graph-body');
            if (!tbody) return;
            
            tbody.innerHTML = ''; // Clear existing content

            if (!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem;">No healthcare providers found for this location. Try selecting a different area.</td></tr>';
                return;
            }

            // Add data rows
            data.forEach((provider, index) => {
                const row = document.createElement('tr');
                row.classList.add('fade-in');
                row.style.animationDelay = `${index * 0.05}s`;

                // Medical Professional (using provider name)
                const professionalCell = document.createElement('td');
                professionalCell.textContent = provider.name || 'N/A';
                row.appendChild(professionalCell);

                // Clinic (extract from name or use source)
                const clinicCell = document.createElement('td');
                clinicCell.textContent = provider.source || 'Healthcare Facility';
                row.appendChild(clinicCell);

                // Address
                const addressCell = document.createElement('td');
                addressCell.textContent = provider.address || 'Address not available';
                addressCell.style.maxWidth = '200px';
                addressCell.style.whiteSpace = 'normal';
                row.appendChild(addressCell);

                // Phone
                const phoneCell = document.createElement('td');
                if (provider.phone) {
                    const phoneLink = document.createElement('a');
                    phoneLink.href = `tel:${provider.phone}`;
                    phoneLink.textContent = provider.phone;
                    phoneLink.style.color = 'var(--secondary-color)';
                    phoneLink.style.textDecoration = 'none';
                    phoneCell.appendChild(phoneLink);
                } else {
                    phoneCell.textContent = 'N/A';
                }
                row.appendChild(phoneCell);

                // Price (placeholder - not available in current data)
                const priceCell = document.createElement('td');
                priceCell.textContent = 'Call for pricing';
                priceCell.style.fontStyle = 'italic';
                priceCell.style.color = '#666';
                row.appendChild(priceCell);

                // Specialties (extract from name or default)
                const specialtiesCell = document.createElement('td');
                const specialties = provider.specialties || ['General Practice'];
                specialtiesCell.textContent = Array.isArray(specialties) ? specialties.join(', ') : specialties;
                specialtiesCell.style.maxWidth = '180px';
                specialtiesCell.style.whiteSpace = 'normal';
                row.appendChild(specialtiesCell);

                // Avg. Score (rating)
                const scoreCell = document.createElement('td');
                if (provider.rating) {
                    scoreCell.innerHTML = `<span style="color: #ffd700;">★</span> ${provider.rating.toFixed(1)}`;
                } else {
                    scoreCell.textContent = 'Not rated';
                    scoreCell.style.color = '#999';
                }
                row.appendChild(scoreCell);

                // Distance
                const distanceCell = document.createElement('td');
                if (provider.distance) {
                    distanceCell.textContent = `${provider.distance.toFixed(1)} mi`;
                } else {
                    distanceCell.textContent = 'N/A';
                }
                row.appendChild(distanceCell);

                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading provider data:', error);
            const tbody = document.getElementById('provider-graph-body');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem; color: #e74c3c;">Error loading provider data. Please try again later.</td></tr>';
            }
        });
}

// Function to update insurance providers based on current location
// Removed updateInsuranceProviders (insurance results now surfaced via unified /search endpoint)

async function loadReviews() {
    try {
        const response = await fetch('/reviews?type=all');
        const data = await response.json();

        // Update healthcare reviews
        const healthcareReviews = document.getElementById('healthcare-reviews');
        healthcareReviews.innerHTML = data.healthcare.map(review => `
            <div class="review-card">
                <div class="review-header">
                    <strong>${review.provider_name}</strong>
                    ${createStarRating(review.rating)}
                    <div class="review-meta">
                        <span class="review-date">${formatDate(review.date)}</span>
                    </div>
                </div>
                <div class="review-text">${review.review_text}</div>
            </div>
        `).join('');

        // Update insurance reviews
        const insuranceReviews = document.getElementById('insurance-reviews');
        insuranceReviews.innerHTML = data.insurance.map(review => `
            <div class="review-card">
                <div class="review-header">
                    <strong>${review.provider_name}</strong>
                    ${createStarRating(review.rating)}
                    <div class="review-meta">
                        <span class="review-date">${formatDate(review.date)}</span>
                    </div>
                </div>
                <div class="review-text">${review.review_text}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading reviews:', error);
    }
}

async function submitReview(event, type) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    try {
        const response = await fetch('/reviews/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: type,
                provider_name: formData.get('provider_name'),
                rating: parseInt(formData.get('rating')),
                review_text: formData.get('review_text')
            })
        });

        const result = await response.json();
        if (response.ok) {
            form.reset();
            loadReviews(); // Reload all reviews
        } else {
            alert('Error submitting review: ' + result.error);
        }
    } catch (error) {
        console.error('Error submitting review:', error);
        alert('Failed to submit review. Please try again.');
    }
}

// Initialize star rating functionality
function initializeStarRating() {
    const ratingContainers = document.querySelectorAll('.rating-input');

    ratingContainers.forEach(container => {
        const labels = container.querySelectorAll('label');

        labels.forEach(label => {
            // Hover effect
            label.addEventListener('mouseover', () => {
                const currentRating = label.getAttribute('for').slice(-1);
                updateStars(container, currentRating, 'hover');
            });

            // Mouse leave effect
            label.addEventListener('mouseout', () => {
                const selectedRating = container.querySelector('input[type="radio"]:checked');
                updateStars(container, selectedRating ? selectedRating.value : 0, 'selected');
            });

            // Click effect
            label.addEventListener('click', () => {
                const rating = label.getAttribute('for').slice(-1);
                updateStars(container, rating, 'selected');
            });
        });
    });
}

// Update star appearance
function updateStars(container, rating, state) {
    const labels = container.querySelectorAll('label');
    labels.forEach((label, index) => {
        if (state === 'hover') {
            label.style.color = index < rating ? '#ffd700' : '#ddd';
        } else {
            label.style.color = index < rating ? '#ffd700' : '#ddd';
        }
    });
}

// Function to populate provider dropdowns
async function loadProviderDropdowns() {
    try {
        const response = await fetch('/providers?type=all');
        const data = await response.json();

        // Populate healthcare providers dropdown
        const healthcareSelect = document.getElementById('healthcare-provider');
        healthcareSelect.innerHTML = '<option value="">Select a Healthcare Provider</option>' +
            data.healthcare.map(provider => `
                <option value="${provider}">${provider}</option>
            `).join('');

        // Populate insurance providers dropdown
        const insuranceSelect = document.getElementById('insurance-provider');
        insuranceSelect.innerHTML = '<option value="">Select an Insurance Provider</option>' +
            data.insurance.map(provider => `
                <option value="${provider}">${provider}</option>
            `).join('');
    } catch (error) {
        console.error('Error loading providers:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const locationBtn = document.getElementById('location-btn');
    const locationStatus = document.querySelector('.location-status');
    const cityOptions = document.querySelectorAll('.city-option');
    const useCurrentLocation = document.getElementById('use-current-location');
    let currentPosition = null;

    // Initialize star rating system and load provider dropdowns
    initializeStarRating();
    loadProviderDropdowns();
    loadReviews();
    updateProviderData(); // Initial load of provider data

    // Add click handlers for city options
    cityOptions.forEach(option => {
        option.addEventListener('click', function() {
            currentLocation = this.textContent.trim(); // Update current location
            updateLocationData(); // Update all location-based data
        });
    });

    function updateLocation(latitude, longitude, accuracy = null) {
        fetch('/update-location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    latitude,
                    longitude,
                    accuracy,
                    isManualSelection: accuracy === null
                })
            }).then(response => response.json())
            .then(data => {
                if (data.success) {
                    locationBtn.classList.add('active');
                    locationStatus.textContent = '✓';
                    console.log('Location updated successfully');
                }
            })
            .catch(error => {
                console.error('Error updating location:', error);
                locationStatus.textContent = '!';
            });
    }

    function handleLocationSuccess(position) {
        currentPosition = position;
        updateLocation(
            position.coords.latitude,
            position.coords.longitude,
            position.coords.accuracy
        );

        // Reverse geocoding to get city name
        fetch(`https://nominatim.openstreetmap.org/reverse?lat=${position.coords.latitude}&lon=${position.coords.longitude}&format=json`)
            .then(response => response.json())
            .then(data => {
                const city = data.address.city || data.address.town || data.address.village || 'Current Location';
                updateLocationLabel(city);
            })
            .catch(error => {
                console.error('Error getting location name:', error);
                updateLocationLabel('Current Location');
            });
    }

    function handleLocationError(error) {
        locationBtn.classList.remove('active');
        locationStatus.textContent = '!';
        console.error('Error getting location:', error);
        alert('Unable to get your location. Please make sure location services are enabled.');
    }

    const locationLabel = document.querySelector('.location-label');

    function updateLocationLabel(locationName) {
        if (locationLabel) {
            locationLabel.textContent = locationName;
        }
    }

    // Handle city selection
    cityOptions.forEach(city => {
        if (city.id !== 'use-current-location') {
            city.addEventListener('click', () => {
                const lat = parseFloat(city.dataset.lat);
                const lng = parseFloat(city.dataset.lng);
                updateLocation(lat, lng);
                updateLocationLabel(city.textContent);
            });
        }
    });

    // Handle current location button
    if (useCurrentLocation) {
        useCurrentLocation.addEventListener('click', () => {
            if (!navigator.geolocation) {
                alert('Location services are not supported by your browser');
                return;
            }

            locationStatus.textContent = '...';
            navigator.geolocation.getCurrentPosition(handleLocationSuccess, handleLocationError, {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            });
        });
    }

    // Handle main location button
    if (locationBtn) {
        locationBtn.addEventListener('click', () => {
            if (currentPosition) {
                // If we already have location, toggle it off
                currentPosition = null;
                locationBtn.classList.remove('active');
                locationStatus.textContent = '';
                updateLocationLabel('Select Location');
            }
        });
    }
});

// Medical Search Handler
document.addEventListener('DOMContentLoaded', () => {
            const searchForm = document.getElementById('searchForm');
            const searchInput = document.getElementById('searchInput');
            const searchTypeSelect = document.getElementById('searchType'); // may be removed
            const locationSelect = document.getElementById('locationSelect'); // optional
            const resultsContainer = document.getElementById('searchResults');
            const loadingSpinner = document.getElementById('loading-spinner');

            if (searchForm) {
                searchForm.addEventListener('submit', async(e) => {
                    e.preventDefault();

                    if (loadingSpinner) loadingSpinner.style.display = 'block';
                    if (resultsContainer) resultsContainer.style.display = 'none';

                    const searchData = {
                        query: searchInput ? searchInput.value : '',
                        type: searchTypeSelect ? searchTypeSelect.value : 'all',
                        location: locationSelect ? locationSelect.value : null
                    };

                    try {
                        const response = await fetch('/search', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(searchData)
                        });

                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }

                        const results = await response.json();
                        displayResults(results);
                    } catch (error) {
                        console.error('Search error:', error);
                        if (resultsContainer) {
                            resultsContainer.innerHTML = '<p class="error">An error occurred while searching. Please try again.</p>';
                            resultsContainer.style.display = 'block';
                        }
                    } finally {
                        if (loadingSpinner) loadingSpinner.style.display = 'none';
                    }
                });
            }

            function displayResults(results) {
                if (!resultsContainer) return;

                let html = '';

                if (results.error) {
                    html = `<p class="error">${results.error}</p>`;
                } else {
                    // Display clinics if any
                    if (results.clinics && results.clinics.length > 0) {
                        html += '<h2>Healthcare Providers</h2>';
                        html += '<div class="results-grid">';
                        results.clinics.forEach(clinic => {
                                    const specialties = clinic.specialties ? (Array.isArray(clinic.specialties) ? clinic.specialties.join(', ') : clinic.specialties) : 'General Practice';
                                    const insurance = clinic.insurance ? (Array.isArray(clinic.insurance) ? clinic.insurance.join(', ') : clinic.insurance) : 'Please inquire';
                                    const address = clinic.address || clinic.location || 'Address not available';
                                    const phone = clinic.phone || '';
                                    const website = clinic.website || clinic.url || '';
                                    const rating = clinic.rating ? `⭐ ${clinic.rating}` : '';
                                    const distance = clinic.distance ? ` • ${clinic.distance.toFixed(1)} mi away` : '';
                                    const suggestedFor = clinic.suggested_for ? `<p class="suggested"><em>Suggested for: ${clinic.suggested_for.join(', ')}</em></p>` : '';

                                    html += `
                        <div class="result-card ${clinic.relevance_score >= 8 ? 'high-relevance' : ''}">
                            <h3>${clinic.name} ${rating}${distance}</h3>
                            ${suggestedFor}
                            <p><strong>Location:</strong> ${address}</p>
                            ${phone ? `<p><strong>Phone:</strong> <a href="tel:${phone}">${phone}</a></p>` : ''}
                            <p><strong>Specialties:</strong> ${specialties}</p>
                            <p><strong>Accepted Insurance:</strong> ${insurance}</p>
                            ${website ? `<p><a href="${website}" target="_blank" rel="noopener" class="btn-link">Visit Website</a></p>` : ''}
                        </div>
                    `;
                        });
                        html += '</div>';
                    }

                    // Display insurance providers if any (enhanced)
                    if (results.insurance && results.insurance.length > 0) {
                        html += '<h2>Insurance Providers</h2>';
                        html += '<div class="results-grid">';
                        results.insurance.forEach(provider => {
                            const coverage = provider.coverage_types ? provider.coverage_types.join(', ') : (provider.coverage || 'Health insurance');
                            const website = provider.website || provider.url || null;
                            const phone = provider.phone || provider.contact || null;
                            const desc = provider.description || '';
                            html += `
                        <div class="result-card">
                            <h3>${provider.name}</h3>
                            ${desc ? `<p class="muted">${desc}</p>` : ''}
                            ${coverage ? `<p><strong>Coverage Types:</strong> ${coverage}</p>` : ''}
                            ${phone ? `<p><strong>Phone:</strong> <a href="tel:${phone}">${phone}</a></p>` : ''}
                            ${website ? `<p><a href="${website}" target="_blank" rel="noopener" class="btn-link">Visit Website</a></p>` : ''}
                        </div>
                    `;
                        });
                        html += '</div>';
                    }

                    // Display medical advice if any (enhanced)
                    if (results.medical_advice && results.medical_advice.possible_conditions && results.medical_advice.possible_conditions.length > 0) {
                        const urgency = results.medical_advice.urgency || 'routine';
                        const urgencyClass = urgency === 'emergency' ? 'urgency-emergency' : 
                                            urgency === 'urgent' ? 'urgency-urgent' : 
                                            urgency === 'moderate' ? 'urgency-moderate' : 'urgency-routine';
                        
                        html += '<h2>Medical Analysis</h2>';
                        html += `<div class="medical-advice ${urgencyClass}">`;
                        
                        // Urgency indicator
                        if (urgency === 'emergency') {
                            html += '<div class="urgency-badge emergency">⚠️ Emergency</div>';
                        } else if (urgency === 'urgent') {
                            html += '<div class="urgency-badge urgent">⚡ Urgent Care Recommended</div>';
                        } else if (urgency === 'moderate') {
                            html += '<div class="urgency-badge moderate">📅 Schedule Appointment</div>';
                        }
                        
                        // Matched symptoms
                        if (results.medical_advice.matched_symptoms && results.medical_advice.matched_symptoms.length > 0) {
                            html += `
                        <p><strong>Recognized Symptoms:</strong> ${results.medical_advice.matched_symptoms.join(', ')}</p>
                    `;
                        }
                        
                        // Possible conditions
                        if (results.medical_advice.possible_conditions) {
                            html += `
                        <p><strong>Possible Conditions:</strong> ${results.medical_advice.possible_conditions.join(', ')}</p>
                    `;
                        }
                        
                        // Confidence score
                        if (results.medical_advice.confidence_score) {
                            const confidence = Math.round(results.medical_advice.confidence_score * 100);
                            const confidenceClass = confidence >= 70 ? 'confidence-high' : confidence >= 40 ? 'confidence-medium' : 'confidence-low';
                            html += `
                        <p><strong>Analysis Confidence:</strong> <span class="${confidenceClass}">${confidence}%</span></p>
                    `;
                        }
                        
                        // Recommendation
                        if (results.medical_advice.recommendation) {
                            html += `
                        <div class="recommendation-box">
                            <p><strong>Recommendation:</strong></p>
                            <p>${results.medical_advice.recommendation}</p>
                        </div>
                    `;
                        }
                        
                        // Disclaimer
                        html += `
                    <div class="disclaimer">
                        ${results.medical_advice.disclaimer}
                    </div>
                </div>
                `;
                    }

                    // If no results found
                    if (!html) {
                        html = '<p>No results found for your search. Try different keywords or describe your symptoms in more detail.</p>';
                    }
                }

        resultsContainer.innerHTML = html;
        resultsContainer.style.display = 'block';
    }

    // Example question selector handler
    const exampleSelect = document.getElementById('example_question');
    const questionInput = document.getElementById('question_input');

    if (exampleSelect && questionInput) {
        exampleSelect.addEventListener('change', () => {
            questionInput.value = exampleSelect.value;
        });
    }
});