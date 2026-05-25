// 3D Consumables Inventory Management System — Main Application JS
// Global state
let filaments = [];
let materialChart = null;
let statusChart = null;
let materialChartReports = null;
let statusChartReports = null;
let usageChart = null;
let dailyUsageChart = null;
let currentEditId = null;
let currentUseId = null;
let selectedFilaments = new Set();
let settings = {};
let longPressTimer = null;
let currentSort = { field: null, direction: 'none' };
let currentSearchTerm = '';
let currentStatusFilter = 'all';

const presetColors = [
    '#000000','#FFFFFF','#808080','#C0C0C0','#FF0000','#0000FF','#008000','#FFFF00','#FFA500','#FFC0CB',
    '#00008B','#006400','#8B0000','#4B0082','#8B4513','#F5F5F5','#F0F8FF','#E0FFFF','#98FB98','#FFFACD',
    '#D2B48C','#C0C0C0','#CD7F32','#DAA520','#87CEEB','#0047AB','#556B2F','#8B0000','#2F4F4F','#D2691E',
    '#FF6347','#32CD32','#1E90FF','#FF69B4','#BA55D3','#20B2AA','#FF4500','#9ACD32','#FFD700','#191970',
    '#8A2BE2','#7FFF00','#DC143C','#00FFFF','#00CED1','#FF1493','#FF8C00','#7CFC00','#ADFF2F','#4B0082'
];

// DOM Ready
document.addEventListener('DOMContentLoaded', function () {
    loadSettings();
    loadData();
    loadUsageRecords();
    initColorPickers();
    loadMaterialOptions();
    loadManufacturerOptions();

    const accessInfo = document.getElementById('accessInfo');
    if (accessInfo) {
        accessInfo.style.display = 'flex';
        fetch('/api/local-ip')
            .then(r => r.json())
            .then(d => { document.getElementById('localAddress').textContent = 'http://' + d.ip + ':9055/'; })
            .catch(() => { document.getElementById('localAddress').textContent = 'http://localhost:9055/'; });
    }

    bindEvents();

    if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
        document.querySelectorAll('input, select, textarea').forEach(el => {
            el.addEventListener('focus', function () {
                setTimeout(() => this.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300);
            });
        });
    }
});

// Status helpers
function getStatusClass(filament) {
    if (filament.current_weight === 0) return 'status-used-up';
    if (filament.current_weight < settings.threshold) return 'status-warning';
    if (filament.is_opened) return 'status-in-use';
    return 'status-unopened';
}

function getStatusText(filament) {
    if (filament.current_weight === 0) return '已用完';
    if (filament.current_weight < settings.threshold) return '库存不足';
    if (filament.is_opened) return '使用中';
    return '未开封';
}

// Load settings
function loadSettings() {
    fetch('/api/settings')
        .then(r => r.json())
        .then(data => { settings = data; });
}

// Load data
function loadData() {
    fetch('/api/filaments')
        .then(r => r.json())
        .then(data => {
            filaments = data;
            renderFilamentTable(applyFilters(data));
            renderFavoriteFilaments(data);
        });
    fetch('/api/statistics')
        .then(r => r.json())
        .then(data => {
            renderStatistics(data);
            renderReports(data);
            renderManufacturerStats(data.manufacturer_stats);
        });
}

// Load material/manufacturer options (adapted for new object-array API format)
function loadMaterialOptions() {
    fetch('/api/materials')
        .then(r => r.json())
        .then(data => {
            const selects = ['materialType', 'batchMaterialType'];
            selects.forEach(sid => {
                const el = document.getElementById(sid);
                if (!el) return;
                el.innerHTML = '';
                data.forEach(item => {
                    const name = typeof item === 'string' ? item : item.name;
                    const opt = document.createElement('option');
                    opt.value = name;
                    opt.textContent = name;
                    el.appendChild(opt);
                });
            });
        });
}

function loadManufacturerOptions() {
    fetch('/api/manufacturers')
        .then(r => r.json())
        .then(data => {
            const selects = ['manufacturer', 'batchManufacturer'];
            selects.forEach(sid => {
                const el = document.getElementById(sid);
                if (!el) return;
                el.innerHTML = '';
                data.forEach(item => {
                    const name = typeof item === 'string' ? item : item.name;
                    const opt = document.createElement('option');
                    opt.value = name;
                    opt.textContent = name;
                    el.appendChild(opt);
                });
            });
        });
}

// Load usage records
function loadUsageRecords() {
    fetch('/api/usage_records')
        .then(r => r.json())
        .then(data => {
            renderUsageRecords(data);
            renderUsageSummary(data);
        });
}

// Filter
function applyFilters(filamentsList) {
    let filtered = filamentsList;
    if (currentSearchTerm) {
        const term = currentSearchTerm.toLowerCase();
        filtered = filtered.filter(f =>
            f.name.toLowerCase().includes(term) ||
            f.material_type.toLowerCase().includes(term) ||
            (f.manufacturer && f.manufacturer.toLowerCase().includes(term)) ||
            (f.color && f.color.toLowerCase().includes(term))
        );
    }
    if (currentStatusFilter === 'opened') filtered = filtered.filter(f => f.is_opened && f.current_weight > 0);
    else if (currentStatusFilter === 'unopened') filtered = filtered.filter(f => !f.is_opened);
    else if (currentStatusFilter === 'used_up') filtered = filtered.filter(f => f.current_weight === 0);
    return filtered;
}

