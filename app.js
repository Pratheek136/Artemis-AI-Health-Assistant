// AI Health Assistant Dashboard JavaScript

// Global variables
let currentUser = {
    id: 'user123',
    name: 'John Doe',
    age: 35,
    email: 'john.doe@example.com'
};

let healthData = {
    vitals: [],
    medications: [],
    insights: [],
    alerts: []
};

let chatHistory = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadDashboardData();
    setupEventListeners();
    startRealTimeUpdates();
});

// Initialize application
function initializeApp() {
    console.log('Initializing AI Health Assistant Dashboard...');
    
    // Set user name
    document.getElementById('userName').textContent = currentUser.name;
    
    // Initialize charts
    initializeCharts();
    
    // Load initial data
    loadVitalsData();
    loadMedications();
    loadInsights();
    
    console.log('Application initialized successfully');
}

// Setup event listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            showSection(section);
        });
    });
    
    // Chat input
    document.getElementById('chatInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Settings form
    document.getElementById('userNameInput').addEventListener('change', updateUserName);
    document.getElementById('userAge').addEventListener('change', updateUserAge);
    document.getElementById('userEmail').addEventListener('change', updateUserEmail);
}

// Show specific section
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active class from nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionName).classList.add('active');
    
    // Add active class to nav item
    document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
    
    // Load section-specific data
    switch(sectionName) {
        case 'vitals':
            loadVitalsData();
            break;
        case 'medications':
            loadMedications();
            break;
        case 'insights':
            loadInsights();
            break;
        case 'chat':
            loadChatHistory();
            break;
    }
}

// Load dashboard data
function loadDashboardData() {
    // Simulate loading health data
    setTimeout(() => {
        updateHealthScore(85);
        updateCurrentVitals();
        updateAlerts();
    }, 1000);
}

// Update health score
function updateHealthScore(score) {
    const scoreElement = document.getElementById('healthScore');
    const statusElement = document.getElementById('healthStatus');
    
    scoreElement.textContent = score;
    
    if (score >= 90) {
        statusElement.textContent = 'Excellent';
        statusElement.className = 'score-status text-success';
    } else if (score >= 80) {
        statusElement.textContent = 'Good';
        statusElement.className = 'score-status text-success';
    } else if (score >= 70) {
        statusElement.textContent = 'Fair';
        statusElement.className = 'score-status text-warning';
    } else if (score >= 60) {
        statusElement.textContent = 'Poor';
        statusElement.className = 'score-status text-warning';
    } else {
        statusElement.textContent = 'Critical';
        statusElement.className = 'score-status text-danger';
    }
}

// Update current vitals
function updateCurrentVitals() {
    // Simulate real-time vitals data
    const vitals = {
        heartRate: 72 + Math.floor(Math.random() * 10) - 5,
        systolicBP: 120 + Math.floor(Math.random() * 10) - 5,
        diastolicBP: 80 + Math.floor(Math.random() * 5) - 2,
        temperature: 98.6 + (Math.random() * 0.4) - 0.2,
        oxygenSaturation: 98 + Math.floor(Math.random() * 3) - 1
    };
    
    document.getElementById('currentHeartRate').textContent = vitals.heartRate;
    document.getElementById('currentBP').textContent = `${vitals.systolicBP}/${vitals.diastolicBP}`;
    document.getElementById('currentTemp').textContent = vitals.temperature.toFixed(1);
    document.getElementById('currentO2').textContent = vitals.oxygenSaturation;
    
    // Update last updated time
    document.getElementById('lastUpdated').textContent = 'Just now';
}

