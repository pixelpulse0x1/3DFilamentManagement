// Device Management JS
let currentPrinterIdForSlot = null;
let currentSlotIdForBind = null;
let allAvailableFilaments = [];

document.addEventListener('DOMContentLoaded', function () {
    loadPrinters();
    loadPrinterModels();

    document.getElementById('addPrinterBtn').addEventListener('click', openAddPrinter);
    document.getElementById('savePrinterBtn').addEventListener('click', savePrinter);
    document.getElementById('saveSlotBtn').addEventListener('click', saveSlot);

    const searchInput = document.getElementById('bindSearchInput');
    if (searchInput) searchInput.addEventListener('input', filterBindList);

    document.querySelectorAll('.close-modal').forEach(b => b.addEventListener('click', closeDeviceModals));
});

function loadPrinterModels() {
    fetch('/api/printer_models')
        .then(r => r.json())
        .then(data => {
            const sel = document.getElementById('printerModel');
            sel.innerHTML = '<option value="">' + _i('select_model_placeholder', '请选择机型') + '</option>';
            const brands = {};
            data.forEach(m => { if (!brands[m.brand]) brands[m.brand] = []; brands[m.brand].push(m); });
            Object.keys(brands).sort().forEach(brand => {
                const og = document.createElement('optgroup');
                og.label = brand;
                brands[brand].forEach(m => {
                    og.innerHTML += '<option value="' + m.id + '">' + m.model_name + ' (' + m.bed_size + ')</option>';
                });
                sel.appendChild(og);
            });
        });
}

function loadPrinters() {
    fetch('/api/printers')
        .then(r => r.json())
        .then(data => {
            const grid = document.getElementById('printerGrid');
            const empty = document.getElementById('noPrinters');
            if (!Array.isArray(data) || data.length === 0) {
                grid.querySelectorAll('.printer-card').forEach(c => c.remove());
                if (empty) empty.style.display = 'block';
                return;
            }
            if (empty) empty.style.display = 'none';
            grid.querySelectorAll('.printer-card').forEach(c => c.remove());
            data.forEach(printer => renderPrinterCard(grid, printer));
        })
        .catch(err => console.error('Failed to load printers:', err));
}

function renderPrinterCard(grid, printer) {
    const card = document.createElement('div');
    card.className = 'printer-card';
    card.dataset.printerId = printer.id;

    let slotsHtml = '';
    (printer.slots || []).forEach(slot => {
        if (slot.filament) {
            const f = slot.filament;
            const pct = f.initial_weight > 0 ? Math.round((f.current_weight / f.initial_weight) * 100) : 0;
            const imageHtml = f.image_id && f.image_file
                ? '<img src="/uploads/filaments/' + f.image_file + '" class="filament-thumb" onclick="event.stopPropagation();openLightbox(\'/uploads/filaments/' + f.image_file + '\')" />'
                : '<div class="no-image-placeholder"><i class="fas fa-image"></i></div>';
            const brandDisplay = f.brand_name || '';
            slotsHtml += [
                '<div class="slot-card slot-occupied" data-slot-id="' + slot.id + '" style="border-left: 4px solid ' + f.color + ';">',
                '<div class="slot-filament-color" style="background:' + f.color + ';"></div>',
                '<div class="slot-filament-info">',
                '<div class="slot-filament-row">',
                imageHtml,
                '<div class="slot-filament-detail">',
                '<div class="slot-filament-name">' + brandDisplay + ' ' + (f.material_type || '') + '</div>',
                '<div class="slot-filament-weight">',
                '<span>' + f.current_weight.toFixed(2) + 'g / ' + f.initial_weight.toFixed(2) + 'g</span>',
                '<div class="progress-bar"><div class="progress-fill" style="width:' + pct + '%"></div></div>',
                '</div></div></div></div>',
                '<button class="btn use-slot-btn" data-filament-id="' + f.id + '" title="' + _i('title_use_filament', '使用耗材') + '"><i class="fas fa-minus-circle"></i></button>',
                '<button class="btn btn-withdraw unbind-btn" data-slot-id="' + slot.id + '" title="' + _i('device_unbind', '下机解绑') + '"><i class="fas fa-eject"></i></button>',
                '</div>'
            ].join('');
        } else {
            slotsHtml += [
                '<div class="slot-card slot-empty" data-slot-id="' + slot.id + '">',
                '<div class="slot-placeholder">',
                '<i class="fas fa-plus-circle"></i>',
                '<span>' + slot.slot_name + '</span>',
                '</div></div>'
            ].join('');
        }
    });

    card.innerHTML = [
        '<div class="printer-card-header">',
        '<div class="printer-info">',
        '<i class="fas fa-print"></i>',
        '<div>',
        '<div class="printer-name">' + printer.name + '</div>',
        '<div class="printer-model">' + (printer.model || '-') + '</div>',
        '</div></div>',
        '<div class="printer-actions">',
        '<button class="btn btn-outline add-slot-btn" data-printer-id="' + printer.id + '" data-printer-name="' + printer.name + '">',
        '<i class="fas fa-plus"></i> ' + _i('slot_button_label', '槽位') + '</button>',
        '<button class="btn btn-danger del-printer-btn" data-printer-id="' + printer.id + '" data-printer-name="' + printer.name + '">',
        '<i class="fas fa-trash"></i></button>',
        '</div></div>',
        '<div class="slots-grid">' + (slotsHtml || '<div class="slot-hint">' + _i('no_slots_hint', '暂无槽位，点击「槽位」按钮添加') + '</div>') + '</div>'
    ].join('');

    grid.appendChild(card);

    card.querySelector('.add-slot-btn').addEventListener('click', function () {
        openAddSlot(this.dataset.printerId, this.dataset.printerName);
    });
    card.querySelector('.del-printer-btn').addEventListener('click', function () {
        deletePrinter(this.dataset.printerId, this.dataset.printerName);
    });
    card.querySelectorAll('.slot-empty').forEach(el => {
        el.addEventListener('click', function () {
            openBindFilament(this.dataset.slotId);
        });
    });
    card.querySelectorAll('.unbind-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            unbindFilament(this.dataset.slotId);
        });
    });
    card.querySelectorAll('.use-slot-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            openUseFromSlot(this.dataset.filamentId);
        });
    });
}