// Init color pickers
function initColorPickers() {
    const addGrid = document.getElementById('presetColors');
    const batchGrid = document.getElementById('batchPresetColors');
    if (addGrid) presetColors.forEach(c => {
        const div = document.createElement('div');
        div.className = 'color-option'; div.style.backgroundColor = c; div.dataset.color = c;
        div.addEventListener('click', () => selectPresetColor(c, 'colorPicker', 'colorPreview'));
        addGrid.appendChild(div);
    });
    if (batchGrid) presetColors.forEach(c => {
        const div = document.createElement('div');
        div.className = 'color-option'; div.style.backgroundColor = c; div.dataset.color = c;
        div.addEventListener('click', () => selectPresetColor(c, 'batchColorPicker', 'batchColorPreview'));
        batchGrid.appendChild(div);
    });
    const cp = document.getElementById('colorPicker');
    const cpr = document.getElementById('colorPreview');
    if (cp && cpr) { cp.addEventListener('input', () => cpr.style.backgroundColor = cp.value); cpr.style.backgroundColor = cp.value; }
    const bcp = document.getElementById('batchColorPicker');
    const bcpr = document.getElementById('batchColorPreview');
    if (bcp && bcpr) { bcp.addEventListener('input', () => bcpr.style.backgroundColor = bcp.value); bcpr.style.backgroundColor = bcp.value; }
}

function selectPresetColor(color, pickerId, previewId) {
    document.getElementById(pickerId).value = color;
    document.getElementById(previewId).style.backgroundColor = color;
    const gridId = pickerId === 'colorPicker' ? 'presetColors' : 'batchPresetColors';
    document.querySelectorAll('#' + gridId + ' .color-option').forEach(o => {
        o.classList.toggle('selected', o.dataset.color === color);
    });
}

// Bind events
function bindEvents() {
    // Refresh
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) refreshBtn.addEventListener('click', () => {
        currentSearchTerm = ''; currentStatusFilter = 'all'; currentSort = { field: null, direction: 'none' };
        const si = document.getElementById('searchInput'); if (si) si.value = '';
        const sf = document.getElementById('statusFilter'); if (sf) sf.value = 'all';
        document.querySelectorAll('th.sortable').forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
        loadData(); loadUsageRecords();
    });

    // Sub-nav tabs
    document.querySelectorAll('.sub-tab').forEach(tab => {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            const panelId = this.dataset.panel + 'Panel';
            const panel = document.getElementById(panelId);
            if (panel) { panel.classList.add('active'); }
            if (this.dataset.panel === 'reports' || this.dataset.panel === 'usage') {
                loadData();
                if (this.dataset.panel === 'usage') loadUsageRecords();
            }
        });
    });

    // Buttons
    const addBtn = document.getElementById('addFilamentBtn'); if (addBtn) addBtn.addEventListener('click', openAddModal);
    const batchBtn = document.getElementById('batchAddBtn'); if (batchBtn) batchBtn.addEventListener('click', openBatchAddModal);
    const exportBtn = document.getElementById('exportBtn'); if (exportBtn) exportBtn.addEventListener('click', exportData);
    const saveBtn = document.getElementById('saveFilamentBtn'); if (saveBtn) saveBtn.addEventListener('click', saveFilament);
    const saveBatchBtn = document.getElementById('saveBatchBtn'); if (saveBatchBtn) saveBatchBtn.addEventListener('click', saveBatch);
    const useBtn = document.getElementById('confirmUseBtn'); if (useBtn) useBtn.addEventListener('click', confirmUseFilament);
    const batchFav = document.getElementById('batchFavoriteBtn'); if (batchFav) batchFav.addEventListener('click', batchFavorite);
    const batchDel = document.getElementById('batchDeleteBtn'); if (batchDel) batchDel.addEventListener('click', batchDelete);
    const batchOpen = document.getElementById('batchMarkOpenedBtn'); if (batchOpen) batchOpen.addEventListener('click', () => batchUpdateStatus(true));
    const batchUnopen = document.getElementById('batchMarkUnopenedBtn'); if (batchUnopen) batchUnopen.addEventListener('click', () => batchUpdateStatus(false));
    const selectAll = document.getElementById('selectAll'); if (selectAll) selectAll.addEventListener('change', toggleSelectAll);

    // Search & filter
    const si = document.getElementById('searchInput');
    if (si) si.addEventListener('input', function () { currentSearchTerm = this.value.toLowerCase(); renderFilamentTable(applyFilters(filaments)); });
    const sf = document.getElementById('statusFilter');
    if (sf) sf.addEventListener('change', function () { currentStatusFilter = this.value; renderFilamentTable(applyFilters(filaments)); });

    // Is opened toggle
    const io = document.getElementById('isOpened');
    if (io) io.addEventListener('change', function () { document.getElementById('openedAtGroup').style.display = this.value === '1' ? 'block' : 'none'; });

    // Close modals
    document.querySelectorAll('.close-modal').forEach(btn => btn.addEventListener('click', closeAllModals));

    // Import
    const impBtn = document.getElementById('importBtn');
    if (impBtn) impBtn.addEventListener('click', () => {
        document.getElementById('importModal').style.display = 'flex';
        document.getElementById('importResults').style.display = 'none';
    });
    const confImp = document.getElementById('confirmImportBtn');
    if (confImp) confImp.addEventListener('click', function () {
        const fileInput = document.getElementById('csvFile');
        if (!fileInput.files.length) { alert('请选择要导入的CSV文件'); return; }
        const formData = new FormData(); formData.append('file', fileInput.files[0]);
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 导入中...'; this.disabled = true;
        fetch('/api/import', { method: 'POST', body: formData })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById('importResults').style.display = 'block';
                    document.getElementById('importAdded').textContent = data.added;
                    document.getElementById('importUpdated').textContent = data.updated;
                    document.getElementById('importSkipped').textContent = data.skipped;
                    document.getElementById('importTotal').textContent = data.added + data.updated + data.skipped;
                    setTimeout(() => { document.getElementById('importModal').style.display = 'none'; loadData(); }, 3000);
                } else {
                    const errEl = document.getElementById('importErrorLog');
                    errEl.style.display = 'block'; errEl.textContent = '错误: ' + (data.error || '未知错误');
                }
            })
            .catch(err => { console.error(err); alert('导入失败: ' + err.message); })
            .finally(() => { this.innerHTML = '<i class="fas fa-upload"></i> 开始导入'; this.disabled = false; });
    });

    // Sort headers
    document.querySelectorAll('th.sortable').forEach(th => {
        th.addEventListener('click', function () { toggleSort(this.dataset.sort); });
    });
}