// Update alerts
function updateAlerts() {
    const alertsList = document.getElementById('alertsList');
    
    // Simulate alerts
    const alerts = [
        {
            type: 'info',
            title: 'Health data synced',
            time: '2 minutes ago',
            icon: 'fas fa-sync-alt'
        },
        {
            type: 'warning',
            title: 'Medication reminder: Metformin due in 15 minutes',
            time: '5 minutes ago',
            icon: 'fas fa-pills'
        },
        {
            type: 'info',
            title: 'Weekly health report generated',
            time: '1 hour ago',
            icon: 'fas fa-chart-line'
        }
    ];
    
    alertsList.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.type}">
            <i class="${alert.icon}"></i>
            <div class="alert-content">
                <div class="alert-title">${alert.title}</div>
                <div class="alert-time">${alert.time}</div>
            </div>
        </div>
    `).join('');
}

// Initialize charts
function initializeCharts() {
    // Heart Rate Chart
    const heartRateCtx = document.getElementById('heartRateChart').getContext('2d');
    new Chart(heartRateCtx, {
        type: 'line',
        data: {
            labels: generateTimeLabels(24),
            datasets: [{
                label: 'Heart Rate (bpm)',
                data: generateRandomData(24, 65, 85),
                borderColor: '#ff6b6b',
                backgroundColor: 'rgba(255, 107, 107, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Heart Rate Trend (24 hours)'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 60,
                    max: 100
                }
            }
        }
    });
    
    // Blood Pressure Chart
    const bpCtx = document.getElementById('bloodPressureChart').getContext('2d');
    new Chart(bpCtx, {
        type: 'line',
        data: {
            labels: generateTimeLabels(24),
            datasets: [
                {
                    label: 'Systolic BP',
                    data: generateRandomData(24, 110, 130),
                    borderColor: '#4834d4',
                    backgroundColor: 'rgba(72, 52, 212, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Diastolic BP',
                    data: generateRandomData(24, 70, 85),
                    borderColor: '#686de0',
                    backgroundColor: 'rgba(104, 109, 224, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Blood Pressure Trend (24 hours)'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 60,
                    max: 140
                }
            }
        }
    });
    
    // Temperature Chart
    const tempCtx = document.getElementById('temperatureChart').getContext('2d');
    new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: generateTimeLabels(24),
            datasets: [{
                label: 'Temperature (°F)',
                data: generateRandomData(24, 97.5, 99.5),
                borderColor: '#f093fb',
                backgroundColor: 'rgba(240, 147, 251, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Temperature Trend (24 hours)'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 97,
                    max: 100
                }
            }
        }
    });
    
    // Oxygen Saturation Chart
    const o2Ctx = document.getElementById('oxygenChart').getContext('2d');
    new Chart(o2Ctx, {
        type: 'line',
        data: {
            labels: generateTimeLabels(24),
            datasets: [{
                label: 'Oxygen Saturation (%)',
                data: generateRandomData(24, 95, 100),
                borderColor: '#4facfe',
                backgroundColor: 'rgba(79, 172, 254, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Oxygen Saturation Trend (24 hours)'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 94,
                    max: 100
                }
            }
        }
    });
}

// Generate time labels for charts
function generateTimeLabels(hours) {
    const labels = [];
    const now = new Date();
    
    for (let i = hours - 1; i >= 0; i--) {
        const time = new Date(now.getTime() - (i * 60 * 60 * 1000));
        labels.push(time.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
        }));
    }
    
    return labels;
}

// Generate random data for charts
function generateRandomData(count, min, max) {
    const data = [];
    for (let i = 0; i < count; i++) {
        data.push(Math.random() * (max - min) + min);
    }
    return data;
}

// Load vitals data
function loadVitalsData() {
    console.log('Loading vitals data...');
    
    // Simulate API call
    setTimeout(() => {
        // Update charts with new data
        updateCharts();
        console.log('Vitals data loaded');
    }, 500);
}

// Update charts with new data
function updateCharts() {
    // This would typically update the charts with new data from the API
    console.log('Updating charts with new data...');
}

// Load medications
function loadMedications() {
    console.log('Loading medications...');
    
    // Simulate medications data
    const medications = [
        {
            id: 'med1',
            name: 'Metformin',
            dosage: '500mg',
            frequency: 'Twice daily',
            lastTaken: '2 hours ago',
            adherenceRate: 95
        },
        {
            id: 'med2',
            name: 'Lisinopril',
            dosage: '10mg',
            frequency: 'Once daily',
            lastTaken: '6 hours ago',
            adherenceRate: 98
        },
        {
            id: 'med3',
            name: 'Atorvastatin',
            dosage: '20mg',
            frequency: 'Once daily',
            lastTaken: '8 hours ago',
            adherenceRate: 92
        }
    ];
    
    const medicationsList = document.getElementById('medicationsList');
    medicationsList.innerHTML = medications.map(med => `
        <div class="medication-card">
            <div class="medication-info">
                <h4>${med.name}</h4>
                <div class="medication-details">
                    ${med.dosage} • ${med.frequency} • Last taken: ${med.lastTaken}
                </div>
                <div class="medication-details">
                    Adherence: ${med.adherenceRate}%
                </div>
            </div>
            <div class="medication-actions">
                <button class="btn btn-success" onclick="logDose('${med.id}')">
                    <i class="fas fa-check"></i>
                    Log Dose
                </button>
                <button class="btn btn-secondary" onclick="editMedication('${med.id}')">
                    <i class="fas fa-edit"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    // Load reminders
    loadReminders();
}

