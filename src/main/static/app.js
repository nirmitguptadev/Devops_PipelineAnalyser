// Global variables
let categoryChart = null;
let trendChart = null;
let currentPlatform = 'jenkins';
let lastFailureId = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeCIPlatformSelector();
    loadStats();
    loadFailures();
    startLiveUpdates();
});

// Start live updates
function startLiveUpdates() {
    // Check for new failures every 10 seconds
    setInterval(checkNewFailures, 10000);
    // Refresh stats every 30 seconds
    setInterval(loadStats, 30000);
    // Refresh failures table every 30 seconds
    setInterval(loadFailures, 30000);
}

// Check for new failures and show in activity feed
async function checkNewFailures() {
    try {
        const response = await fetch('/api/failures?limit=1');
        const failures = await response.json();
        
        if (failures.length > 0) {
            const latestFailure = failures[0];
            if (latestFailure.id > lastFailureId) {
                lastFailureId = latestFailure.id;
                addToActivityFeed(latestFailure);
                showNotification('New Failure Detected', latestFailure.pipeline_name);
                loadStats();
                loadFailures();
            }
        }
    } catch (error) {
        console.error('Failed to check new failures:', error);
    }
}

// Add failure to activity feed
function addToActivityFeed(failure) {
    const feed = document.getElementById('activityFeed');
    
    // Remove placeholder if exists
    if (feed.querySelector('.text-muted')) {
        feed.innerHTML = '';
    }
    
    const severityColors = {
        critical: 'danger',
        high: 'warning',
        medium: 'info',
        low: 'secondary'
    };
    
    const platformIcons = {
        jenkins: 'fab fa-jenkins',
        github: 'fab fa-github',
        gitlab: 'fab fa-gitlab'
    };
    
    const activityItem = document.createElement('div');
    activityItem.className = 'alert alert-' + severityColors[failure.severity] + ' mb-3 fade-in';
    activityItem.style.cursor = 'pointer';
    activityItem.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div class="flex-grow-1">
                <h6 class="mb-2">
                    <i class="${platformIcons[failure.ci_platform] || 'fas fa-server'}"></i>
                    ${failure.pipeline_name}
                    <span class="badge bg-${severityColors[failure.severity]} ms-2">${failure.severity}</span>
                </h6>
                <p class="mb-2"><strong>Category:</strong> ${failure.category.replace('_', ' ')}</p>
                <p class="mb-0"><strong>Root Cause:</strong> ${failure.root_cause}</p>
                <small class="text-muted d-block mt-2">
                    <i class="fas fa-clock"></i> ${new Date(failure.timestamp).toLocaleString()}
                </small>
            </div>
        </div>
    `;
    
    // Click to show AI summary
    activityItem.addEventListener('click', () => {
        showAISummary(failure);
        // Highlight selected
        document.querySelectorAll('#activityFeed .alert').forEach(a => a.style.opacity = '0.6');
        activityItem.style.opacity = '1';
    });
    
    // Add to top of feed
    feed.insertBefore(activityItem, feed.firstChild);
    
    // Keep only last 10 items
    while (feed.children.length > 10) {
        feed.removeChild(feed.lastChild);
    }
    
    // Auto-show AI summary for the first failure
    if (feed.children.length === 1) {
        showAISummary(failure);
    }
}

// Show AI summary in dedicated card
function showAISummary(failure) {
    const summaryCard = document.getElementById('aiSummaryCard');
    
    // Parse troubleshooting if it's a JSON string
    let troubleshooting = [];
    if (failure.troubleshooting) {
        try {
            troubleshooting = typeof failure.troubleshooting === 'string' 
                ? JSON.parse(failure.troubleshooting) 
                : failure.troubleshooting;
        } catch (e) {
            console.error('Failed to parse troubleshooting:', e);
        }
    }
    
    const severityColors = {
        critical: 'danger',
        high: 'warning',
        medium: 'info',
        low: 'secondary'
    };
    
    if (failure.ai_insights || troubleshooting.length > 0) {
        summaryCard.innerHTML = `
            <div class="d-flex align-items-center gap-2 mb-3">
                <span class="badge bg-${severityColors[failure.severity]}">${failure.severity}</span>
                <span class="badge bg-secondary">${failure.category.replace('_', ' ')}</span>
            </div>
            <p class="fw-semibold mb-3" style="font-size:0.95rem;color:#111827;">${failure.pipeline_name}</p>

            <div class="analysis-box">
                ${failure.ai_insights ? `
                    <p class="analysis-section-label">Core Problem</p>
                    <p class="analysis-problem">${failure.ai_insights}</p>
                ` : ''}
                ${troubleshooting.length > 0 ? `
                    <p class="analysis-section-label">How to Fix</p>
                    <ul class="fix-list">
                        ${troubleshooting.map((step, i) => `
                            <li><span class="step-num">${i + 1}</span><span>${step}</span></li>
                        `).join('')}
                    </ul>
                ` : ''}
            </div>

            <p class="mt-3 mb-0" style="font-size:0.75rem;color:#9ca3af;">
                <i class="fas fa-clock me-1"></i>${new Date(failure.timestamp).toLocaleString()}
            </p>
        `;
    } else {
        summaryCard.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-circle-info" style="color:#d1d5db;"></i>
                <p style="color:#6b7280;">No analysis available for this failure</p>
            </div>
        `;
    }
}