// Sorting
function toggleSort(field) {
    document.querySelectorAll('th.sortable').forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
    const header = document.querySelector('th[data-sort="' + field + '"]');
    let newDir = 'asc';
    if (currentSort.field === field) {
        if (currentSort.direction === 'asc') newDir = 'desc';
        else if (currentSort.direction === 'desc') newDir = 'none';
    }
    currentSort.field = field; currentSort.direction = newDir;
    if (newDir === 'asc') header.classList.add('sort-asc');
    else if (newDir === 'desc') header.classList.add('sort-desc');
    renderFilamentTable(applyFilters(filaments));
}

function sortFilaments(data) {
    if (currentSort.direction === 'none') return data;
    const sorted = [...data];
    const dir = currentSort.direction === 'asc' ? 1 : -1;
    sorted.sort((a, b) => {
        let va, vb;
        switch (currentSort.field) {
            case 'name': va = a.name || ''; vb = b.name || ''; return va.localeCompare(vb) * dir;
            case 'material': va = a.material_type || ''; vb = b.material_type || ''; return va.localeCompare(vb) * dir;
            case 'color': va = a.color || ''; vb = b.color || ''; return va.localeCompare(vb) * dir;
            case 'manufacturer': va = a.manufacturer || ''; vb = b.manufacturer || ''; return va.localeCompare(vb) * dir;
            case 'weight': return (a.current_weight - b.current_weight) * dir;
            case 'location': va = a.location || ''; vb = b.location || ''; return va.localeCompare(vb) * dir;
            case 'status': return getStatusText(a).localeCompare(getStatusText(b)) * dir;
            default: return 0;
        }
    });
    return sorted;
}