// Load reminders
function loadReminders() {
    const reminders = [
        {
            medication: 'Metformin',
            time: 'In 15 minutes',
            isOverdue: false
        },
        {
            medication: 'Lisinopril',
            time: 'In 2 hours',
            isOverdue: false
        }
    ];
    
    const remindersList = document.getElementById('remindersList');
    remindersList.innerHTML = reminders.map(reminder => `
        <div class="reminder-item">
            <div class="reminder-info">
                <div class="reminder-medication">${reminder.medication}</div>
                <div class="reminder-time">${reminder.time}</div>
            </div>
            <button class="btn btn-primary btn-sm" onclick="snoozeReminder('${reminder.medication}')">
                Snooze
            </button>
        </div>
    `).join('');
}

// Load insights
function loadInsights() {
    console.log('Loading insights...');
    
    const insights = [
        {
            type: 'info',
            title: 'Heart Rate Analysis',
            message: 'Your heart rate has been stable over the past week, averaging 72 bpm.',
            recommendation: 'Continue your current exercise routine to maintain cardiovascular health.'
        },
        {
            type: 'warning',
            title: 'Blood Pressure Trend',
            message: 'Your blood pressure has been slightly elevated recently.',
            recommendation: 'Consider reducing sodium intake and increasing physical activity.'
        },
        {
            type: 'info',
            title: 'Medication Adherence',
            message: 'Excellent medication adherence at 95% overall.',
            recommendation: 'Keep up the great work with your medication schedule.'
        }
    ];
    
    const insightsContent = document.getElementById('insightsContent');
    insightsContent.innerHTML = insights.map(insight => `
        <div class="insight-card">
            <div class="insight-header">
                <span class="insight-type ${insight.type}">${insight.type.toUpperCase()}</span>
                <h4>${insight.title}</h4>
            </div>
            <p>${insight.message}</p>
            <div class="insight-recommendation">
                <strong>Recommendation:</strong> ${insight.recommendation}
            </div>
        </div>
    `).join('');
}

// Load chat history
function loadChatHistory() {
    console.log('Loading chat history...');
    
    // Chat history is already initialized in HTML
    // This would typically load from a database
}

// Send chat message
function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Clear input
    input.value = '';
    
    // Simulate AI response
    setTimeout(() => {
        const response = generateAIResponse(message);
        addMessageToChat('assistant', response);
    }, 1000);
}

// Add message to chat
function addMessageToChat(sender, text) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas ${sender === 'user' ? 'fa-user' : 'fa-robot'}"></i>
        </div>
        <div class="message-content">
            <div class="message-text">${text}</div>
            <div class="message-time">${timeString}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Generate AI response
function generateAIResponse(userMessage) {
    const message = userMessage.toLowerCase();
    
    if (message.includes('heart rate') || message.includes('heart')) {
        return "Your current heart rate is 72 bpm, which is within the normal range for your age. Your heart rate has been stable over the past week. Is there anything specific about your heart health you'd like to discuss?";
    } else if (message.includes('blood pressure') || message.includes('pressure')) {
        return "Your blood pressure is currently 120/80 mmHg, which is in the normal range. However, I've noticed a slight upward trend recently. I recommend monitoring your sodium intake and maintaining regular exercise.";
    } else if (message.includes('medication') || message.includes('medicine')) {
        return "You have 3 active medications with excellent adherence rates. Your next medication reminder is for Metformin in 15 minutes. Would you like me to help you with any medication-related questions?";
    } else if (message.includes('exercise') || message.includes('workout')) {
        return "Regular exercise is great for your cardiovascular health. Based on your current vitals, I recommend 30 minutes of moderate exercise most days of the week. Always consult with your healthcare provider before starting a new exercise routine.";
    } else if (message.includes('diet') || message.includes('food') || message.includes('eating')) {
        return "A balanced diet is essential for maintaining good health. Given your blood pressure trends, I recommend reducing sodium intake and increasing fruits, vegetables, and whole grains. Would you like specific dietary recommendations?";
    } else if (message.includes('sleep') || message.includes('tired')) {
        return "Quality sleep is crucial for overall health. Aim for 7-9 hours of sleep per night. Poor sleep can affect your heart rate and blood pressure. Are you experiencing any sleep issues?";
    } else if (message.includes('stress') || message.includes('anxiety')) {
        return "Stress management is important for your health. High stress can impact your heart rate and blood pressure. Consider relaxation techniques like deep breathing, meditation, or gentle exercise. Would you like some stress management tips?";
    } else if (message.includes('emergency') || message.includes('urgent') || message.includes('help')) {
        return "If you're experiencing a medical emergency, please call 911 immediately. For non-emergency health concerns, I can provide general information, but always consult with your healthcare provider for medical advice.";
    } else {
        return "I'm here to help with your health questions. I can provide information about your vitals, medications, and general health topics. What would you like to know more about?";
    }
}