function openAddPrinter() {
    document.getElementById('printerName').value = '';
    document.getElementById('printerModel').value = '';
    document.getElementById('addPrinterModal').style.display = 'flex';
}

function savePrinter() {
    const name = document.getElementById('printerName').value.trim();
    if (!name) { alert(_i('msg_enter_printer_name', '请输入打印机名称')); return; }
    const modelId = parseInt(document.getElementById('printerModel').value) || null;
    fetch('/api/printers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, model_id: modelId })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { closeDeviceModals(); loadPrinters(); }
            else alert(d.error || _i('msg_add_failed', '添加失败'));
        })
        .catch(err => alert(_i('msg_add_failed', '添加失败') + ': ' + err.message));
}

function deletePrinter(id, name) {
    if (!confirm(_i('confirm_delete_printer', '确定要删除打印机「{name}」及其所有槽位吗？绑定的耗材将自动下机。').replace('{name}', name))) return;
    fetch('/api/printers/' + id, { method: 'DELETE' })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') loadPrinters();
            else alert(d.error || _i('msg_delete_failed', '删除失败'));
        })
        .catch(err => alert(_i('msg_delete_failed', '删除失败') + ': ' + err.message));
}

function openAddSlot(printerId, printerName) {
    currentPrinterIdForSlot = printerId;
    document.getElementById('slotPrinterName').textContent = printerName;
    document.getElementById('slotName').value = '';
    document.getElementById('addSlotModal').style.display = 'flex';
}

function saveSlot() {
    const slotName = document.getElementById('slotName').value.trim();
    if (!slotName) { alert(_i('msg_enter_slot_name', '请输入槽位名称')); return; }
    fetch('/api/printers/' + currentPrinterIdForSlot + '/slots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot_name: slotName })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { closeDeviceModals(); loadPrinters(); }
            else alert(d.error || _i('msg_add_failed', '添加失败'));
        })
        .catch(err => alert(_i('msg_add_failed', '添加失败') + ': ' + err.message));
}

function openBindFilament(slotId) {
    currentSlotIdForBind = slotId;
    const slotEl = document.querySelector('[data-slot-id="' + slotId + '"]');
    const slotName = slotEl ? slotEl.querySelector('.slot-placeholder span').textContent : '';
    document.getElementById('bindSlotName').textContent = slotName;
    document.getElementById('bindSearchInput').value = '';

    fetch('/api/filaments')
        .then(r => r.json())
        .then(data => {
            allAvailableFilaments = data.filter(f => f.status === '全新' || f.status === '闲置');
            renderBindList(allAvailableFilaments);
        })
        .catch(err => console.error('Failed to load filaments:', err));

    document.getElementById('bindFilamentModal').style.display = 'flex';
}

function renderBindList(filaments) {
    const container = document.getElementById('bindFilamentList');
    container.innerHTML = '';
    if (!filaments || filaments.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-cube"></i><p>' + _i('no_available_filaments_hint', '暂无可用的耗材（需要「全新」或「闲置」状态）') + '</p></div>';
        return;
    }
    filaments.forEach(f => {
        const item = document.createElement('div');
        item.className = 'bind-filament-item';
        const brandDisplay = f.brand_name || '';
        item.innerHTML = '<span class="color-indicator" style="background-color:' + f.color + ';"></span>' +
            '<div class="bind-filament-detail">' +
            '<strong>' + brandDisplay + ' ' + f.material_type + '</strong>' +
            '<small>' + f.name + ' · ' + f.current_weight.toFixed(2) + 'g · ' + _statusI18n(f.status) + '</small>' +
            '</div>';
        item.addEventListener('click', () => bindFilament(currentSlotIdForBind, f.id));
        container.appendChild(item);
    });
}

function filterBindList() {
    const term = document.getElementById('bindSearchInput').value.toLowerCase();
    const filtered = allAvailableFilaments.filter(f =>
        f.name.toLowerCase().includes(term) ||
        f.material_type.toLowerCase().includes(term) ||
        (f.brand_name && f.brand_name.toLowerCase().includes(term))
    );
    renderBindList(filtered);
}

function bindFilament(slotId, filamentId) {
    fetch('/api/slots/' + slotId + '/bind', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filament_id: filamentId })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { closeDeviceModals(); loadPrinters(); }
            else alert(d.error || _i('msg_bind_failed', '绑定失败'));
        })
        .catch(err => alert(_i('msg_bind_failed', '绑定失败') + ': ' + err.message));
}

function unbindFilament(slotId) {
    if (!confirm(_i('confirm_unbind_slot', '确定要对该槽位执行下机解绑吗？'))) return;
    fetch('/api/slots/' + slotId + '/unbind', { method: 'PUT' })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') loadPrinters();
            else alert(d.error || _i('msg_unbind_failed', '解绑失败'));
        })
        .catch(err => alert(_i('msg_unbind_failed', '解绑失败') + ': ' + err.message));
}

function openUseFromSlot(filamentId) {
    if (typeof openUseModal === 'function') {
        openUseModal(filamentId);
    }
}

function closeDeviceModals() {
    ['addPrinterModal', 'addSlotModal', 'bindFilamentModal'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
}