// Render filament table
function renderFilamentTable(filaments) {
    const tbody = document.getElementById('filamentTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    selectedFilaments.clear();
    const selAll = document.getElementById('selectAll'); if (selAll) selAll.checked = false;
    const sorted = sortFilaments(filaments);
    if (sorted.length === 0) { tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">没有找到耗材记录</td></tr>'; return; }
    sorted.forEach(f => {
        const pct = f.initial_weight > 0 ? (f.current_weight / f.initial_weight) * 100 : 0;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><input type="checkbox" class="filament-checkbox" data-id="${f.id}"></td>
            <td class="hide-on-mobile">
                <i class="${f.is_favorite ? 'fas' : 'far'} fa-star favorite-btn" data-id="${f.id}" style="${f.is_favorite ? 'color:#ffc107;' : ''}"></i>
                ${f.name}
            </td>
            <td class="material-cell">${f.material_type}</td>
            <td><span class="color-indicator" style="background-color:${f.color};"></span></td>
            <td class="manufacturer-cell">${f.manufacturer || '-'}</td>
            <td class="weight-cell">
                <div class="mobile-hidden"><div>${f.current_weight}g / ${f.initial_weight}g</div>
                <div class="progress-container"><div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div></div></div>
                <span class="mobile-only">${f.current_weight}g</span>
            </td>
            <td class="hide-on-mobile">${f.location || '-'}</td>
            <td><span class="status-badge ${getStatusClass(f)}">${getStatusText(f)}</span></td>
            <td>
                <div class="action-buttons-container">
                    <i class="fas fa-edit action-btn" title="编辑" data-id="${f.id}"></i>
                    <i class="fas fa-eye action-btn" title="查看详情" data-id="${f.id}" style="color:#5b9bd5;"></i>
                    <i class="fas fa-minus-circle action-btn" title="使用耗材" style="color:var(--warning);" data-id="${f.id}"></i>
                    <i class="fas fa-trash action-btn" title="删除" style="color:#dc3545;" data-id="${f.id}"></i>
                </div>
            </td>`;
        tbody.appendChild(tr);
    });
    bindTableButtons();
}

// Render favorite cards
function renderFavoriteFilaments(filaments) {
    const grid = document.getElementById('favoriteFilamentsGrid');
    if (!grid) return;
    grid.innerHTML = '';
    const favs = filaments.filter(f => f.is_favorite);
    if (favs.length === 0) {
        grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:2rem;color:var(--text-muted);"><i class="fas fa-star" style="font-size:3rem;margin-bottom:1rem;"></i><p>没有常用耗材</p></div>';
        return;
    }
    favs.forEach(f => {
        const card = document.createElement('div');
        card.className = 'filament-card'; card.dataset.id = f.id;
        card.innerHTML = `
            <div class="filament-spool"><div class="spool-outer" style="background-color:${f.color};"><div class="spool-center"></div><div class="spool-hole hole-top"></div><div class="spool-hole hole-right"></div><div class="spool-hole hole-bottom"></div><div class="spool-hole hole-left"></div></div></div>
            <div class="filament-info"><div class="filament-manufacturer">${f.manufacturer}</div><div class="filament-material">${f.material_type}</div><div class="filament-weight ${f.current_weight <= 200 ? 'low' : ''}">${f.current_weight}g</div></div>
            <i class="fas fa-star action-icon"></i>`;
        grid.appendChild(card);
    });
    document.querySelectorAll('.filament-card').forEach(card => {
        card.addEventListener('click', function () { openUseModal(this.dataset.id); });
        card.addEventListener('mousedown', function (e) { const id = this.dataset.id; longPressTimer = setTimeout(() => openEditModal(id), 1000); });
        card.addEventListener('touchstart', function (e) { const id = this.dataset.id; longPressTimer = setTimeout(() => openEditModal(id), 1000); });
        card.addEventListener('mouseup', () => clearTimeout(longPressTimer));
        card.addEventListener('mouseleave', () => clearTimeout(longPressTimer));
        card.addEventListener('touchend', () => clearTimeout(longPressTimer));
    });
}

// Render manufacturer stats
function renderManufacturerStats(stats) {
    const grid = document.getElementById('manufacturerGrid');
    if (!grid) return;
    grid.innerHTML = '';
    if (!stats || stats.length === 0) {
        grid.innerHTML = '<div class="card" style="grid-column:1/-1;text-align:center;padding:2rem;"><i class="fas fa-inbox" style="font-size:3rem;color:var(--text-muted);margin-bottom:1rem;"></i><p>没有厂商数据</p></div>';
        return;
    }
    stats.forEach(s => {
        const card = document.createElement('div');
        card.className = 'card manufacturer-card'; card.dataset.manufacturer = s.manufacturer;
        card.innerHTML = `
            <div class="manufacturer-header"><div class="fa-filament"><i class="fas fa-box-open"></i></div>
            <div class="manufacturer-name">${s.manufacturer}${s.low_stock_count > 0 ? '<span class="low-stock-badge">'+s.low_stock_count+'卷库存不足</span>' : ''}${s.used_up_count > 0 ? '<span class="used-up-badge">'+s.used_up_count+'卷耗材用完</span>' : ''}</div></div>
            <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:1rem;">
                <div class="stat-card"><div class="stat-value-large">${s.total_filaments}</div><div class="stat-label-large">卷耗材</div></div>
                <div class="stat-card"><div class="stat-value-large">${s.distinct_materials}</div><div class="stat-label-large">材料类型</div></div>
                <div class="stat-card"><div class="stat-value-large">${s.distinct_colors}</div><div class="stat-label-large">颜色</div></div>
                <div class="stat-card"><div class="stat-value-large">${s.total_weight ? s.total_weight.toFixed(0) : '0'}</div><div class="stat-label-large">总克数</div></div>
            </div>
            <div class="value-card"><div class="stat-value-large">¥${s.total_value ? s.total_value.toFixed(2) : '0.00'}</div><div class="stat-label-large">耗材总价值</div></div>`;
        grid.appendChild(card);
    });
    document.querySelectorAll('.manufacturer-card').forEach(card => {
        card.addEventListener('click', function () {
            const mfr = this.dataset.manufacturer;
            currentSearchTerm = mfr;
            const si = document.getElementById('searchInput'); if (si) si.value = mfr;
            currentStatusFilter = 'all';
            const sf = document.getElementById('statusFilter'); if (sf) sf.value = 'all';
            renderFilamentTable(applyFilters(filaments));
            document.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
            const mgmtTab = document.querySelector('.sub-tab[data-panel="management"]');
            if (mgmtTab) mgmtTab.classList.add('active');
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            const mp = document.getElementById('managementPanel'); if (mp) mp.classList.add('active');
            window.scrollTo(0, 0);
        });
    });
}

// Render usage records
function renderUsageRecords(records) {
    const tbody = document.getElementById('usageTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (records.length === 0) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">没有使用记录</td></tr>'; return; }
    records.forEach(r => {
        const d = new Date(r.used_at);
        const ds = d.getFullYear()+'-'+(d.getMonth()+1).toString().padStart(2,'0')+'-'+d.getDate().toString().padStart(2,'0');
        const ts = d.getHours().toString().padStart(2,'0')+':'+d.getMinutes().toString().padStart(2,'0')+':'+d.getSeconds().toString().padStart(2,'0');
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${ds} ${ts}</td><td>${r.filament_name}</td><td>${r.used_weight}g</td><td>¥${r.used_cost ? r.used_cost.toFixed(2) : '0.00'}</td><td>${r.note || '-'}</td><td><button class="btn btn-danger btn-sm btn-withdraw" data-id="${r.id}"><i class="fas fa-undo"></i></button></td>`;
        tbody.appendChild(tr);
    });
    bindWithdrawButtons();
}

function bindWithdrawButtons() {
    document.querySelectorAll('.btn-withdraw').forEach(btn => {
        btn.addEventListener('click', function () { withdrawUsageRecord(this.dataset.id); });
    });
}

function withdrawUsageRecord(recordId) {
    if (!confirm('确定要撤回这条使用记录吗？撤回后使用重量将加回到耗材中。')) return;
    fetch('/api/usage_records/' + recordId, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'success') { alert('撤回成功！'); loadUsageRecords(); loadData(); }
            else alert('撤回失败: ' + (data.error || '未知错误'));
        })
        .catch(err => { alert('撤回失败: ' + err.message); });
}

