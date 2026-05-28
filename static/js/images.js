// Image Assets Management JS
let currentEditImageId = null;
let pendingAction = null;
let pendingImageId = null;

document.addEventListener('DOMContentLoaded', function () {
    loadImages();

    document.getElementById('addImageBtn').addEventListener('click', openAddImage);
    document.getElementById('saveImageBtn').addEventListener('click', saveImage);
    document.getElementById('imageFile').addEventListener('change', onFileSelected);
    document.getElementById('confirmRiskBtn').addEventListener('click', executePendingAction);
    document.getElementById('cancelRiskBtn').addEventListener('click', closeRiskModal);

    document.querySelectorAll('#imageModal .close-modal, #confirmRiskModal .close-modal').forEach(b => {
        b.addEventListener('click', closeAllModals);
    });
});

function loadImages() {
    fetch('/api/images')
        .then(r => r.json())
        .then(data => {
            const grid = document.getElementById('imageGrid');
            grid.querySelectorAll('.image-card').forEach(c => c.remove());
            const empty = document.getElementById('noImages');
            if (!data || data.length === 0) {
                if (empty) empty.style.display = 'block';
                return;
            }
            if (empty) empty.style.display = 'none';
            data.forEach(img => {
                const card = document.createElement('div');
                card.className = 'image-card';
                card.innerHTML = [
                    '<div class="image-card-preview">',
                    '<img src="/uploads/filaments/' + img.file_name + '" alt="' + img.name + '" loading="lazy">',
                    '</div>',
                    '<div class="image-card-info">',
                    '<div class="image-card-name" title="' + img.name + '">' + img.name + '</div>',
                    '<div class="image-card-meta">',
                    '<span class="image-ref-count ' + (img.ref_count > 0 ? 'has-refs' : '') + '">',
                    '<i class="fas fa-link"></i> ' + _i('filament_ref_count', '{count} 卷耗材引用').replace('{count}', img.ref_count),
                    '</span></div></div>',
                    '<div class="image-card-actions">',
                    '<button class="btn btn-outline edit-img-btn" data-id="' + img.id + '" data-name="' + img.name + '" data-ref="' + img.ref_count + '"><i class="fas fa-edit"></i></button>',
                    '<button class="btn btn-danger del-img-btn" data-id="' + img.id + '" data-name="' + img.name + '" data-ref="' + img.ref_count + '"><i class="fas fa-trash"></i></button>',
                    '</div>'
                ].join('');
                grid.appendChild(card);
            });

            document.querySelectorAll('.edit-img-btn').forEach(b => {
                b.addEventListener('click', function () {
                    openEditImage(this.dataset.id, this.dataset.name, parseInt(this.dataset.ref));
                });
            });
            document.querySelectorAll('.del-img-btn').forEach(b => {
                b.addEventListener('click', function () {
                    deleteImage(this.dataset.id, this.dataset.name, parseInt(this.dataset.ref));
                });
            });
        })
        .catch(err => console.error(_i('msg_load_images_failed', '加载实物图失败') + ':', err));
}

function openAddImage() {
    currentEditImageId = null;
    document.getElementById('imageModalTitle').textContent = _i('upload_image_title', '上传实物图');
    document.getElementById('imageName').value = '';
    document.getElementById('imageFile').value = '';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('imageMsg').style.display = 'none';
    document.getElementById('imageModal').style.display = 'flex';
}

function openEditImage(id, name, refCount) {
    if (refCount > 0) {
        pendingAction = 'edit';
        pendingImageId = id;
        document.getElementById('confirmRiskMessage').innerHTML =
            _i('image_ref_replace_warning', '该实物图「<strong>{name}</strong>」当前正被 <strong>{count}</strong> 卷耗材使用，修改或替换图片将同步影响这些耗材的显示。').replace('{name}', name).replace('{count}', refCount);
        document.getElementById('confirmRiskModal').style.display = 'flex';
        return;
    }
    _doOpenEdit(id, name);
}

