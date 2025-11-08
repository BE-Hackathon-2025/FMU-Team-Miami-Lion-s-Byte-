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

// Location Services Handler
document.addEventListener('DOMContentLoaded', () => {
    const locationBtn = document.getElementById('location-btn');
    const locationStatus = document.querySelector('.location-status');
    const cityOptions = document.querySelectorAll('.city-option');
    const useCurrentLocation = document.getElementById('use-current-location');
    let currentPosition = null;

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
                html += '<h2>Clinics</h2>';
                html += '<div class="results-grid">';
                results.clinics.forEach(clinic => {
                    html += `
                        <div class="result-card">
                            <h3>${clinic.name}</h3>
                            <p><strong>Location:</strong> ${clinic.location}</p>
                            <p><strong>Specialties:</strong> ${clinic.specialties.join(', ')}</p>
                            <p><strong>Accepted Insurance:</strong> ${clinic.insurance.join(', ')}</p>
                        </div>
                    `;
                });
                html += '</div>';
            }

            // Display insurance providers if any
            if (results.insurance && results.insurance.length > 0) {
                html += '<h2>Insurance Providers</h2>';
                html += '<div class="results-grid">';
                results.insurance.forEach(provider => {
                    html += `
                        <div class="result-card">
                            <h3>${provider.name}</h3>
                            <p><strong>Coverage Types:</strong> ${provider.coverage_types.join(', ')}</p>
                        </div>
                    `;
                });
                html += '</div>';
            }

            // Display medical advice if any
            if (results.medical_advice) {
                html += '<h2>Medical Analysis</h2>';
                html += '<div class="medical-advice">';
                if (results.medical_advice.possible_conditions) {
                    html += `
                        <p><strong>Possible Conditions:</strong> ${results.medical_advice.possible_conditions.join(', ')}</p>
                    `;
                }
                if (results.medical_advice.confidence_score) {
                    html += `
                        <p><strong>Analysis Confidence:</strong> ${Math.round(results.medical_advice.confidence_score * 100)}%</p>
                    `;
                }
                if (results.medical_advice.recommendation) {
                    html += `
                        <p><strong>Recommendation:</strong> ${results.medical_advice.recommendation}</p>
                    `;
                }
                html += `
                    <div class="disclaimer">
                        ${results.medical_advice.disclaimer}
                    </div>
                </div>
                `;
            }

            // If no results found
            if (!html) {
                html = '<p>No results found for your search.</p>';
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