// Render usage summary
function renderUsageSummary(records) {
    const el = document.getElementById('usageSummary');
    if (!el) return;
    el.innerHTML = '';
    if (records.length === 0) { el.innerHTML = '<p style="padding:1rem;color:var(--text-muted);">暂无使用数据</p>'; return; }
    let totalW = 0, totalC = 0;
    const daily = {};
    records.forEach(r => {
        totalW += r.used_weight; totalC += r.used_cost || 0;
        const date = new Date(r.used_at).toISOString().split('T')[0];
        if (!daily[date]) daily[date] = { weight: 0, cost: 0 };
        daily[date].weight += r.used_weight; daily[date].cost += r.used_cost || 0;
    });
    let html = '<table style="width:100%;margin-top:1rem;"><tr><th>日期</th><th>使用重量(g)</th><th>使用金额(¥)</th></tr>';
    Object.keys(daily).sort().reverse().forEach(date => {
        html += '<tr><td>'+date+'</td><td>'+daily[date].weight.toFixed(1)+'</td><td>¥'+daily[date].cost.toFixed(2)+'</td></tr>';
    });
    html += '</table>';
    el.innerHTML = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;"><div class="stat-card"><div class="stat-value">'+totalW.toFixed(1)+'g</div><div class="stat-label">总使用重量</div></div><div class="stat-card"><div class="stat-value">¥'+totalC.toFixed(2)+'</div><div class="stat-label">总使用金额</div></div></div><div class="card-header" style="margin-top:1.5rem;"><div class="card-title">每日使用汇总</div></div>'+html;
    updateDailyUsageChart(daily);
}

function updateDailyUsageChart(dailySummary) {
    const ctx = document.getElementById('dailyUsageChart');
    if (!ctx) return;
    if (dailyUsageChart) dailyUsageChart.destroy();
    const dates = Object.keys(dailySummary).sort();
    dailyUsageChart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                { label: '使用重量 (g)', data: dates.map(d => dailySummary[d].weight), backgroundColor: '#5b9bd5', yAxisID: 'y' },
                { label: '使用金额 (¥)', data: dates.map(d => dailySummary[d].cost), backgroundColor: '#f72585', type: 'line', yAxisID: 'y1' }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                y: { type: 'linear', display: true, position: 'left', title: { display: true, text: '重量 (g)' } },
                y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: '金额 (¥)' }, grid: { drawOnChartArea: false } }
            }
        }
    });
}

// Table buttons
function bindTableButtons() {
    document.querySelectorAll('.favorite-btn').forEach(btn => {
        btn.addEventListener('click', function () { toggleFavorite(this.dataset.id, !this.classList.contains('fas')); });
    });
    document.querySelectorAll('.fa-edit').forEach(btn => { btn.addEventListener('click', function () { openEditModal(this.dataset.id); }); });
    document.querySelectorAll('.fa-eye').forEach(btn => { btn.addEventListener('click', function () { openDetailModal(this.dataset.id); }); });
    document.querySelectorAll('.fa-minus-circle').forEach(btn => { btn.addEventListener('click', function () { openUseModal(this.dataset.id); }); });
    document.querySelectorAll('.fa-trash').forEach(btn => {
        btn.addEventListener('click', function () { if (confirm('确定要删除此耗材记录吗？此操作不可撤销。')) deleteFilament(this.dataset.id); });
    });
    document.querySelectorAll('.filament-checkbox').forEach(cb => {
        cb.addEventListener('change', function () {
            const id = parseInt(this.dataset.id);
            this.checked ? selectedFilaments.add(id) : selectedFilaments.delete(id);
            updateSelectAllState();
        });
    });
}

function updateSelectAllState() {
    const sa = document.getElementById('selectAll');
    if (!sa) return;
    const cbs = document.querySelectorAll('.filament-checkbox');
    sa.checked = selectedFilaments.size === cbs.length && cbs.length > 0;
    sa.indeterminate = selectedFilaments.size > 0 && selectedFilaments.size < cbs.length;
}

