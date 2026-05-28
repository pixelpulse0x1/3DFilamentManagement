// Materials Management JS
let currentMaterialId = null;

document.addEventListener('DOMContentLoaded', function () {
    loadMaterials();
    document.getElementById('addMaterialBtn').addEventListener('click', openAddMaterial);
    document.getElementById('saveMaterialBtn').addEventListener('click', saveMaterial);
    document.getElementById('cancelMaterialBtn').addEventListener('click', closeMaterialModal);
    document.getElementById('closeMaterialModal').addEventListener('click', closeMaterialModal);
});

function loadMaterials() {
    fetch('/api/materials')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('materialsTableBody');
            if (!Array.isArray(data) || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><i class="fas fa-layer-group"></i><p>' + _i('no_materials_hint', '暂无耗材类型，点击上方按钮添加') + '</p></div></td></tr>';
                return;
            }
            tbody.innerHTML = '';
            data.forEach(m => {
                const tr = document.createElement('tr');
                tr.innerHTML = '<td>' + m.id + '</td><td>' + m.name + '</td><td>' + (m.description || '-') + '</td>' +
                    '<td><button class="btn btn-outline edit-mat-btn" data-id="' + m.id + '" data-name="' + m.name + '" data-desc="' + (m.description || '') + '" style="margin-right:4px;height:30px;font-size:0.8rem;"><i class="fas fa-edit"></i></button>' +
                    '<button class="btn btn-danger del-mat-btn" data-id="' + m.id + '" data-name="' + m.name + '" style="height:30px;font-size:0.8rem;"><i class="fas fa-trash"></i></button></td>';
                tbody.appendChild(tr);
            });
            document.querySelectorAll('.edit-mat-btn').forEach(b => b.addEventListener('click', function () { openEditMaterial(this.dataset.id, this.dataset.name, this.dataset.desc); }));
            document.querySelectorAll('.del-mat-btn').forEach(b => b.addEventListener('click', function () { deleteMaterial(this.dataset.id, this.dataset.name); }));
        })
        .catch(err => { showError(_i('msg_load_data_failed', '加载数据失败') + ': ' + err.message); });
}

function openAddMaterial() {
    currentMaterialId = null;
    document.getElementById('materialModalTitle').textContent = _i('material_add', '添加材料类型');
    document.getElementById('materialName').value = '';
    document.getElementById('materialDescription').value = '';
    document.getElementById('materialModal').style.display = 'flex';
}

function openEditMaterial(id, name, desc) {
    currentMaterialId = id;
    document.getElementById('materialModalTitle').textContent = _i('material_edit', '编辑材料类型');
    document.getElementById('materialName').value = name;
    document.getElementById('materialDescription').value = desc;
    document.getElementById('materialModal').style.display = 'flex';
}

function closeMaterialModal() {
    document.getElementById('materialModal').style.display = 'none';
    hideError();
}

function saveMaterial() {
    const name = document.getElementById('materialName').value.trim();
    if (!name) { alert(_i('msg_enter_material_name', '请输入材料名称')); return; }
    const desc = document.getElementById('materialDescription').value.trim();
    const url = currentMaterialId ? '/api/materials/' + currentMaterialId : '/api/materials';
    const method = currentMaterialId ? 'PUT' : 'POST';
    fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, description: desc }) })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { closeMaterialModal(); loadMaterials(); }
            else { showError(d.error || _i('msg_save_failed', '保存失败')); }
        })
        .catch(err => { showError(_i('msg_save_failed', '保存失败') + ': ' + err.message); });
}

function deleteMaterial(id, name) {
    if (!confirm(_i('confirm_delete_material', '确定要删除材料类型 "{name}" 吗？').replace('{name}', name))) return;
    fetch('/api/materials/' + id, { method: 'DELETE' })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { loadMaterials(); }
            else { showError(d.error || _i('msg_delete_failed', '删除失败')); }
        })
        .catch(err => { showError(_i('msg_delete_failed', '删除失败') + ': ' + err.message); });
}

function showError(msg) {
    const el = document.getElementById('materialError');
    el.textContent = msg; el.style.display = 'block';
}

function hideError() {
    const el = document.getElementById('materialError');
    if (el) el.style.display = 'none';
}