// Show browser notification
function showNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: body,
            icon: '/static/icon.png'
        });
    } else if ('Notification' in window && Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification(title, { body: body });
            }
        });
    }
}

// CI Platform Selector
function initializeCIPlatformSelector() {
    document.querySelectorAll('.ci-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.ci-option').forEach(o => o.classList.remove('active'));
            this.classList.add('active');
            currentPlatform = this.dataset.platform;
            document.getElementById('ciPlatform').value = currentPlatform;
        });
    });
}

// Form submission
document.getElementById('analyzeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const btn = e.target.querySelector('button[type="submit"]');
    btn.classList.add('loading');
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                pipeline_name: document.getElementById('pipelineName').value,
                log_content: document.getElementById('logContent').value,
                ci_platform: document.getElementById('ciPlatform').value,
                use_ai: document.getElementById('useAI').checked
            })
        });
        
        const result = await response.json();
        displayResult(result);
        loadFailures();
        loadStats();
    } catch (error) {
        showError('Analysis failed: ' + error.message);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
});

function displayResult(result) {
    // Add to activity feed instead of result area
    addToActivityFeed(result);
}

function showError(message) {
    document.getElementById('resultArea').innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `;
}

async function loadFailures() {
    try {
        const response = await fetch('/api/failures?limit=10');
        const failures = await response.json();
        
        window.recentFailuresData = failures;
        const tbody = document.getElementById('failuresTable');
        
        tbody.innerHTML = failures.map((f, i) => {
            const severityColors = {
                critical: 'danger',
                high: 'warning',
                medium: 'info',
                low: 'secondary'
            };
            
            const platformIcons = {
                jenkins: 'fab fa-jenkins',
                github: 'fab fa-github',
                gitlab: 'fab fa-gitlab'
            };
            
            return `
                <tr style="cursor: pointer;" onclick='showAISummary(window.recentFailuresData[${i}])' class="clickable-row">
                    <td>${f.pipeline_name}</td>
                    <td><span class="badge bg-secondary">${f.category.replace('_', ' ')}</span></td>
                    <td><span class="badge bg-${severityColors[f.severity]}">${f.severity}</span></td>
                    <td><i class="${platformIcons[f.ci_platform] || 'fas fa-server'}"></i> ${f.ci_platform || 'jenkins'}</td>
                    <td>${new Date(f.timestamp).toLocaleString()}</td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load failures:', error);
    }
}

// Download report
async function downloadReport(format) {
    try {
        const response = await fetch('/api/report/download', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                type: format,
                date_range: 7
            })
        });
        
        if (format === 'json') {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `pipeline_report_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `pipeline_report_${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }
    } catch (error) {
        console.error('Failed to download report:', error);
        alert('Failed to generate report. Please try again.');
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // Update stat cards
        document.getElementById('totalFailures').textContent = stats.total_failures || 0;
        document.getElementById('criticalCount').textContent = stats.by_severity?.critical || 0;
        
        if (stats.avg_mttr_minutes != null) {
            const m = stats.avg_mttr_minutes;
            document.getElementById('avgMTTR').textContent = m >= 60
                ? `${Math.floor(m / 60)}h ${Math.round(m % 60)}m`
                : `${Math.round(m)}m`;
        } else {
            document.getElementById('avgMTTR').textContent = 'N/A';
        }
        
        document.getElementById('successRate').textContent = stats.success_rate != null
            ? `${stats.success_rate}%`
            : 'N/A';
        
        // Update category chart
        updateCategoryChart(stats.by_category);
        
        // Update trend chart
        updateTrendChart(stats.weekly_trend);
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

function updateCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data).map(k => k.replace('_', ' ').toUpperCase()),
            datasets: [{
                data: Object.values(data),
                backgroundColor: [
                    '#e74c3c',
                    '#f39c12',
                    '#3498db',
                    '#27ae60',
                    '#9b59b6'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { 
                        color: '#2c3e50',
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

function updateTrendChart(data) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (trendChart) {
        trendChart.destroy();
    }
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: 'Failures',
                data: Object.values(data),
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.4,
                fill: true,
                borderWidth: 2,
                pointBackgroundColor: '#3498db',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { 
                        color: '#2c3e50',
                        font: { size: 12 }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { 
                        color: '#7f8c8d',
                        font: { size: 11 }
                    },
                    grid: { color: 'rgba(149, 165, 166, 0.1)' }
                },
                x: {
                    ticks: { 
                        color: '#7f8c8d',
                        font: { size: 11 }
                    },
                    grid: { color: 'rgba(149, 165, 166, 0.1)' }
                }
            }
        }
    });
}
