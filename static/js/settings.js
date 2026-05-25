// Settings Management JS
document.addEventListener('DOMContentLoaded', function () {
    loadSettings();
    loadBackgrounds();

    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
    document.getElementById('resetSettingsBtn').addEventListener('click', resetSettings);
    document.getElementById('uploadBgBtn').addEventListener('click', uploadBackground);

    // Migration bindings
    document.getElementById('migrateDbBtn').addEventListener('click', migrateDb);
    document.getElementById('migrateMaterialsBtn').addEventListener('click', migrateMaterials);
    document.getElementById('migrateManufacturersBtn').addEventListener('click', migrateManufacturers);
});

function loadSettings() {
    fetch('/api/settings')
        .then(r => r.json())
        .then(data => {
            document.getElementById('thresholdInput').value = data.threshold;
            document.getElementById('defaultWeightInput').value = data.default_weight;
        })
        .catch(err => { showSettingsMsg('加载设置失败: ' + err.message, 'error'); });
}

function saveSettings() {
    const threshold = parseFloat(document.getElementById('thresholdInput').value);
    const defaultWeight = parseFloat(document.getElementById('defaultWeightInput').value);
    if (!threshold || threshold <= 0 || !defaultWeight || defaultWeight <= 0) {
        showSettingsMsg('请输入有效的设置值', 'error'); return;
    }
    fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ threshold, default_weight: defaultWeight })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') showSettingsMsg('设置保存成功', 'success');
            else showSettingsMsg('保存失败: ' + (d.error || '未知错误'), 'error');
        })
        .catch(err => { showSettingsMsg('保存失败: ' + err.message, 'error'); });
}

function resetSettings() {
    if (!confirm('确定要恢复默认设置吗？')) return;
    document.getElementById('thresholdInput').value = 200;
    document.getElementById('defaultWeightInput').value = 1000;
    showSettingsMsg('已恢复默认值，请点击保存', 'success');
}

function showSettingsMsg(msg, type) {
    const el = document.getElementById('settingsMsg');
    el.textContent = msg; el.style.display = 'block';
    el.style.color = type === 'error' ? '#f72585' : '#4cc9f0';
    setTimeout(() => { el.style.display = 'none'; }, 3000);
}

function loadBackgrounds() {
    fetch('/api/settings/background')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('bgThumbnails');
            container.innerHTML = '';
            if (!data.backgrounds || data.backgrounds.length === 0) {
                container.innerHTML = '<div class="bg-placeholder">未上传任何背景图片</div>';
                return;
            }
            data.backgrounds.forEach(filename => {
                const isActive = filename === data.active;
                const thumb = document.createElement('div');
                thumb.className = 'bg-thumb' + (isActive ? ' active' : '');
                thumb.innerHTML = '<img src="/static/uploads/backgrounds/' + filename + '" alt="' + filename + '">' +
                    '<div class="bg-thumb-overlay">' +
                    (!isActive ? '<button class="btn btn-primary set-bg-btn" data-filename="' + filename + '">设为背景</button>' : '<span style="color:#4cc9f0;font-size:0.8rem;">当前使用</span>') +
                    '</div>';
                container.appendChild(thumb);
            });
            document.querySelectorAll('.set-bg-btn').forEach(b => {
                b.addEventListener('click', function () { setActiveBackground(this.dataset.filename); });
            });
        })
        .catch(err => { console.error('加载背景列表失败:', err); });
}

function uploadBackground() {
    const fileInput = document.getElementById('backgroundFile');
    if (!fileInput.files.length) { showBgMsg('请选择要上传的图片', 'error'); return; }
    const file = fileInput.files[0];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['jpg','jpeg','png','webp'].includes(ext)) { showBgMsg('仅支持 jpg、jpeg、png、webp 格式', 'error'); return; }
    const formData = new FormData();
    formData.append('file', file);
    const btn = document.getElementById('uploadBgBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 上传中...'; btn.disabled = true;
    fetch('/api/settings/background/upload', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { showBgMsg('上传成功', 'success'); fileInput.value = ''; loadBackgrounds(); }
            else showBgMsg(d.error || '上传失败', 'error');
        })
        .catch(err => { showBgMsg('上传失败: ' + err.message, 'error'); })
        .finally(() => { btn.innerHTML = '<i class="fas fa-upload"></i> 上传'; btn.disabled = false; });
}

