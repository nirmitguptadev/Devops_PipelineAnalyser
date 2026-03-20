// Load current settings on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    checkAllStatuses();
});

// Load saved settings
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        // Jenkins
        if (settings.jenkins) {
            document.getElementById('jenkinsUrl').value = settings.jenkins.url || '';
            document.getElementById('jenkinsUser').value = settings.jenkins.user || '';
            document.getElementById('jenkinsPollInterval').value = settings.jenkins.poll_interval || 300;
        }
        
        // GitHub
        if (settings.github) {
            document.getElementById('githubOwner').value = settings.github.owner || '';
            document.getElementById('githubRepo').value = settings.github.repo || '';
        }
        
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

// Check all integration statuses
async function checkAllStatuses() {
    checkJenkinsStatus();
    checkGitHubStatus();
    checkGroqStatus();
}

// Jenkins Status
async function checkJenkinsStatus() {
    try {
        const response = await fetch('/api/settings/jenkins/status');
        const data = await response.json();
        updateStatusBadge('jenkinsStatus', data.connected, data.message);
    } catch (error) {
        updateStatusBadge('jenkinsStatus', false, 'Not configured');
    }
}

// GitHub Status
async function checkGitHubStatus() {
    try {
        const response = await fetch('/api/settings/github/status');
        const data = await response.json();
        updateStatusBadge('githubStatus', data.connected, data.message);
    } catch (error) {
        updateStatusBadge('githubStatus', false, 'Not configured');
    }
}

// Groq Status
async function checkGroqStatus() {
    try {
        const response = await fetch('/api/settings/groq/status');
        const data = await response.json();
        updateStatusBadge('groqStatus', data.connected, data.message);
    } catch (error) {
        updateStatusBadge('groqStatus', false, 'Not configured');
    }
}

// Update status badge
function updateStatusBadge(elementId, connected, message) {
    const badge = document.getElementById(elementId);
    if (connected) {
        badge.className = 'status-badge status-connected';
        badge.innerHTML = `<i class="fas fa-check-circle"></i> Connected`;
    } else {
        badge.className = 'status-badge status-disconnected';
        badge.innerHTML = `<i class="fas fa-times-circle"></i> ${message || 'Disconnected'}`;
    }
}

// Jenkins Form Submit
document.getElementById('jenkinsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        url: document.getElementById('jenkinsUrl').value,
        user: document.getElementById('jenkinsUser').value,
        token: document.getElementById('jenkinsToken').value,
        poll_interval: parseInt(document.getElementById('jenkinsPollInterval').value)
    };
    
    try {
        const response = await fetch('/api/settings/jenkins', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('jenkinsTestResult', 'success', 
                '<i class="fas fa-check-circle"></i> Jenkins integration saved and enabled!');
            // Mark connection time so dashboard only shows failures from this point
            localStorage.setItem('jenkins_connected_at', Date.now());
            localStorage.removeItem('dashboard_baseline_id');
            checkJenkinsStatus();
        } else {
            showAlert('jenkinsTestResult', 'danger', 
                '<i class="fas fa-exclamation-triangle"></i> ' + result.error);
        }
    } catch (error) {
        showAlert('jenkinsTestResult', 'danger', 
            '<i class="fas fa-exclamation-triangle"></i> Failed to save: ' + error.message);
    }
});

// GitHub Form Submit
document.getElementById('githubForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        token: document.getElementById('githubToken').value,
        owner: document.getElementById('githubOwner').value,
        repo: document.getElementById('githubRepo').value
    };
    
    try {
        const response = await fetch('/api/settings/github', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('githubTestResult', 'success', 
                '<i class="fas fa-check-circle"></i> GitHub integration saved and enabled!');
            checkGitHubStatus();
        } else {
            showAlert('githubTestResult', 'danger', 
                '<i class="fas fa-exclamation-triangle"></i> ' + result.error);
        }
    } catch (error) {
        showAlert('githubTestResult', 'danger', 
            '<i class="fas fa-exclamation-triangle"></i> Failed to save: ' + error.message);
    }
});

