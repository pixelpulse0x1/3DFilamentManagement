let currentEditBrandId = null;
let currentRenameOldName = '';
let allBrandsData = [];

document.addEventListener('DOMContentLoaded', function () {
    loadBrands();
    document.getElementById('addBrandBtn').addEventListener('click', openAdd);
    document.getElementById('saveBrandBtn').addEventListener('click', saveBrand);
    document.getElementById('cancelBrandBtn').addEventListener('click', closeModal);
    document.getElementById('saveRenameBtn').addEventListener('click', saveRename);
    document.getElementById('cancelRenameBtn').addEventListener('click', closeRenameModal);
    document.querySelectorAll('.close-modal').forEach(b => b.addEventListener('click', () => { closeModal(); closeRenameModal(); }));
});

function loadBrands() {
    fetch('/api/brands')
        .then(r => r.json())
        .then(data => {
            allBrandsData = data;
            const tree = {};
            data.forEach(b => {
                if (!tree[b.name]) tree[b.name] = { name: b.name, spools: [] };
                tree[b.name].spools.push(b);
            });
            const list = document.getElementById('brandNameList');
            list.innerHTML = '';
            Object.keys(tree).sort().forEach(name => {
                list.innerHTML += '<option value="' + name + '">';
            });
            renderTree(tree);
        });
}

function renderTree(tree) {
    const container = document.getElementById('brandTree');
    const names = Object.keys(tree).sort();
    if (!names.length) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-weight-scale"></i><p>' + _i('no_brands', '暂无品牌数据') + '</p></div>';
        return;
    }
    container.innerHTML = '';
    names.forEach(name => {
        const brand = tree[name];
        const spools = brand.spools;
        const brandId = 'brand-' + name.replace(/[^a-zA-Z0-9一-鿿]/g, '-');

        let spoolRows = '';
        spools.forEach(s => {
            spoolRows += [
                '<div class="spool-row">',
                '<div class="spool-detail">',
                '<span class="spool-type">' + s.spool_type + '</span>',
                '<span class="spool-weight">' + s.spool_weight + 'g</span>',
                '<span class="spool-remark">' + (s.remark || '-') + '</span>',
                '</div>',
                '<div class="spool-actions">',
                '<button class="btn btn-outline edit-s-btn" data-id="' + s.id + '" data-name="' + s.name + '" data-st="' + s.spool_type + '" data-sw="' + s.spool_weight + '" data-rm="' + (s.remark||'') + '"><i class="fas fa-edit"></i></button>',
                '<button class="btn btn-danger del-s-btn" data-id="' + s.id + '" data-name="' + s.name + '" data-st="' + s.spool_type + '"><i class="fas fa-trash"></i></button>',
                '</div></div>'
            ].join('');
        });

        const card = document.createElement('div');
        card.className = 'brand-tree-card';
        card.innerHTML = [
            '<div class="brand-tree-header" onclick="this.parentElement.classList.toggle(\'expanded\')">',
            '<div class="brand-tree-info">',
            '<i class="fas fa-chevron-right brand-tree-arrow"></i>',
            '<strong>' + name + '</strong>',
            '<span class="brand-spool-count">' + spools.length + ' ' + _i('spool_count_unit', '款盘型') + '</span>',
            '</div>',
            '<i class="fa-regular fa-pen-to-square btn-edit-brand-name" onclick="event.stopPropagation();openRenameBrand(\'' + name.replace(/'/g, "\\'") + '\')" title="' + _i('edit_brand_name_title', '编辑品牌名称') + '"></i>',
            '</div>',
            '<div class="brand-tree-body">' + spoolRows + '</div>'
        ].join('');
        container.appendChild(card);
    });

    document.querySelectorAll('.edit-s-btn').forEach(b => {
        b.addEventListener('click', function (e) {
            e.stopPropagation();
            openEdit(this.dataset.id, this.dataset.name, this.dataset.st, this.dataset.sw, this.dataset.rm);
        });
    });
    document.querySelectorAll('.del-s-btn').forEach(b => {
        b.addEventListener('click', function (e) {
            e.stopPropagation();
            deleteBrand(this.dataset.id, this.dataset.name + ' - ' + this.dataset.st);
        });
    });
}

