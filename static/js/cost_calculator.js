let costPieChart = null;

document.addEventListener('DOMContentLoaded', function () {
    loadHistory();
    Promise.all([loadFilamentOptions(), loadPrinterOptions()]).then(() => {
        addFilamentRow();
        addPrinterRow();
    });
});

function loadFilamentOptions() {
    return fetch('/api/filaments').then(r => r.json()).then(data => {
        window._allFilaments = data;
    });
}
function loadPrinterOptions() {
    return fetch('/api/printers').then(r => r.json()).then(data => {
        window._allPrinters = data;
        document.querySelectorAll('.printer-select').forEach(sel => populatePrinterSelect(sel));
    });
}

function addFilamentRow() {
    const c = document.getElementById('filamentsContainer');
    const row = document.createElement('div'); row.className = 'calc-row';
    row.innerHTML = '<button type="button" class="btn btn-outline filament-pick-btn" onclick="openFilamentPicker(this)" style="width:35%;text-align:left;font-size:0.85rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + _i('pick_filament_btn', '点击选择耗材') + '</button>' +
        '<input type="hidden" class="filament-id" value="">' +
        '<input type="hidden" class="filament-price" value="">' +
        '<input type="hidden" class="filament-init" value="">' +
        '<input type="hidden" class="filament-current" value="">' +
        '<input type="hidden" class="filament-name" value="">' +
        '<input type="number" class="form-control weight-input" placeholder="g" step="0.1" oninput="recalc()" style="width:10%">' +
        '<input type="number" class="form-control purge-input" placeholder="0" value="0" step="0.1" oninput="recalc()" style="width:10%">' +
        '<span class="unit-price" style="font-size:0.8rem;width:10%">¥0/g</span>' +
        '<label style="font-size:0.75rem;width:10%"><input type="checkbox" class="is-support"> ' + _i('support_label_short', '支撑') + '</label>' +
        '<button class="btn btn-danger btn-sm" onclick="this.parentElement.remove();recalc();"><i class="fas fa-times"></i></button>';
    c.appendChild(row);
}

let currentPickerRow = null;

function openFilamentPicker(btn) {
    currentPickerRow = btn.parentElement;
    loadPickerTable();
    document.getElementById('filamentPickerModal').style.display = 'flex';
}

function closeFilamentPicker() {
    document.getElementById('filamentPickerModal').style.display = 'none';
    currentPickerRow = null;
}

function loadPickerTable() {
    if (!window._allFilaments) {
        fetch('/api/filaments').then(r => r.json()).then(data => {
            window._allFilaments = data;
            renderPickerTable();
        });
        return;
    }
    renderPickerTable();
}