function _doOpenEdit(id, name) {
    currentEditImageId = id;
    document.getElementById('imageModalTitle').textContent = _i('edit_image_title', '编辑实物图');
    document.getElementById('imageName').value = name;
    document.getElementById('imageFile').value = '';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('imageMsg').style.display = 'none';
    document.getElementById('imageModal').style.display = 'flex';
}

function onFileSelected() {
    const file = this.files[0];
    const preview = document.getElementById('imagePreview');
    const img = document.getElementById('previewImg');
    if (file) {
        const url = URL.createObjectURL(file);
        img.src = url;
        preview.style.display = 'block';
    } else {
        preview.style.display = 'none';
    }
}

function saveImage() {
    const name = document.getElementById('imageName').value.trim();
    if (!name) { showImageMsg(_i('msg_enter_image_name', '请输入图片名称'), 'error'); return; }

    const fileInput = document.getElementById('imageFile');
    const formData = new FormData();
    formData.append('name', name);
    if (fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
    } else if (currentEditImageId) {
        showImageMsg(_i('msg_select_file', '请选择要上传的文件'), 'error'); return;
    }

    const url = currentEditImageId
        ? '/api/images/' + currentEditImageId
        : '/api/images/upload';
    const method = currentEditImageId ? 'PUT' : 'POST';

    const btn = document.getElementById('saveImageBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + _i('saving', '保存中...'); btn.disabled = true;

    fetch(url, { method, body: formData })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                closeAllModals();
                loadImages();
            } else {
                showImageMsg(d.error || _i('msg_save_failed', '保存失败'), 'error');
            }
        })
        .catch(err => showImageMsg(_i('msg_save_failed', '保存失败') + ': ' + err.message, 'error'))
        .finally(() => { btn.innerHTML = '<i class="fas fa-save"></i> ' + _i('btn_save', '保存'); btn.disabled = false; });
}

function deleteImage(id, name, refCount) {
    if (refCount > 0) {
        pendingAction = 'delete';
        pendingImageId = id;
        document.getElementById('confirmRiskMessage').innerHTML =
            _i('image_ref_delete_warning', '该实物图「<strong>{name}</strong>」当前正被 <strong>{count}</strong> 卷耗材使用，执行删除将同步影响这些耗材的显示。').replace('{name}', name).replace('{count}', refCount);
        document.getElementById('confirmRiskModal').style.display = 'flex';
        return;
    }
    _doDelete(id);
}

function _doDelete(id) {
    if (!confirm(_i('confirm_delete_image', '确定要删除该实物图吗？'))) return;
    fetch('/api/images/' + id, { method: 'DELETE' })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') loadImages();
            else alert(d.error || _i('msg_delete_failed', '删除失败'));
        })
        .catch(err => alert(_i('msg_delete_failed', '删除失败') + ': ' + err.message));
}

function executePendingAction() {
    closeRiskModal();
    if (pendingAction === 'delete') {
        _doDelete(pendingImageId);
    } else if (pendingAction === 'edit') {
        const btn = document.querySelector('.edit-img-btn[data-id="' + pendingImageId + '"]');
        _doOpenEdit(pendingImageId, btn ? btn.dataset.name : '');
    }
    pendingAction = null;
    pendingImageId = null;
}

function closeRiskModal() {
    document.getElementById('confirmRiskModal').style.display = 'none';
}

function showImageMsg(msg, type) {
    const el = document.getElementById('imageMsg');
    el.textContent = msg; el.style.display = 'block';
    el.style.color = type === 'error' ? '#f72585' : '#4cc9f0';
    setTimeout(() => { el.style.display = 'none'; }, 3000);
}

function closeAllModals() {
    document.getElementById('imageModal').style.display = 'none';
    document.getElementById('confirmRiskModal').style.display = 'none';
}