function populateCloneDropdown() {
    const sel = document.getElementById('copySpoolSourceSelect');
    sel.innerHTML = '<option value="">' + _i('clone_from_existing_brand', '-- 从已有品牌/盘型中选择并克隆 --') + '</option>';
    allBrandsData.forEach(b => {
        sel.innerHTML += '<option value="' + b.id + '" data-spool-type="' + b.spool_type + '" data-spool-weight="' + b.spool_weight + '" data-remark="' + (b.remark||'') + '">【' + b.name + '】' + b.spool_type + ' (' + b.spool_weight + 'g)</option>';
    });
}

function onCloneSpool() {
    const sel = document.getElementById('copySpoolSourceSelect');
    const opt = sel.selectedOptions[0];
    if (!opt || !opt.value) return;
    document.getElementById('brandSpoolType').value = opt.dataset.spoolType || _i('spool_default', '标准盘');
    document.getElementById('brandSpoolWeight').value = opt.dataset.spoolWeight || '0';
    document.getElementById('brandRemark').value = opt.dataset.remark || '';
    sel.value = '';
}

function openAdd() {
    currentEditBrandId = null;
    document.getElementById('brandModalTitle').textContent = _i('add_brand_spool_title', '添加品牌/盘型');
    document.getElementById('brandName').value = '';
    document.getElementById('brandSpoolType').value = _i('spool_default', '标准盘');
    document.getElementById('brandSpoolWeight').value = '0';
    document.getElementById('brandRemark').value = '';
    populateCloneDropdown();
    document.getElementById('brandModal').style.display = 'flex';
}

function openEdit(id, name, st, sw, rm) {
    currentEditBrandId = id;
    document.getElementById('brandModalTitle').textContent = _i('edit_spool_title', '编辑盘型');
    document.getElementById('brandName').value = name;
    document.getElementById('brandSpoolType').value = st;
    document.getElementById('brandSpoolWeight').value = sw;
    document.getElementById('brandRemark').value = rm;
    populateCloneDropdown();
    document.getElementById('brandModal').style.display = 'flex';
}

function closeModal() { document.getElementById('brandModal').style.display = 'none'; }

function saveBrand() {
    const name = document.getElementById('brandName').value.trim();
    if (!name) { alert(_i('msg_enter_brand_name', '请输入品牌名称')); return; }
    const url = currentEditBrandId ? '/api/brands/' + currentEditBrandId : '/api/brands';
    fetch(url, {
        method: currentEditBrandId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name,
            spool_type: document.getElementById('brandSpoolType').value.trim() || _i('spool_default', '标准盘'),
            spool_weight: parseFloat(document.getElementById('brandSpoolWeight').value) || 0,
            remark: document.getElementById('brandRemark').value.trim(),
        })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { closeModal(); loadBrands(); }
            else alert(d.error || _i('msg_save_failed', '保存失败'));
        })
        .catch(err => alert(_i('msg_save_failed', '保存失败') + ': ' + err.message));
}

function deleteBrand(id, label) {
    if (!confirm(_i('confirm_delete_brand_item', '确定要删除「{label}」吗？').replace('{label}', label))) return;
    fetch('/api/brands/' + id, { method: 'DELETE' })
        .then(r => r.json())
        .then(d => { if (d.status === 'success') loadBrands(); else alert(d.error || _i('msg_delete_failed', '删除失败')); });
}

function openRenameBrand(oldName) {
    currentRenameOldName = oldName;
    document.getElementById('oldBrandNameDisplay').textContent = oldName;
    document.getElementById('newBrandName').value = oldName;
    document.getElementById('renameBrandMsg').style.display = 'none';
    document.getElementById('editBrandNameModal').style.display = 'flex';
}

function closeRenameModal() {
    document.getElementById('editBrandNameModal').style.display = 'none';
}

function saveRename() {
    const newName = document.getElementById('newBrandName').value.trim();
    if (!newName) { alert(_i('msg_enter_new_brand_name', '请输入新的品牌名称')); return; }
    if (newName === currentRenameOldName) { closeRenameModal(); return; }

    fetch('/api/brands/rename', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_name: currentRenameOldName, new_name: newName })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                closeRenameModal();
                loadBrands();
            } else {
                const el = document.getElementById('renameBrandMsg');
                el.textContent = d.error || _i('msg_rename_failed', '重命名失败');
                el.style.display = 'block';
                el.style.color = '#f72585';
            }
        })
        .catch(err => {
            const el = document.getElementById('renameBrandMsg');
            el.textContent = _i('msg_request_failed', '请求失败') + ': ' + err.message;
            el.style.display = 'block';
            el.style.color = '#f72585';
        });
}
