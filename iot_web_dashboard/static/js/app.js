


let chart = null;
let eventSource = null;
let mqttConnected = false;


document.addEventListener('DOMContentLoaded', function() {
    console.log('IoT Dashboard initialized');
    
   
    startMQTTStream();
    
    
    loadHistoricalData();
    loadStatistics();
    updateServerTime();
    
   
    setInterval(updateServerTime, 1000);
});


function openTab(tabName) {
    
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(tab => {
        tab.classList.remove('active');
    });
    
    
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });
    
   
    document.getElementById(tabName).classList.add('active');
    
    event.currentTarget.classList.add('active');
    
    if (tabName === 'historical') {
        loadHistoricalData();
    } else if (tabName === 'stats') {
        loadStatistics();
    }
}


function startMQTTStream() {
    if (eventSource) {
        eventSource.close();
    }
    
    eventSource = new EventSource('/api/stream');
    
    eventSource.onopen = function() {
        console.log('Connected to MQTT stream');
        updateConnectionStatus(true);
        mqttConnected = true;
    };
    
    eventSource.onmessage = function(event) {
        if (event.data.startsWith(': heartbeat')) {
            return; 
        }
        
        try {
            const data = JSON.parse(event.data);
            displayLatestData(data.payload, data.timestamp);
        } catch (error) {
            console.error('Error parsing MQTT data:', error);
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('MQTT stream error:', error);
        updateConnectionStatus(false);
        mqttConnected = false;
        
        
        setTimeout(startMQTTStream, 5000);
    };
}


function displayLatestData(data, timestamp) {
    const latestDataDiv = document.getElementById('latest-data');
    
    
    const formattedData = JSON.stringify(data, null, 2)
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    
    latestDataDiv.classList.add('new-data');
    setTimeout(() => {
        latestDataDiv.classList.remove('new-data');
    }, 1000);
    
    latestDataDiv.innerHTML = `<pre>${formattedData}</pre>`;
    
    
    if (timestamp) {
        const date = new Date(timestamp * 1000);
        document.getElementById('last-updated').textContent = 
            date.toLocaleTimeString();
    }
    
    
    updateQuickStats(data);
}


function updateQuickStats(data) {
    document.getElementById('device-id').textContent = 
        data.device_id || 'RaspberryPiEmulator1';
    
    document.getElementById('current-value').textContent = 
        data.sendor_data || data.value || '--';
    
    document.getElementById('device-status').textContent = 
        data.status || 'active';
    
    document.getElementById('message-id').textContent = 
        data.message_id || '--';
}


async function loadHistoricalData() {
    try {
        const timeRange = document.getElementById('time-range').value;
        
        const response = await fetch(`/api/historical?hours=${timeRange}`);
        const data = await response.json();
        
        if (data.success) {
            displayHistoricalData(data.data);
            updateChart(data.data);
        } else {
            document.getElementById('historical-data').innerHTML = 
                `<p class="loading">${data.error || 'No historical data'}</p>`;
        }
    } catch (error) {
        console.error('Error loading historical:', error);
        document.getElementById('historical-data').innerHTML = 
            '<p class="loading error">Failed to load data</p>';
    }
}


function displayHistoricalData(data) {
    const tableDiv = document.getElementById('historical-data');
    
    if (!data || data.length === 0) {
        tableDiv.innerHTML = '<p class="loading">No data found</p>';
        return;
    }
    
    let html = `
        <div class="table-row header">
            <div>Time</div>
            <div>Device</div>
            <div>Message</div>
            <div>Value</div>
        </div>
    `;
    
    data.forEach(item => {
        html += `
            <div class="table-row">
                <div>${item.formatted_time}</div>
                <div>${item.device_id}</div>
                <div>${item.message || '-'}</div>
                <div><strong>${item.value}</strong></div>
            </div>
        `;
    });
    
    tableDiv.innerHTML = html;
}


function updateChart(data) {
    const ctx = document.getElementById('historyChart').getContext('2d');
    
    if (chart) {
        chart.destroy();
    }
    
    const labels = data.map(item => item.formatted_time);
    const values = data.map(item => item.value);
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sensor Value',
                data: values,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45
                    }
                },
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}


async function loadStatistics() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            updateStatistics(data.stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}


function updateStatistics(stats) {
    document.getElementById('total-readings').textContent = stats.total_readings;
    document.getElementById('average-value').textContent = stats.average_value;
    document.getElementById('max-value').textContent = stats.max_value;
    document.getElementById('min-value').textContent = stats.min_value;
}


function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('connection-status');
    
    if (connected) {
        statusDot.classList.add('active');
        statusText.innerHTML = '<i class="fas fa-bolt"></i> Receiving live MQTT data';
        statusText.style.color = '#10b981';
    } else {
        statusDot.classList.remove('active');
        statusText.innerHTML = '<i class="fas fa-unlink"></i> Disconnected from MQTT';
        statusText.style.color = '#ef4444';
    }
}


async function loadLatestData() {
    try {
        const response = await fetch('/api/latest');
        const data = await response.json();
        
        if (data.success) {
            displayLatestData(data.data.payload, data.timestamp);
        }
    } catch (error) {
        console.error('Error loading latest:', error);
    }
}


function updateServerTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    document.getElementById('server-time').textContent = timeString;
}


window.addEventListener('beforeunload', function() {
    if (eventSource) {
        eventSource.close();
    }
});