function renderPickerTable() {
    const tbody = document.getElementById('pickerTableBody');
    const term = (document.getElementById('pickerSearch')?.value || '').toLowerCase();
    const statusFilters = new Set();
    document.querySelectorAll('#pickerStatusFilters input:checked').forEach(cb => statusFilters.add(cb.value));

    let data = window._allFilaments || [];
    if (term) data = data.filter(f => (f.brand_name||'') + ' ' + (f.material_type||'') + ' ' + (f.name||'') .toLowerCase().includes(term));
    const low = 100;
    // Map DB Chinese status → i18n display value to match checkbox filters
    const _fi18n = function(dbStatus) {
        const m = { '全新': _i('status_new', '全新'), '闲置': _i('status_idle', '闲置'), '不足': _i('status_insufficient', '不足'), '用尽': _i('status_used_up', '用尽'), '上机': _i('status_loaded', '上机') };
        return m[dbStatus] || dbStatus;
    };
    data = data.filter(f => {
        const s = f.current_weight > 0 && f.current_weight <= low ? _fi18n('不足') : (f.is_loaded ? _fi18n('上机') : _fi18n(f.status));
        return statusFilters.has(s);
    });
    data.sort((a, b) => (b.is_favorite ? 1 : 0) - (a.is_favorite ? 1 : 0));

    tbody.innerHTML = '';
    if (!data.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">' + _i('no_matching_filaments_msg', '无匹配耗材') + '</td></tr>'; return; }
    data.forEach(f => {
        tbody.innerHTML += '<tr style="cursor:pointer;" onclick="selectPickerFilament(' + f.id + ',\'' + (f.brand_name||'').replace(/'/g,"\\'") + '\',\'' + (f.material_type||'').replace(/'/g,"\\'") + '\',\'' + (f.name||'').replace(/'/g,"\\'") + '\',' + (f.purchase_price||0) + ',' + (f.initial_weight||1000) + ',' + (f.current_weight||0) + ')">' +
            '<td>' + (f.brand_name||'-') + '</td><td>' + (f.material_type||'-') + '</td><td>' + (f.name||'-') + '</td>' +
            '<td><span class="color-indicator" style="background:' + f.color + ';"></span></td>' +
            '<td>' + ((f.current_weight||0).toFixed(1)) + 'g</td>' +
            '<td><button class="btn btn-primary btn-sm">' + _i('confirm_btn', '确定') + '</button></td></tr>';
    });
}

function selectPickerFilament(id, brand, mat, name, price, initW, currentW) {
    if (!currentPickerRow) return;
    const row = currentPickerRow;
    row.querySelector('.filament-pick-btn').textContent = brand + ' ' + mat + ' - ' + name;
    row.querySelector('.filament-id').value = id;
    row.querySelector('.filament-price').value = price;
    row.querySelector('.filament-init').value = initW;
    row.querySelector('.filament-current').value = currentW;
    row.querySelector('.filament-name').value = name;
    const unitPrice = initW > 0 ? (price / initW).toFixed(4) : 0;
    row.querySelector('.unit-price').textContent = '¥' + unitPrice + '/g';
    closeFilamentPicker();
    recalc();
}

function addPrinterRow() {
    const c = document.getElementById('printersContainer');
    const row = document.createElement('div'); row.className = 'calc-row';
    row.innerHTML = '<select class="form-control printer-select" onchange="onPrinterSelect(this)" style="width:30%"><option value="">' + _i('select_device_placeholder', '选择设备') + '</option></select>' +
        '<input type="number" class="form-control print-hours" placeholder="' + _i('hours_placeholder', '时') + '" value="0" min="0" oninput="recalc()" style="width:8%">' +
        '<input type="number" class="form-control print-mins" placeholder="' + _i('mins_placeholder', '分') + '" value="0" min="0" oninput="recalc()" style="width:8%">' +
        '<span class="printer-info" style="font-size:0.75rem;width:30%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">—</span>' +
        '<button class="btn btn-danger btn-sm" onclick="this.parentElement.remove();recalc();"><i class="fas fa-times"></i></button>';
    c.appendChild(row);
    const sel = row.querySelector('.printer-select');
    if (window._allPrinters) populatePrinterSelect(sel);
}

function populatePrinterSelect(sel) {
    sel.innerHTML = '<option value="">' + _i('select_device_placeholder', '选择设备') + '</option>';
    (window._allPrinters || []).forEach(p => {
        const slots = p.slots || [];
        const loadedCount = slots.filter(s => s.filament).length;
        sel.innerHTML += '<option value="' + p.id + '" data-power="' + (p.power_w||200) + '" data-value="' + (p.value_yuan||0) + '" data-life="' + (p.lifespan_h||20000) + '" data-name="' + p.name + '">' + p.name + (loadedCount>0?' [' + loadedCount + _i('slot_occupied_suffix', '{count}槽占用').replace('{count}', '') + ']':'') + '</option>';
    });
}

function onPrinterSelect(el) {
    const opt = el.selectedOptions[0];
    el.parentElement.querySelector('.printer-info').textContent = opt?.dataset.name
        ? opt.dataset.power + 'W ¥' + opt.dataset.value + ' ' + opt.dataset.life + 'h' : '—';
    recalc();
}

function addPostRow() {
    const c = document.getElementById('postContainer');
    const row = document.createElement('div'); row.className = 'calc-row';
    row.innerHTML = '<input type="text" class="form-control" placeholder="' + _i('process_name_placeholder', '工序名') + '" style="width:20%">' +
        '<select class="form-control post-charge" onchange="recalc()" style="width:15%"><option value="hourly">' + _i('charge_hourly', '按小时计费') + '</option><option value="per_item">' + _i('charge_per_item', '按件计费') + '</option></select>' +
        '<input type="number" class="form-control post-rate" placeholder="' + _i('unit_price_short', '单价') + '" value="0" step="0.01" oninput="recalc()" style="width:10%">' +
        '<input type="number" class="form-control post-qty" placeholder="' + _i('qty_placeholder', '数量') + '" value="1" step="0.1" oninput="recalc()" style="width:10%">' +
        '<button class="btn btn-danger btn-sm" onclick="this.parentElement.remove();recalc();"><i class="fas fa-times"></i></button>';
    c.appendChild(row);
}

function recalc() {
    let materialCost = 0, electricityCost = 0, depreciationCost = 0;
    const filamentItems = [];

    document.querySelectorAll('#filamentsContainer .calc-row').forEach(row => {
        const fid = row.querySelector('.filament-id')?.value;
        const weight = parseFloat(row.querySelector('.weight-input').value) || 0;
        const purge = parseFloat(row.querySelector('.purge-input').value) || 0;
        const isSupport = row.querySelector('.is-support')?.checked || false;
        const price = parseFloat(row.querySelector('.filament-price')?.value) || 0;
        const initW = parseFloat(row.querySelector('.filament-init')?.value) || 1000;
        const currentW = parseFloat(row.querySelector('.filament-current')?.value) || 0;
        const fname = row.querySelector('.filament-name')?.value || '';
        const unitPrice = initW > 0 ? price / initW : 0;
        const lineCost = (weight + purge) * unitPrice;
        materialCost += lineCost;
        if (fid) filamentItems.push({
            filament_id: parseInt(fid), material_name: fname,
            weight_g: weight, purge_g: purge, cost_per_g: unitPrice, is_support: isSupport ? 1 : 0,
            current_g: currentW,
            _overstock: (weight + purge) > currentW,
        });
        row.style.border = filamentItems.length && filamentItems[filamentItems.length - 1]._overstock
            ? '2px solid var(--warning)' : '';
    });

    const printerItems = [];
    document.querySelectorAll('#printersContainer .calc-row').forEach(row => {
        const sel = row.querySelector('.printer-select');
        const hours = parseFloat(row.querySelector('.print-hours').value) || 0;
        const mins = parseFloat(row.querySelector('.print-mins').value) || 0;
        const totalMins = hours * 60 + mins;
        const opt = sel?.selectedOptions[0];
        const power = parseFloat(opt?.dataset.power) || 200;
        const valueYuan = parseFloat(opt?.dataset.value) || 0;
        const lifeH = parseFloat(opt?.dataset.life) || 20000;
        const elecCost = (totalMins / 60) * (power / 1000) * 0.6;
        const deprecCost = (totalMins / 60) * (valueYuan / lifeH);
        electricityCost += elecCost;
        depreciationCost += deprecCost;
        if (sel?.value) printerItems.push({
            printer_id: parseInt(sel.value), printer_name: opt?.dataset.name || '',
            print_time_mins: totalMins, power_w: power, value_yuan: valueYuan, lifespan_h: lifeH,
        });
    });

    let postCost = 0;
    const postItems = [];
    document.querySelectorAll('#postContainer .calc-row').forEach(row => {
        const chargeType = row.querySelector('.post-charge')?.value || 'hourly';
        const rate = parseFloat(row.querySelector('.post-rate')?.value) || 0;
        const qty = parseFloat(row.querySelector('.post-qty')?.value) || 0;
        const subtotal = chargeType === 'hourly' ? rate * qty : rate * qty;
        postCost += subtotal;
        postItems.push({ process_name: row.querySelector('input')?.value || '', charge_type: chargeType, rate, quantity: qty, subtotal });
    });

    const designFee = parseFloat(document.getElementById('designFee').value) || 0;
    const packagingFee = parseFloat(document.getElementById('packagingFee').value) || 0;
    const shippingFee = parseFloat(document.getElementById('shippingFee').value) || 0;
    const otherFee = parseFloat(document.getElementById('otherFee').value) || 0;
    const extraFees = designFee + packagingFee + shippingFee + otherFee;

    const totalCost = materialCost + electricityCost + depreciationCost + postCost + extraFees;
    const taxRate = (parseFloat(document.getElementById('taxRate').value) || 0) / 100;
    const platformRate = (parseFloat(document.getElementById('platformRate').value) || 0) / 100;
    const profitExpect = (parseFloat(document.getElementById('profitExpect').value) || 0) / 100;
    const laborFee = parseFloat(document.getElementById('laborFee').value) || 0;

    const baseForProfit = (totalCost + laborFee);
    const divisor = 1 - profitExpect - platformRate - taxRate;
    const suggestedPrice = divisor > 0 ? baseForProfit / divisor : totalCost * 1.5;
    const pureProfit = suggestedPrice - totalCost;

    document.getElementById('dispTotalCost').textContent = '¥' + totalCost.toFixed(2);
    document.getElementById('dispPrice').textContent = '¥' + suggestedPrice.toFixed(2);
    document.getElementById('dispProfit').textContent = '¥' + pureProfit.toFixed(2);

    updatePieChart(materialCost, electricityCost, depreciationCost, postCost, extraFees);

    window._calcData = { filaments: filamentItems, printers: printerItems, post_processing: postItems,
        total_cost: totalCost, suggested_price: suggestedPrice, pure_profit: pureProfit };
}

function updatePieChart(mat, elec, depr, post, extra) {
    const ctx = document.getElementById('costPieChart'); if (!ctx) return;
    if (costPieChart) costPieChart.destroy();
    const data = {};
    data[_i('cost_breakdown_material', '材料费')] = mat;
    data[_i('cost_breakdown_elec', '电费')] = elec;
    data[_i('cost_breakdown_depr', '折旧费')] = depr;
    data[_i('cost_breakdown_post', '后处理')] = post;
    data[_i('cost_breakdown_extra', '附加费')] = extra;
    const labels = Object.keys(data).filter(k => data[k] > 0);
    const values = labels.map(k => data[k]);
    if (values.length === 0) return;
    costPieChart = new Chart(ctx.getContext('2d'), {
        type: 'pie',
        data: { labels, datasets: [{ data: values, backgroundColor: ['#5b9bd5','#f72585','#ff8c00','#20b2aa','#9acd32'] }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { color: '#333' } },
                datalabels: {
                    color: '#111',
                    font: { weight: 'bold', size: 12 },
                    formatter: (value, ctx) => {
                        const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                        const pct = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                        return '¥' + value.toFixed(0) + '\n' + pct + '%';
                    },
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}

function saveCalculation() {
    const data = window._calcData || {};
    const payload = {
        id: document.getElementById('currentRecordId').value || null,
        project_name: document.getElementById('calcProjectName').value || _i('unnamed_project', '未命名项目'),
        filaments: data.filaments || [],
        printers: data.printers || [],
        post_processing: data.post_processing || [],
        design_fee: parseFloat(document.getElementById('designFee').value) || 0,
        packaging_fee: parseFloat(document.getElementById('packagingFee').value) || 0,
        shipping_fee: parseFloat(document.getElementById('shippingFee').value) || 0,
        other_fee: parseFloat(document.getElementById('otherFee').value) || 0,
        tax_rate: parseFloat(document.getElementById('taxRate').value) || 0,
        platform_commission_rate: parseFloat(document.getElementById('platformRate').value) || 0,
        profit_rate_expect: parseFloat(document.getElementById('profitExpect').value) || 0,
        labor_markup_fee: parseFloat(document.getElementById('laborFee').value) || 0,
        total_cost: data.total_cost || 0,
        suggested_price: data.suggested_price || 0,
        pure_profit: data.pure_profit || 0,
    };
    fetch('/api/tools/calculator/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        .then(r => r.json()).then(d => {
            if (d.status === 'success') {
                document.getElementById('currentRecordId').value = d.id;
                const btn = document.getElementById('saveCalcBtn');
                btn.innerHTML = '<i class="fas fa-save"></i> ' + (d.action === 'updated' ? _i('updated_label', '已更新') : _i('saved_label', '已保存'));
                setTimeout(() => btn.innerHTML = '<i class="fas fa-save"></i> ' + _i('btn_save_calc', '保存计算'), 2000);
                loadHistory();
            } else alert(d.error || _i('msg_save_failed', '保存失败'));
        });
}

function loadHistory() {
    fetch('/api/tools/calculator/history').then(r => r.json()).then(data => {
        const c = document.getElementById('historyList');
        if (!data.length) { c.innerHTML = '<div class="empty-state"><i class="fas fa-history"></i><p>' + _i('no_history_msg', '暂无历史记录') + '</p></div>'; return; }
        c.innerHTML = '';
        data.forEach(h => {
            c.innerHTML += '<div class="history-item" style="display:flex;justify-content:space-between;align-items:center;padding:0.5rem;border-bottom:1px solid rgba(0,0,0,0.05);">' +
                '<div><strong>' + h.project_name + '</strong><br><small>' + h.created_at + ' | ' + _i('cost_label', '成本') + '¥' + h.total_cost.toFixed(2) + ' | ' + _i('price_label', '报价') + '¥' + h.suggested_price.toFixed(2) + ' | ' + _i('profit_label', '利润') + '¥' + (h.pure_profit||0).toFixed(2) + '</small></div>' +
                '<div><button class="btn btn-outline btn-sm" onclick="loadHistoryDetail(' + h.id + ')" title="' + _i('load_edit_title', '载入编辑') + '">📂</button>' +
                '<button class="btn btn-outline btn-sm" onclick="cloneHistory(' + h.id + ')" title="' + _i('clone_title', '复制克隆') + '">👥</button>' +
                '<button class="btn btn-danger btn-sm" onclick="deleteHistory(' + h.id + ')"><i class="fas fa-trash"></i></button></div></div>';
        });
    });
}
function loadHistoryDetail(id) {
    fetch('/api/tools/calculator/detail/' + id).then(r => r.json()).then(d => {
        document.getElementById('currentRecordId').value = d.id;
        document.getElementById('calcProjectName').value = d.project_name;
        document.getElementById('designFee').value = d.design_fee;
        document.getElementById('packagingFee').value = d.packaging_fee;
        document.getElementById('shippingFee').value = d.shipping_fee;
        document.getElementById('otherFee').value = d.other_fee;
        document.getElementById('taxRate').value = d.tax_rate;
        document.getElementById('platformRate').value = d.platform_commission_rate;
        document.getElementById('profitExpect').value = d.profit_rate_expect;
        document.getElementById('laborFee').value = d.labor_markup_fee;
        deserializeFilaments(d.filaments || []);
        deserializePrinters(d.printers || []);
        deserializePost(d.post_processing || []);
        recalc();
        document.getElementById('saveCalcBtn').innerHTML = '<i class="fas fa-save"></i> ' + _i('update_current_record', '更新当前记录');
    });
}
function cloneHistory(id) {
    fetch('/api/tools/calculator/detail/' + id).then(r => r.json()).then(d => {
        document.getElementById('currentRecordId').value = '';
        loadHistoryDetail(id);
        document.getElementById('currentRecordId').value = '';
        document.getElementById('saveCalcBtn').innerHTML = '<i class="fas fa-save"></i> ' + _i('save_as_new_calc', '保存为新的计算');
    });
}
function deleteHistory(id) {
    if (!confirm(_i('confirm_delete_history', '确定要删除这条历史记录吗？'))) return;
    fetch('/api/tools/calculator/history/' + id, { method: 'DELETE' }).then(r => r.json()).then(d => { if (d.status === 'success') loadHistory(); });
}

function deserializeFilaments(items) {
    const c = document.getElementById('filamentsContainer'); c.innerHTML = '';
    items.forEach(item => {
        addFilamentRow();
        const row = c.lastChild;
        const f = (window._allFilaments || []).find(fi => fi.id == item.filament_id);
        const brand = f?.brand_name || '';
        const mat = f?.material_type || '';
        const name = f?.name || item.material_name || '';
        row.querySelector('.filament-pick-btn').textContent = brand + ' ' + mat + ' - ' + name;
        row.querySelector('.filament-id').value = item.filament_id;
        row.querySelector('.filament-price').value = f?.purchase_price || 0;
        row.querySelector('.filament-init').value = f?.initial_weight || 1000;
        row.querySelector('.filament-current').value = f?.current_weight || 0;
        row.querySelector('.filament-name').value = name;
        const price = f?.purchase_price || 0;
        const initW = f?.initial_weight || 1000;
        const unitPrice = initW > 0 ? (price / initW).toFixed(4) : 0;
        row.querySelector('.unit-price').textContent = '¥' + unitPrice + '/g';
        row.querySelector('.weight-input').value = item.weight_g;
        row.querySelector('.purge-input').value = item.purge_g || 0;
        if (item.is_support) row.querySelector('.is-support').checked = true;
    });
}
function deserializePrinters(items) {
    const c = document.getElementById('printersContainer'); c.innerHTML = '';
    items.forEach(item => {
        addPrinterRow();
        const row = c.lastChild;
        setTimeout(() => {
            row.querySelector('.printer-select').value = item.printer_id;
            const tm = item.print_time_mins || 0;
            row.querySelector('.print-hours').value = Math.floor(tm / 60);
            row.querySelector('.print-mins').value = Math.round(tm % 60);
            onPrinterSelect(row.querySelector('.printer-select'));
        }, 100);
    });
}
function deserializePost(items) {
    const c = document.getElementById('postContainer'); c.innerHTML = '';
    items.forEach(item => {
        addPostRow();
        const row = c.lastChild;
        row.querySelector('input').value = item.process_name || '';
        row.querySelector('.post-charge').value = item.charge_type || 'hourly';
        row.querySelector('.post-rate').value = item.rate || 0;
        row.querySelector('.post-qty').value = item.quantity || 1;
    });
}
