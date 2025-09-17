document.addEventListener('DOMContentLoaded', () => {

    // ------------------------------
    // Initialize Chart.js
    // ------------------------------
    const ctx = document.getElementById('dailyInteractionsChart').getContext('2d');
    const dailyInteractionsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],  // x-axis labels (dates)
            datasets: [{
                label: 'Daily Interactions',
                data: [],  // y-axis data
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // ------------------------------
    // Function to update cards & chart
    // ------------------------------
    function updateAnalyticsData() {
        // Replace these with real data from your backend
        const cardData = {
            totalInteractions: 1200,
            activeUsers: 350,
            faqUsage: 80,
            newLeads: 45
        };

        // Update cards
        document.getElementById('total-interactions').textContent = cardData.totalInteractions;
        document.getElementById('active-users').textContent = cardData.activeUsers;
        document.getElementById('faq-usage').textContent = cardData.faqUsage;
        document.getElementById('new-leads').textContent = cardData.newLeads;

        // Example daily interactions for chart
        const dailyLabels = ["Aug 1","Aug 2","Aug 3","Aug 4","Aug 5","Aug 6","Aug 7"];
        const dailyData = [20, 35, 50, 45, 60, 55, 70];

        // Update chart data
        dailyInteractionsChart.data.labels = dailyLabels;
        dailyInteractionsChart.data.datasets[0].data = dailyData;
        dailyInteractionsChart.update();
    }

    // ------------------------------
    // Analytics menu click listener
    // ------------------------------
    document.getElementById('menu-analytics').addEventListener('click', () => {
        // Hide all dashboard sections
        document.querySelectorAll('.dashboard-section').forEach(section => {
            section.classList.add('hidden');
        });

        // Show Analytics section
        document.getElementById('analytics').classList.remove('hidden');

        // Update cards and chart
        updateAnalyticsData();
    });

});
