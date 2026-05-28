let monthlyROIChart = null;
let roiUsageData = [];

document.addEventListener('DOMContentLoaded', function () {
    loadConfigAndData();
    document.getElementById('marketPrice').addEventListener('change', onParamChange);
    document.getElementById('elecDepreciation').addEventListener('change', onParamChange);
});

function loadConfigAndData() {
    fetch('/api/system/config')
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success' && d.data) {
                document.getElementById('marketPrice').value = d.data.market_price_per_gram ?? 0.15;
                document.getElementById('elecDepreciation').value = d.data.cost_per_gram ?? 0.01;
            }
        })
        .catch(() => {})
        .finally(() => {
            fetch('/api/usage_records')
                .then(r => r.json())
                .then(records => {
                    roiUsageData = records;
                    calcROI();
                });
        });
}

function onParamChange() {
    const payload = {
        market_price_per_gram: parseFloat(document.getElementById('marketPrice').value) || 0.15,
        cost_per_gram: parseFloat(document.getElementById('elecDepreciation').value) || 0.01,
    };
    fetch('/api/system/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    }).catch(() => {});
    calcROI();
}

function calcROI() {
    const marketPrice = parseFloat(document.getElementById('marketPrice').value) || 0.15;
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
        const t = r.material_type || _i('unknown', '未知');
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
    document.getElementById('roiNote').textContent = _i('roi_net_profit_note', '净收益: ¥') + netSaving.toFixed(2);

    const months = Object.keys(monthly).sort();
    const ctx = document.getElementById('monthlyROIChart');
    if (ctx) {
        const marketVals = months.map(m => monthly[m].weight * marketPrice);
        const actualVals = months.map(m => monthly[m].cost);
        const savings = months.map((m, i) => marketVals[i] - actualVals[i]);
        if (monthlyROIChart) monthlyROIChart.destroy();
        monthlyROIChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: months,
                datasets: [
                    { label: _i('chart_market_value_label', '代打市场价 (¥)'), data: marketVals, backgroundColor: '#5b9bd5', yAxisID: 'y' },
                    { label: _i('chart_actual_cost_label', '自制实际成本 (¥)'), data: actualVals, backgroundColor: '#f72585', yAxisID: 'y' },
                    { label: _i('chart_monthly_saving_label', '当月净省 (¥)'), data: savings, type: 'line', borderColor: '#4cc9f0', backgroundColor: 'rgba(76,201,240,0.1)', yAxisID: 'y', tension: 0.3, fill: true },
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
        });
    }

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