function toggleSelectAll() {
    selectedFilaments.clear();
    document.querySelectorAll('.filament-checkbox').forEach(cb => {
        cb.checked = this.checked;
        if (this.checked) selectedFilaments.add(parseInt(cb.dataset.id));
    });
}

// Render statistics
function renderStatistics(data) {
    const container = document.getElementById('statsGrid');
    if (!container) return;
    container.innerHTML = '';
    [{ title:'总耗材数量', icon:'fas fa-boxes', value:data.total_filaments, label:'卷', cls:'icon-primary' },
     { title:'耗材类型', icon:'fas fa-layer-group', value:data.material_types, label:'种材料类型', cls:'icon-primary' },
     { title:'库存预警', icon:'fas fa-exclamation-triangle', value:data.low_stock, label:'卷', cls:'icon-warning' },
     { title:'常用耗材', icon:'fas fa-star', value:data.favorites, label:'标记为常用', cls:'icon-primary' },
     { title:'库存总价值', icon:'fas fa-yen-sign', value:'¥'+data.total_value.toFixed(2), label:'耗材总价值', cls:'icon-primary' }
    ].forEach(c => {
        const card = document.createElement('div'); card.className = 'card';
        card.innerHTML = '<div class="card-header"><div class="card-title">'+c.title+'</div><div class="card-icon '+c.cls+'"><i class="'+c.icon+'"></i></div></div><div class="stat-value">'+c.value+'</div><div class="stat-label">'+c.label+'</div>';
        container.appendChild(card);
    });
    const alertEl = document.getElementById('lowStockAlert');
    if (alertEl) {
        if (data.low_stock > 0) {
            document.getElementById('lowStockMessage').innerHTML = '有 <strong>'+data.low_stock+'卷耗材</strong> 库存低于'+data.threshold+'克，请及时补充！';
            alertEl.style.display = 'flex';
        } else { alertEl.style.display = 'none'; }
    }
    updateCharts(data);
}