// Medication functions
function showAddMedicationModal() {
    document.getElementById('addMedicationModal').style.display = 'block';
}

function closeAddMedicationModal() {
    document.getElementById('addMedicationModal').style.display = 'none';
}

function addMedication() {
    const name = document.getElementById('medName').value;
    const dosage = document.getElementById('medDosage').value;
    const frequency = document.getElementById('medFrequency').value;
    const instructions = document.getElementById('medInstructions').value;
    
    if (!name || !dosage || !frequency) {
        alert('Please fill in all required fields.');
        return;
    }
    
    // Simulate adding medication
    console.log('Adding medication:', { name, dosage, frequency, instructions });
    
    // Close modal and refresh medications
    closeAddMedicationModal();
    loadMedications();
    
    // Show success message
    showNotification('Medication added successfully!', 'success');
}

function logDose(medicationId) {
    console.log('Logging dose for medication:', medicationId);
    
    // Simulate logging dose
    showNotification('Dose logged successfully!', 'success');
    
    // Refresh medications
    loadMedications();
}

function editMedication(medicationId) {
    console.log('Editing medication:', medicationId);
    // This would open an edit modal
    showNotification('Edit functionality coming soon!', 'info');
}

function snoozeReminder(medication) {
    console.log('Snoozing reminder for:', medication);
    showNotification(`Reminder for ${medication} snoozed for 30 minutes`, 'info');
}

// Insights functions
function generateInsights() {
    console.log('Generating new insights...');
    
    // Show loading state
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    button.disabled = true;
    
    // Simulate API call
    setTimeout(() => {
        loadInsights();
        button.innerHTML = originalText;
        button.disabled = false;
        showNotification('New insights generated!', 'success');
    }, 2000);
}

// Settings functions
function updateUserName() {
    const newName = document.getElementById('userNameInput').value;
    currentUser.name = newName;
    document.getElementById('userName').textContent = newName;
}

function updateUserAge() {
    const newAge = document.getElementById('userAge').value;
    currentUser.age = parseInt(newAge);
}

function updateUserEmail() {
    const newEmail = document.getElementById('userEmail').value;
    currentUser.email = newEmail;
}

function saveSettings() {
    console.log('Saving settings...');
    
    // Update user object
    currentUser.name = document.getElementById('userNameInput').value;
    currentUser.age = parseInt(document.getElementById('userAge').value);
    currentUser.email = document.getElementById('userEmail').value;
    
    // Simulate saving
    showNotification('Settings saved successfully!', 'success');
}

// Utility functions
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        animation: slideIn 0.3s ease-out;
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function refreshVitals() {
    console.log('Refreshing vitals...');
    
    // Show loading state
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    button.disabled = true;
    
    // Simulate refresh
    setTimeout(() => {
        updateCurrentVitals();
        updateCharts();
        button.innerHTML = originalText;
        button.disabled = false;
        showNotification('Vitals refreshed!', 'success');
    }, 1000);
}

// Start real-time updates
function startRealTimeUpdates() {
    // Update vitals every 30 seconds
    setInterval(() => {
        updateCurrentVitals();
    }, 30000);
    
    // Update health score every 5 minutes
    setInterval(() => {
        const newScore = 85 + Math.floor(Math.random() * 10) - 5;
        updateHealthScore(newScore);
    }, 300000);
    
    // Update last updated time
    setInterval(() => {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        document.getElementById('lastUpdated').textContent = timeString;
    }, 60000);
}

// Emergency functions
function triggerEmergencyAlert() {
    if (confirm('Are you sure you want to trigger an emergency alert? This will notify your emergency contacts and healthcare provider.')) {
        console.log('Emergency alert triggered');
        showNotification('Emergency alert sent! Help is on the way.', 'error');
        
        // This would typically call the emergency alerts API
        // fetch('/api/emergency', { method: 'POST', body: JSON.stringify({ type: 'panic' }) });
    }
}

// Export functions for global access
window.showSection = showSection;
window.refreshVitals = refreshVitals;
window.showAddMedicationModal = showAddMedicationModal;
window.closeAddMedicationModal = closeAddMedicationModal;
window.addMedication = addMedication;
window.logDose = logDose;
window.editMedication = editMedication;
window.snoozeReminder = snoozeReminder;
window.generateInsights = generateInsights;
window.saveSettings = saveSettings;
window.sendMessage = sendMessage;
window.triggerEmergencyAlert = triggerEmergencyAlert;
