document.addEventListener('DOMContentLoaded', function() {
    const predictionForm = document.getElementById('prediction-form');
    const locationSelect = document.getElementById('location-select');
    const loadWeatherBtn = document.getElementById('load-weather-btn');
    const loadingSpinner = document.getElementById('loading-spinner');
    const predictionResult = document.getElementById('prediction-result');
    
    // Result elements
    const resRegion = document.getElementById('res-region');
    const resProbability = document.getElementById('res-probability');
    const resRiskLevel = document.getElementById('res-risk-level');
    const resOutcome = document.getElementById('res-outcome');
    const resRecommendation = document.getElementById('res-recommendation');
    const resReportBtn = document.getElementById('res-report-btn');
    const resAlertNotify = document.getElementById('res-alert-notify');
    const probRing = document.getElementById('prob-ring');
    
    // Autofill Weather Data from predefined cities
    if (loadWeatherBtn && locationSelect) {
        loadWeatherBtn.addEventListener('click', function() {
            const selectedCity = locationSelect.value;
            if (!selectedCity) {
                alert('Please select a location first.');
                return;
            }
            
            // Show loading animation on button
            const originalBtnText = loadWeatherBtn.innerHTML;
            loadWeatherBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching...';
            loadWeatherBtn.disabled = true;
            
            const formData = new FormData();
            formData.append('autofill_city', selectedCity);
            
            fetch('/predict', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(res => {
                loadWeatherBtn.innerHTML = originalBtnText;
                loadWeatherBtn.disabled = false;
                
                if (res.status === 'success') {
                    // Populate fields
                    const weather = res.data;
                    document.getElementById('region').value = selectedCity;
                    
                    for (const [key, value] of Object.entries(weather)) {
                        const inputElement = document.getElementById(key);
                        if (inputElement) {
                            inputElement.value = value;
                        }
                    }
                    
                    // Show a quick success alert
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-info alert-dismissible fade show mt-2';
                    alertDiv.innerHTML = `<strong>Success!</strong> Meteorological parameters populated for ${selectedCity}. <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
                    locationSelect.parentNode.appendChild(alertDiv);
                    
                    setTimeout(() => {
                        const bsAlert = new bootstrap.Alert(alertDiv);
                        bsAlert.close();
                    }, 5000);
                } else {
                    alert('Error loading weather parameters.');
                }
            })
            .catch(err => {
                loadWeatherBtn.innerHTML = originalBtnText;
                loadWeatherBtn.disabled = false;
                console.error(err);
                alert('Error connecting to local weather database.');
            });
        });
    }
    
    // Submit prediction form via AJAX
    if (predictionForm) {
        predictionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Clear previous results
            predictionResult.style.display = 'none';
            loadingSpinner.style.display = 'block';
            
            // Smooth scroll to loading section
            loadingSpinner.scrollIntoView({ behavior: 'smooth' });
            
            const formData = new FormData(predictionForm);
            
            fetch('/predict', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(res => {
                loadingSpinner.style.display = 'none';
                
                if (res.status === 'success') {
                    // Populate result data
                    resRegion.textContent = document.getElementById('region').value || 'Selected Location';
                    resProbability.textContent = res.probability;
                    resRiskLevel.textContent = `${res.risk_level} Risk`;
                    resOutcome.textContent = res.prediction;
                    resRecommendation.textContent = res.recommendation;
                    
                    // Dynamic color configurations
                    resRiskLevel.className = `risk-indicator risk-${res.risk_level.split(' ')[0]}`;
                    
                    // Color code probability circular ring
                    probRing.style.borderColor = res.color;
                    probRing.style.color = res.color;
                    
                    // Style Outcome color
                    if (res.prediction === 'Flood Likely') {
                        resOutcome.className = 'text-danger fw-bold';
                        probRing.className = 'result-prob-ring pulse-veryhigh';
                    } else {
                        resOutcome.className = 'text-success fw-bold';
                        probRing.className = 'result-prob-ring';
                    }
                    
                    // PDF Download link update
                    resReportBtn.href = `/export/pdf/${res.id}`;
                    
                    // Alert notifications info box
                    if (res.alert_sent) {
                        resAlertNotify.style.display = 'block';
                        resAlertNotify.innerHTML = `<i class="fas fa-paper-plane me-2"></i> <b>Regional Alert Triggered:</b> Dynamic notifications successfully broadcasted to local authorities and emergency channels.`;
                    } else {
                        resAlertNotify.style.display = 'none';
                    }
                    
                    // Display results
                    predictionResult.style.display = 'block';
                    predictionResult.scrollIntoView({ behavior: 'smooth' });
                } else {
                    // Show error modal or text
                    alert(`Validation Error: ${res.message}`);
                }
            })
            .catch(err => {
                loadingSpinner.style.display = 'none';
                console.error(err);
                alert('An error occurred while compiling the prediction.');
            });
        });
    }
});