// Render reports
function renderReports(data) {
    const mrCtx = document.getElementById('materialChartReports');
    if (mrCtx) {
        if (materialChartReports) materialChartReports.destroy();
        materialChartReports = new Chart(mrCtx.getContext('2d'), {
            type: 'doughnut',
            data: { labels: Object.keys(data.material_distribution), datasets: [{ data: Object.values(data.material_distribution), backgroundColor: ['#5b9bd5','#3a0ca3','#4cc9f0','#f72585','#7209b7','#adb5bd'] }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }
        });
    }
    const srCtx = document.getElementById('statusChartReports');
    if (srCtx) {
        if (statusChartReports) statusChartReports.destroy();
        statusChartReports = new Chart(srCtx.getContext('2d'), {
            type: 'bar',
            data: { labels: ['库存充足','库存正常','库存不足','未开封'], datasets: [{ label:'耗材数量', data:[data.stock_status.sufficient,data.stock_status.normal,data.stock_status.insufficient,data.stock_status.unopened], backgroundColor:'#5b9bd5' }] },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
        });
    }
    const uCtx = document.getElementById('usageChart');
    if (uCtx) {
        if (usageChart) usageChart.destroy();
        const labels = data.usage_stats.map(i => i.month).reverse();
        const pts = data.usage_stats.map(i => i.total_used).reverse();
        usageChart = new Chart(uCtx.getContext('2d'), {
            type: 'line',
            data: { labels: labels, datasets: [{ label:'耗材使用量 (克)', data:pts, borderColor:'#f72585', backgroundColor:'rgba(247,37,133,0.1)', tension:0.3, fill:true }] },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
        });
    }
}

// Update dashboard charts
function updateCharts(data) {
    const mc = document.getElementById('materialChart');
    if (mc) {
        if (materialChart) materialChart.destroy();
        materialChart = new Chart(mc.getContext('2d'), {
            type: 'doughnut',
            data: { labels: Object.keys(data.material_distribution), datasets: [{ data: Object.values(data.material_distribution), backgroundColor: ['#5b9bd5','#3a0ca3','#4cc9f0','#f72585','#7209b7','#adb5bd'] }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }
        });
    }
    const sc = document.getElementById('statusChart');
    if (sc) {
        if (statusChart) statusChart.destroy();
        statusChart = new Chart(sc.getContext('2d'), {
            type: 'bar',
            data: { labels: ['库存充足','库存正常','库存不足','未开封'], datasets: [{ label:'耗材数量', data:[data.stock_status.sufficient,data.stock_status.normal,data.stock_status.insufficient,data.stock_status.unopened], backgroundColor:'#5b9bd5' }] },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
        });
    }
}

// Modal openers
function openAddModal() {
    currentEditId = null;
    document.getElementById('modalTitle').textContent = '添加新耗材';
    document.getElementById('filamentName').value = '';
    const mt = document.getElementById('materialType'); if (mt) mt.value = 'PLA Basic';
    const mfr = document.getElementById('manufacturer'); if (mfr) mfr.value = '拓竹';
    document.getElementById('colorPicker').value = '#5b9bd5';
    document.getElementById('colorPreview').style.backgroundColor = '#5b9bd5';
    document.getElementById('location').value = '';
    document.getElementById('isOpened').value = '0';
    document.getElementById('initialWeight').value = settings.default_weight || 1000;
    document.getElementById('currentWeight').value = settings.default_weight || 1000;
    document.getElementById('isFavorite').checked = false;
    document.getElementById('purchaseDate').value = '';
    document.getElementById('purchasePrice').value = '';
    document.getElementById('purchaseChannel').value = '';
    document.getElementById('openedAtGroup').style.display = 'none';
    document.getElementById('openedAt').value = '';
    document.getElementById('addModal').style.display = 'flex';
}

function openBatchAddModal() {
    const mt = document.getElementById('batchMaterialType'); if (mt) mt.value = 'PLA Basic';
    document.getElementById('batchColorPicker').value = '#5b9bd5';
    document.getElementById('batchColorPreview').style.backgroundColor = '#5b9bd5';
    const mfr = document.getElementById('batchManufacturer'); if (mfr) mfr.value = '拓竹';
    document.getElementById('batchLocation').value = '';
    document.getElementById('batchInitialWeight').value = settings.default_weight || 1000;
    document.getElementById('batchQuantity').value = '1';
    document.getElementById('batchNamePrefix').value = '';
    document.getElementById('batchPurchaseDate').value = '';
    document.getElementById('batchPurchasePrice').value = '';
    document.getElementById('batchPurchaseChannel').value = '';
    document.getElementById('batchAddModal').style.display = 'flex';
}

function openEditModal(filamentId) {
    const f = filaments.find(f => f.id == filamentId);
    if (!f) return;
    currentEditId = filamentId;
    document.getElementById('modalTitle').textContent = '编辑耗材';
    document.getElementById('filamentName').value = f.name;
    document.getElementById('manufacturer').value = f.manufacturer || '';
    document.getElementById('materialType').value = f.material_type;
    document.getElementById('colorPicker').value = f.color;
    document.getElementById('colorPreview').style.backgroundColor = f.color;
    document.getElementById('location').value = f.location || '';
    document.getElementById('isOpened').value = f.is_opened ? '1' : '0';
    document.getElementById('initialWeight').value = f.initial_weight;
    document.getElementById('currentWeight').value = f.current_weight;
    document.getElementById('isFavorite').checked = f.is_favorite;
    document.getElementById('purchaseDate').value = f.purchase_date || '';
    document.getElementById('purchasePrice').value = f.purchase_price || '';
    document.getElementById('purchaseChannel').value = f.purchase_channel || '';
    if (f.opened_at) document.getElementById('openedAt').value = f.opened_at;
    document.getElementById('openedAtGroup').style.display = f.is_opened ? 'block' : 'none';
    document.getElementById('addModal').style.display = 'flex';
}

function openUseModal(filamentId) {
    const f = filaments.find(f => f.id == filamentId);
    if (!f) return;
    currentUseId = filamentId;
    document.getElementById('useFilamentName').textContent = f.name + ' - ' + f.material_type + ' - ' + f.manufacturer;
    document.getElementById('currentWeightDisplay').textContent = f.current_weight;
    document.getElementById('usedWeight').value = '';
    document.getElementById('usedWeight').max = f.current_weight;
    document.getElementById('useNote').value = '';
    document.getElementById('useModal').style.display = 'flex';
}

function openDetailModal(filamentId) {
    const f = filaments.find(f => f.id == filamentId);
    if (!f) return;
    document.getElementById('detailName').textContent = f.name || '-';
    document.getElementById('detailMaterial').textContent = f.material_type || '-';
    document.getElementById('detailManufacturer').textContent = f.manufacturer || '-';
    document.getElementById('detailCurrentWeight').textContent = f.current_weight ? f.current_weight+'g' : '-';
    document.getElementById('detailInitialWeight').textContent = f.initial_weight ? f.initial_weight+'g' : '-';
    document.getElementById('detailPurchaseDate').textContent = f.purchase_date || '-';
    document.getElementById('detailPurchasePrice').textContent = f.purchase_price ? '¥'+f.purchase_price : '-';
    document.getElementById('detailPurchaseChannel').textContent = f.purchase_channel || '-';
    document.getElementById('detailOpenedStatus').textContent = f.is_opened ? '已开封' : '未开封';
    document.getElementById('detailOpenedDate').textContent = f.opened_at || '-';
    document.getElementById('detailLocation').textContent = f.location || '-';
    document.getElementById('detailColorPreview').style.backgroundColor = f.color;
    document.getElementById('detailColor').textContent = f.color || '-';
    const pct = f.initial_weight > 0 ? Math.round((f.current_weight/f.initial_weight)*100) : 0;
    document.getElementById('detailProgressText').textContent = pct+'%';
    document.getElementById('detailProgressBar').style.width = pct+'%';
    const el = document.getElementById('detailStatus');
    el.textContent = getStatusText(f); el.className = 'detail-status ' + getStatusClass(f);
    document.getElementById('detailModal').style.display = 'flex';
}

function closeAllModals() {
    ['addModal','batchAddModal','useModal','detailModal','importModal'].forEach(id => {
        const el = document.getElementById(id); if (el) el.style.display = 'none';
    });
}

// CRUD operations
function saveFilament() {
    const name = document.getElementById('filamentName').value;
    const mt = document.getElementById('materialType').value;
    const color = document.getElementById('colorPicker').value;
    if (!name || !mt || !color) { alert('请填写必填字段：耗材名称、材料类型和颜色'); return; }
    const data = {
        name, material_type: mt, color,
        manufacturer: document.getElementById('manufacturer').value,
        location: document.getElementById('location').value,
        is_opened: document.getElementById('isOpened').value === '1',
        initial_weight: parseFloat(document.getElementById('initialWeight').value),
        current_weight: parseFloat(document.getElementById('currentWeight').value),
        is_favorite: document.getElementById('isFavorite').checked,
        purchase_date: document.getElementById('purchaseDate').value || null,
        purchase_price: parseFloat(document.getElementById('purchasePrice').value) || null,
        purchase_channel: document.getElementById('purchaseChannel').value || null,
        opened_at: null
    };
    if (data.is_opened && document.getElementById('openedAt').value) data.opened_at = document.getElementById('openedAt').value;
    const url = currentEditId ? '/api/filaments/'+currentEditId : '/api/filaments';
    fetch(url, { method: currentEditId ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
        .then(r => r.json()).then(d => { if (d.status==='success') { closeAllModals(); loadData(); } else alert('保存失败: '+(d.error||'未知错误')); })
        .catch(err => { alert('保存失败: '+err.message); });
}

function saveBatch() {
    const mt = document.getElementById('batchMaterialType').value;
    const color = document.getElementById('batchColorPicker').value;
    const prefix = document.getElementById('batchNamePrefix').value;
    const qty = parseInt(document.getElementById('batchQuantity').value);
    if (!prefix || !mt || !color || qty < 1) { alert('请填写必填字段'); return; }
    const batch = [];
    for (let i=1; i<=qty; i++) batch.push({
        name: prefix, manufacturer: document.getElementById('batchManufacturer').value, material_type: mt, color,
        location: document.getElementById('batchLocation').value, is_opened: false,
        initial_weight: parseFloat(document.getElementById('batchInitialWeight').value),
        current_weight: parseFloat(document.getElementById('batchInitialWeight').value), is_favorite: false,
        purchase_date: document.getElementById('batchPurchaseDate').value || null,
        purchase_price: parseFloat(document.getElementById('batchPurchasePrice').value) || null,
        purchase_channel: document.getElementById('batchPurchaseChannel').value || null
    });
    fetch('/api/filaments/batch', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(batch) })
        .then(r=>r.json()).then(d=>{ if(d.status==='success'){closeAllModals();loadData();}else alert('批量添加失败: '+(d.error||'未知错误')); })
        .catch(err=>{alert('批量添加失败: '+err.message);});
}

function confirmUseFilament() {
    const w = parseFloat(document.getElementById('usedWeight').value);
    if (!w || w<=0) { alert('请输入有效的使用重量'); return; }
    fetch('/api/filaments/'+currentUseId+'/use', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({used_weight:w, note:document.getElementById('useNote').value})
    }).then(r=>r.json()).then(d=>{if(d.status==='success'){closeAllModals();loadData();loadUsageRecords();}else alert('操作失败: '+(d.error||'未知错误'));})
      .catch(err=>{alert('操作失败: '+err.message);});
}

function toggleFavorite(id, isFav) {
    fetch('/api/filaments/'+id, { method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({is_favorite:isFav}) })
        .then(r=>r.json()).then(d=>{if(d.status==='success')loadData();});
}

function batchFavorite() {
    if (selectedFilaments.size===0) { alert('请先选择要操作的耗材'); return; }
    Promise.all(Array.from(selectedFilaments).map(id =>
        fetch('/api/filaments/'+id, { method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({is_favorite:true}) })
    )).then(rs=>Promise.all(rs.map(r=>r.json()))).then(r=>{if(r.every(res=>res.status==='success')){loadData();alert('已标记'+r.length+'卷耗材为常用');}else alert('部分操作失败');});
}

function batchUpdateStatus(isOpened) {
    if (selectedFilaments.size===0) { alert('请先选择要操作的耗材'); return; }
    Promise.all(Array.from(selectedFilaments).map(id =>
        fetch('/api/filaments/'+id, { method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({is_opened:isOpened}) })
    )).then(rs=>Promise.all(rs.map(r=>r.json()))).then(r=>{if(r.every(res=>res.status==='success')){loadData();alert('已更新'+r.length+'卷耗材状态');}else alert('部分操作失败');});
}

function batchDelete() {
    if (selectedFilaments.size===0) { alert('请先选择要删除的耗材'); return; }
    if (!confirm('确定要删除选中的 '+selectedFilaments.size+' 卷耗材吗？此操作不可撤销。')) return;
    fetch('/api/filaments/delete-multiple', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ids:Array.from(selectedFilaments)}) })
        .then(r=>r.json()).then(d=>{if(d.status==='success'){loadData();alert('已删除 '+d.count+' 卷耗材');}else alert('删除失败: '+(d.error||'未知错误'));});
}

function deleteFilament(id) {
    fetch('/api/filaments/'+id, { method:'DELETE' }).then(r=>r.json()).then(d=>{if(d.status==='success')loadData();});
}

function exportData() {
    fetch('/api/export').then(r=>{if(r.ok)return r.blob();throw new Error('导出失败');}).then(blob=>{
        const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='filament_inventory.csv';
        document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(a.href);
    }).catch(err=>{alert('导出失败: '+err.message);});
}
