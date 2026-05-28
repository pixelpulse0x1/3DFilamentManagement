// Manufacturers Management JS
let currentManufacturerId = null;

document.addEventListener('DOMContentLoaded', function () {
    loadManufacturers();
    document.getElementById('addManufacturerBtn').addEventListener('click', openAddManufacturer);
    document.getElementById('saveManufacturerBtn').addEventListener('click', saveManufacturer);
    document.getElementById('cancelManufacturerBtn').addEventListener('click', closeManufacturerModal);
    document.getElementById('closeManufacturerModal').addEventListener('click', closeManufacturerModal);
});

function loadManufacturers() {
    fetch('/api/manufacturers')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('manufacturersTableBody');
            if (!Array.isArray(data) || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><i class="fas fa-tag"></i><p>' + _i('no_brands_hint', '暂无品牌，点击上方按钮添加') + '</p></div></td></tr>';
                return;
            }
            tbody.innerHTML = '';
            data.forEach(m => {
                const tr = document.createElement('tr');
                tr.innerHTML = '<td>' + m.id + '</td><td>' + m.name + '</td><td>' + (m.website || '-') + '</td>' +
                    '<td><button class="btn btn-outline edit-mfr-btn" data-id="' + m.id + '" data-name="' + m.name + '" data-website="' + (m.website || '') + '" style="margin-right:4px;height:30px;font-size:0.8rem;"><i class="fas fa-edit"></i></button>' +
                    '<button class="btn btn-danger del-mfr-btn" data-id="' + m.id + '" data-name="' + m.name + '" style="height:30px;font-size:0.8rem;"><i class="fas fa-trash"></i></button></td>';
                tbody.appendChild(tr);
            });
            document.querySelectorAll('.edit-mfr-btn').forEach(b => b.addEventListener('click', function () { openEditManufacturer(this.dataset.id, this.dataset.name, this.dataset.website); }));
            document.querySelectorAll('.del-mfr-btn').forEach(b => b.addEventListener('click', function () { deleteManufacturer(this.dataset.id, this.dataset.name); }));
        })
        .catch(err => { showError(_i('msg_load_data_failed', '加载数据失败') + ': ' + err.message); });
}

function openAddManufacturer() {
    currentManufacturerId = null;
    document.getElementById('manufacturerModalTitle').textContent = _i('add_brand_title', '添加品牌');
    document.getElementById('manufacturerName').value = '';
    document.getElementById('manufacturerWebsite').value = '';
    document.getElementById('manufacturerModal').style.display = 'flex';
}

function openEditManufacturer(id, name, website) {
    currentManufacturerId = id;
    document.getElementById('manufacturerModalTitle').textContent = _i('edit_brand_title', '编辑品牌');
    document.getElementById('manufacturerName').value = name;
    document.getElementById('manufacturerWebsite').value = website;
    document.getElementById('manufacturerModal').style.display = 'flex';
}

function closeManufacturerModal() {
    document.getElementById('manufacturerModal').style.display = 'none';
    hideError();
}

function saveManufacturer() {
    const name = document.getElementById('manufacturerName').value.trim();
    if (!name) { alert(_i('msg_enter_brand_name', '请输入品牌名称')); return; }
    const website = document.getElementById('manufacturerWebsite').value.trim();
    const url = currentManufacturerId ? '/api/manufacturers/' + currentManufacturerId : '/api/manufacturers';
    const method = currentManufacturerId ? 'PUT' : 'POST';
    fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, website }) })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { closeManufacturerModal(); loadManufacturers(); }
            else { showError(d.error || _i('msg_save_failed', '保存失败')); }
        })
        .catch(err => { showError(_i('msg_save_failed', '保存失败') + ': ' + err.message); });
}

function deleteManufacturer(id, name) {
    if (!confirm(_i('confirm_delete_brand', '确定要删除品牌 "{name}" 吗？').replace('{name}', name))) return;
    fetch('/api/manufacturers/' + id, { method: 'DELETE' })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { loadManufacturers(); }
            else { showError(d.error || _i('msg_delete_failed', '删除失败')); }
        })
        .catch(err => { showError(_i('msg_delete_failed', '删除失败') + ': ' + err.message); });
}

function showError(msg) {
    const el = document.getElementById('manufacturerError');
    el.textContent = msg; el.style.display = 'block';
}

function hideError() {
    const el = document.getElementById('manufacturerError');
    if (el) el.style.display = 'none';
}
