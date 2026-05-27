let monthlyROIChart = null;
let roiUsageData = [];

document.addEventListener('DOMContentLoaded', function () {
    loadROIData();
});

function loadROIData() {
    fetch('/api/usage_records')
        .then(r => r.json())
        .then(records => {
            roiUsageData = records;
            calcROI();
        })
        .catch(err => console.error('ROI数据加载失败:', err));
}

function calcROI() {
    const marketPrice = parseFloat(document.getElementById('marketPrice').value) || 0.2;
    const elecDep = parseFloat(document.getElementById('elecDepreciation').value) || 0.01;

    let totalWeight = 0, actualCost = 0;
    const monthly = {};
    const byType = {};

    roiUsageData.forEach(r => {
        const w = r.used_weight;
        totalWeight += w;
        const unitPrice = (r.purchase_price && r.initial_weight > 0) ? r.purchase_price / r.initial_weight : 0;
        const cost = w * unitPrice + w * elecDep;
        actualCost += cost;

        const m = new Date(r.used_at).toISOString().slice(0, 7);
        if (!monthly[m]) monthly[m] = { weight: 0, cost: 0 };
        monthly[m].weight += w;
        monthly[m].cost += cost;

        const t = r.material_type || '未知';
        if (!byType[t]) byType[t] = { weight: 0, cost: 0 };
        byType[t].weight += w;
        byType[t].cost += cost;
    });

    const marketValue = totalWeight * marketPrice;
    const netSaving = marketValue - actualCost;

    document.getElementById('marketValue').textContent = '¥' + marketValue.toFixed(2);
    document.getElementById('actualCost').textContent = '¥' + actualCost.toFixed(2);
    document.getElementById('netSaving').textContent = '¥' + netSaving.toFixed(2);
    document.getElementById('totalThroughput').textContent = totalWeight.toFixed(0) + 'g';
    document.getElementById('roiNote').textContent = '净收益: ¥' + netSaving.toFixed(2);

    // Monthly ROI chart
    const months = Object.keys(monthly).sort();
    const marketVals = months.map(m => monthly[m].weight * marketPrice);
    const actualVals = months.map(m => monthly[m].cost);
    const savings = months.map((m, i) => marketVals[i] - actualVals[i]);

    const ctx = document.getElementById('monthlyROIChart');
    if (ctx) {
        if (monthlyROIChart) monthlyROIChart.destroy();
        monthlyROIChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: months,
                datasets: [
                    { label: '代打市场价 (¥)', data: marketVals, backgroundColor: '#5b9bd5', yAxisID: 'y' },
                    { label: '自制实际成本 (¥)', data: actualVals, backgroundColor: '#f72585', yAxisID: 'y' },
                    { label: '当月净省 (¥)', data: savings, type: 'line', borderColor: '#4cc9f0', backgroundColor: 'rgba(76,201,240,0.1)', yAxisID: 'y', tension: 0.3, fill: true },
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
        });
    }

    // Material ROI table
    const tbody = document.getElementById('roiMaterialTable');
    if (tbody) {
        const sorted = Object.entries(byType).sort((a, b) => b[1].weight - a[1].weight);
        tbody.innerHTML = '';
        sorted.forEach(([type, d]) => {
            const mv = d.weight * marketPrice;
            const saved = mv - d.cost;
            tbody.innerHTML += `<tr><td>${type}</td><td>${d.weight.toFixed(0)}g</td><td>¥${d.cost.toFixed(2)}</td><td>¥${mv.toFixed(2)}</td><td style="color:${saved>0?'var(--success)':'var(--warning)'};font-weight:600;">${saved>0?'+':''}¥${saved.toFixed(2)}</td></tr>`;
        });
    }
}