// Groq Form Submit
document.getElementById('groqForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        api_key: document.getElementById('groqApiKey').value
    };
    
    try {
        const response = await fetch('/api/settings/groq', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('groqTestResult', 'success', 
                '<i class="fas fa-check-circle"></i> Groq AI integration saved and enabled!');
            checkGroqStatus();
        } else {
            showAlert('groqTestResult', 'danger', 
                '<i class="fas fa-exclamation-triangle"></i> ' + result.error);
        }
    } catch (error) {
        showAlert('groqTestResult', 'danger', 
            '<i class="fas fa-exclamation-triangle"></i> Failed to save: ' + error.message);
    }
});

// Test Jenkins Connection
async function testJenkinsConnection() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    
    const data = {
        url: document.getElementById('jenkinsUrl').value,
        user: document.getElementById('jenkinsUser').value,
        token: document.getElementById('jenkinsToken').value
    };
    
    try {
        const response = await fetch('/api/settings/jenkins/test', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('jenkinsTestResult', 'success', 
                `<i class="fas fa-check-circle"></i> Connection successful! Found ${result.jobs_count} jobs.`);
        } else {
            showAlert('jenkinsTestResult', 'danger', 
                `<i class="fas fa-times-circle"></i> ${result.error}`);
        }
    } catch (error) {
        showAlert('jenkinsTestResult', 'danger', 
            '<i class="fas fa-times-circle"></i> Connection failed: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-plug"></i> Test Connection';
    }
}

// Test GitHub Connection
async function testGitHubConnection() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    
    const data = {
        token: document.getElementById('githubToken').value,
        owner: document.getElementById('githubOwner').value,
        repo: document.getElementById('githubRepo').value
    };
    
    try {
        const response = await fetch('/api/settings/github/test', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('githubTestResult', 'success', 
                `<i class="fas fa-check-circle"></i> Connection successful! User: ${result.username}`);
        } else {
            showAlert('githubTestResult', 'danger', 
                `<i class="fas fa-times-circle"></i> ${result.error}`);
        }
    } catch (error) {
        showAlert('githubTestResult', 'danger', 
            '<i class="fas fa-times-circle"></i> Connection failed: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-plug"></i> Test Connection';
    }
}

// Test Groq Connection
async function testGroqConnection() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    
    const data = {
        api_key: document.getElementById('groqApiKey').value
    };
    
    try {
        const response = await fetch('/api/settings/groq/test', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('groqTestResult', 'success', 
                '<i class="fas fa-check-circle"></i> Connection successful! AI analysis ready.');
        } else {
            showAlert('groqTestResult', 'danger', 
                `<i class="fas fa-times-circle"></i> ${result.error}`);
        }
    } catch (error) {
        showAlert('groqTestResult', 'danger', 
            '<i class="fas fa-times-circle"></i> Connection failed: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-plug"></i> Test Connection';
    }
}

// Disable integrations
async function disableJenkins() {
    if (confirm('Disable Jenkins integration?')) {
        await fetch('/api/settings/jenkins', {method: 'DELETE'});
        showAlert('jenkinsTestResult', 'info', '<i class="fas fa-info-circle"></i> Jenkins integration disabled');
        checkJenkinsStatus();
    }
}

async function disableGitHub() {
    if (confirm('Disable GitHub integration?')) {
        await fetch('/api/settings/github', {method: 'DELETE'});
        showAlert('githubTestResult', 'info', '<i class="fas fa-info-circle"></i> GitHub integration disabled');
        checkGitHubStatus();
    }
}

async function disableGroq() {
    if (confirm('Disable Groq AI integration?')) {
        await fetch('/api/settings/groq', {method: 'DELETE'});
        showAlert('groqTestResult', 'info', '<i class="fas fa-info-circle"></i> Groq AI integration disabled');
        checkGroqStatus();
    }
}

// Show alert helper
function showAlert(elementId, type, message) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    setTimeout(() => {
        element.innerHTML = '';
    }, 5000);
}