function setActiveBackground(filename) {
    fetch('/api/settings/background/set', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                showBgMsg('背景已切换', 'success');
                loadBackgrounds();
                // Apply background to body
                if (filename) {
                    document.body.classList.add('has-background');
                    document.body.style.backgroundImage = 'url(/static/uploads/backgrounds/' + filename + ')';
                } else {
                    document.body.classList.remove('has-background');
                    document.body.style.backgroundImage = '';
                }
            } else showBgMsg(d.error || '设置失败', 'error');
        })
        .catch(err => { showBgMsg('设置失败: ' + err.message, 'error'); });
}

function showBgMsg(msg, type) {
    const el = document.getElementById('bgUploadMsg');
    el.textContent = msg; el.style.display = 'block';
    el.style.color = type === 'error' ? '#f72585' : '#4cc9f0';
    setTimeout(() => { el.style.display = 'none'; }, 3000);
}

// ─── Data Migration ───

function migrateDb() {
    const fileInput = document.getElementById('migrateDbFile');
    if (!fileInput.files.length) { showMigrateMsg('migrateDbMsg', '请选择 .db 数据库文件', 'error'); return; }
    const file = fileInput.files[0];
    if (!file.name.endsWith('.db')) { showMigrateMsg('migrateDbMsg', '请选择 .db 格式的数据库文件', 'error'); return; }

    const formData = new FormData();
    formData.append('file', file);
    const btn = document.getElementById('migrateDbBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 导入中...'; btn.disabled = true;

    fetch('/api/settings/migrate/db', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                let msg = '导入完成：' + d.added_filaments + ' 卷耗材';
                if (d.added_records > 0) msg += '，' + d.added_records + ' 条使用记录';
                if (d.updated_settings > 0) msg += '，已更新系统设置';
                if (d.errors && d.errors.length > 0) msg += '。错误: ' + d.errors.join('; ');
                showMigrateMsg('migrateDbMsg', msg, d.errors && d.errors.length > 0 ? 'error' : 'success');
                fileInput.value = '';
            } else {
                showMigrateMsg('migrateDbMsg', d.error || '导入失败', 'error');
            }
        })
        .catch(err => { showMigrateMsg('migrateDbMsg', '导入失败: ' + err.message, 'error'); })
        .finally(() => { btn.innerHTML = '<i class="fas fa-upload"></i> 导入数据库'; btn.disabled = false; });
}

function migrateMaterials() {
    const fileInput = document.getElementById('migrateMaterialsFile');
    if (!fileInput.files.length) { showMigrateMsg('migrateMaterialsMsg', '请选择 materials.txt 文件', 'error'); return; }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const btn = document.getElementById('migrateMaterialsBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 导入中...'; btn.disabled = true;

    fetch('/api/settings/migrate/materials', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                let msg = '导入完成：' + d.added + ' 个新增，' + d.skipped + ' 个已存在跳过';
                if (d.errors && d.errors.length > 0) msg += '。错误: ' + d.errors.join('; ');
                showMigrateMsg('migrateMaterialsMsg', msg, d.errors && d.errors.length > 0 ? 'error' : 'success');
                fileInput.value = '';
            } else {
                showMigrateMsg('migrateMaterialsMsg', d.error || '导入失败', 'error');
            }
        })
        .catch(err => { showMigrateMsg('migrateMaterialsMsg', '导入失败: ' + err.message, 'error'); })
        .finally(() => { btn.innerHTML = '<i class="fas fa-upload"></i> 导入材料'; btn.disabled = false; });
}

function migrateManufacturers() {
    const fileInput = document.getElementById('migrateManufacturersFile');
    if (!fileInput.files.length) { showMigrateMsg('migrateManufacturersMsg', '请选择 manufacturers.txt 文件', 'error'); return; }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const btn = document.getElementById('migrateManufacturersBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 导入中...'; btn.disabled = true;

    fetch('/api/settings/migrate/manufacturers', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                let msg = '导入完成：' + d.added + ' 个新增，' + d.skipped + ' 个已存在跳过';
                if (d.errors && d.errors.length > 0) msg += '。错误: ' + d.errors.join('; ');
                showMigrateMsg('migrateManufacturersMsg', msg, d.errors && d.errors.length > 0 ? 'error' : 'success');
                fileInput.value = '';
            } else {
                showMigrateMsg('migrateManufacturersMsg', d.error || '导入失败', 'error');
            }
        })
        .catch(err => { showMigrateMsg('migrateManufacturersMsg', '导入失败: ' + err.message, 'error'); })
        .finally(() => { btn.innerHTML = '<i class="fas fa-upload"></i> 导入品牌'; btn.disabled = false; });
}

function showMigrateMsg(elId, msg, type) {
    const el = document.getElementById(elId);
    el.textContent = msg; el.style.display = 'block';
    el.style.color = type === 'error' ? '#f72585' : '#4cc9f0';
}
