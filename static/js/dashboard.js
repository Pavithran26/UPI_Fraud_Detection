// Dashboard JavaScript for UPI Fraud Detection System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard components
    initializeAlerts();
    initializeTransactionTable();
    setupRealTimeUpdates();
    
    // Auto-refresh alerts every 30 seconds
    setInterval(refreshAlerts, 30000);
});

/**
 * Initialize alert components
 */
function initializeAlerts() {
    const alertItems = document.querySelectorAll('.alert-item');
    
    alertItems.forEach(item => {
        // Add click handlers for alert actions
        const resolveBtn = item.querySelector('button[type="submit"]');
        if (resolveBtn) {
            resolveBtn.addEventListener('click', function(e) {
                if (!confirm('Mark this alert as resolved?')) {
                    e.preventDefault();
                }
            });
        }
    });
}

/**
 * Initialize transaction table features
 */
function initializeTransactionTable() {
    const table = document.querySelector('.table');
    if (!table) return;
    
    // Add hover effects and click handlers
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on a button or link
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || e.target.closest('a')) {
                return;
            }
            
            // Find transaction link in the row
            const link = row.querySelector('a');
            if (link) {
                window.location.href = link.href;
            }
        });
        
        // Add cursor pointer style
        row.style.cursor = 'pointer';
    });
}

/**
 * Setup real-time updates for the dashboard
 */
function setupRealTimeUpdates() {
    // Update timestamps every minute
    setInterval(updateRelativeTimes, 60000);
    
    // Check for new high-priority alerts
    setInterval(checkHighPriorityAlerts, 10000);
}

/**
 * Update relative timestamps
 */
function updateRelativeTimes() {
    const timeElements = document.querySelectorAll('[data-timestamp]');
    timeElements.forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
        const relativeTime = getRelativeTime(new Date(timestamp));
        element.textContent = relativeTime;
    });
}

/**
 * Get relative time string
 */
function getRelativeTime(date) {
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d ago`;
}

/**
 * Refresh alerts from server
 */
async function refreshAlerts() {
    try {
        const response = await fetch('/api/alerts');
        if (!response.ok) return;
        
        const alerts = await response.json();
        updateAlertsDisplay(alerts);
    } catch (error) {
        console.error('Error refreshing alerts:', error);
    }
}

/**
 * Update alerts display
 */
function updateAlertsDisplay(alerts) {
    const alertsList = document.querySelector('.alert-list');
    const alertBadge = document.querySelector('.card-header .badge');
    
    if (!alertsList || !alertBadge) return;
    
    // Update alert count
    alertBadge.textContent = alerts.length;
    
    if (alerts.length === 0) {
        alertsList.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-shield-alt text-success fa-3x mb-3"></i>
                <p class="text-muted">No active alerts</p>
            </div>
        `;
        return;
    }
    
    // Update alerts list
    alertsList.innerHTML = alerts.map(alert => `
        <div class="alert-item p-3 border-bottom">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="alert-severity mb-1">
                        <span class="badge bg-${getSeverityClass(alert.severity)}">
                            ${alert.severity}
                        </span>
                    </div>
                    <div class="alert-message small">${alert.message.substring(0, 80)}...</div>
                    <div class="alert-time text-muted small">
                        ${formatAlertTime(alert.timestamp)}
                    </div>
                </div>
                <div class="alert-actions">
                    <form method="POST" action="/resolve-alert/${alert.id}" style="display: inline;">
                        <button type="submit" class="btn btn-sm btn-outline-success" title="Mark as resolved">
                            <i class="fas fa-check"></i>
                        </button>
                    </form>
                </div>
            </div>
        </div>
    `).join('');
    
    // Reinitialize alert handlers
    initializeAlerts();
}

/**
 * Get CSS class for alert severity
 */
function getSeverityClass(severity) {
    switch (severity) {
        case 'HIGH': return 'danger';
        case 'MEDIUM': return 'warning';
        case 'LOW': return 'info';
        default: return 'secondary';
    }
}

/**
 * Format alert timestamp
 */
function formatAlertTime(timestamp) {
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const day = date.getDate();
    const month = date.toLocaleDateString('en', { month: 'short' });
    return `${hours}:${minutes}, ${day} ${month}`;
}

/**
 * Check for high-priority alerts and show notifications
 */
async function checkHighPriorityAlerts() {
    try {
        const response = await fetch('/api/alerts');
        if (!response.ok) return;
        
        const alerts = await response.json();
        const highPriorityAlerts = alerts.filter(alert => alert.severity === 'HIGH');
        
        if (highPriorityAlerts.length > 0) {
            // Show browser notification if permitted
            if (Notification.permission === 'granted') {
                new Notification('High Priority Fraud Alert', {
                    body: `${highPriorityAlerts.length} high-priority fraud alerts require attention`,
                    icon: '/static/favicon.ico'
                });
            }
            
            // Update page title to show alert count
            document.title = `(${highPriorityAlerts.length}) UPI Fraud Detection - Dashboard`;
        } else {
            // Reset title
            document.title = 'UPI Fraud Detection - Dashboard';
        }
    } catch (error) {
        console.error('Error checking high-priority alerts:', error);
    }
}

/**
 * Request notification permission on load
 */
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

/**
 * Utility function to format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Utility function to format percentage
 */
function formatPercentage(value) {
    return `${(value * 100).toFixed(1)}%`;
}

/**
 * Export functions for testing
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getRelativeTime,
        getSeverityClass,
        formatAlertTime,
        formatCurrency,
        formatPercentage
    };
}
