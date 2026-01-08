
// Equity curve

const canvas = document.getElementById('equityChart');
const equityData = JSON.parse(canvas.dataset.equity);

const ctx = canvas.getContext('2d');

const equityValues = equityData.map(d => d.equity);
const timeLabels = equityData.map(d => new Date(d.time_close));
// calculate min and max with 10% buffer
const minEquity = Math.min(...equityValues);
const maxEquity = Math.max(...equityValues);
const yMin = minEquity * 0.95; // 10% under lowest equity value
const yMax = maxEquity * 1.05; // 10% above highest equity value

const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: equityData.map(d => d.time_close),
        datasets: [{
            label: '2026',
            data: equityData.map(d => d.equity),
            borderColor: 'rgb(75, 192, 192)',
            fill: false,
            tension: 0.1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Equity Curve',
                font: {
                    size: 20
                }
            },
            legend: {
                display: true,
                position: 'top', // inside the chart
                align: 'end',   // top right
                labels: {
                    boxWidth: 20,
                    padding: 10,
                    font: {size: 14}
                }
            } },
        scales: {
            x: {
                title: { display: true, text: 'Date' }
            },
            y: {
                title: { display: true, text: 'Equity ($)' },
                min: yMin,
                max: yMax
            }
        }
    }
});

// Daily P&L
const equity_change = equityData.map(d => d.equity_change);
const last_dailyPL = equity_change[equity_change.length - 1];

document.getElementById('dailyPL').innerText = last_dailyPL.toFixed(2) + ' $';