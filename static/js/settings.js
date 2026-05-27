// Settings Management JS — supports general, appearance, and advanced pages
document.addEventListener('DOMContentLoaded', function () {
    // General page
    if (document.getElementById('thresholdInput')) {
        loadGeneralSettings();
        document.getElementById('saveSettingsBtn').addEventListener('click', saveGeneralSettings);
        document.getElementById('resetSettingsBtn').addEventListener('click', resetGeneralSettings);
    }

    // Appearance page
    if (document.getElementById('cardOpacitySlider')) {
        loadAppearanceSettings();
        document.getElementById('cardOpacitySlider').addEventListener('input', onOpacityChange);
        document.getElementById('cardColorPicker').addEventListener('input', onColorChange);
        document.getElementById('cardBlurSlider').addEventListener('input', onBlurChange);
        document.getElementById('saveAppearanceBtn').addEventListener('click', saveAppearanceSettings);
        document.getElementById('resetAppearanceBtn').addEventListener('click', resetAppearanceSettings);
        document.getElementById('uploadBgBtn').addEventListener('click', uploadBackground);
        loadBackgrounds();
    }

    // Advanced page
    if (document.getElementById('systemStatus')) {
        loadSystemStatus();
    }
    if (document.getElementById('backupBtn')) {
        document.getElementById('backupBtn').addEventListener('click', triggerBackup);
    }
    if (document.getElementById('exportExcelBtn')) {
        document.getElementById('exportExcelBtn').addEventListener('click', triggerExcelExport);
    }
});

// ─── General Settings ───

function loadGeneralSettings() {
    fetch('/api/settings')
        .then(r => r.json())
        .then(data => {
            document.getElementById('thresholdInput').value = data.threshold;
            document.getElementById('defaultWeightInput').value = data.default_weight;
        })
        .catch(err => { showMsg('settingsMsg', '加载设置失败: ' + err.message, 'error'); });
}

function saveGeneralSettings() {
    const threshold = parseFloat(document.getElementById('thresholdInput').value);
    const defaultWeight = parseFloat(document.getElementById('defaultWeightInput').value);
    if (!threshold || threshold <= 0 || !defaultWeight || defaultWeight <= 0) {
        showMsg('settingsMsg', '请输入有效的设置值', 'error'); return;
    }
    fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ threshold, default_weight: defaultWeight })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') showMsg('settingsMsg', '设置保存成功', 'success');
            else showMsg('settingsMsg', '保存失败: ' + (d.error || '未知错误'), 'error');
        })
        .catch(err => { showMsg('settingsMsg', '保存失败: ' + err.message, 'error'); });
}

function resetGeneralSettings() {
    if (!confirm('确定要恢复默认设置吗？')) return;
    document.getElementById('thresholdInput').value = 200;
    document.getElementById('defaultWeightInput').value = 1000;
    showMsg('settingsMsg', '已恢复默认值，请点击保存', 'success');
}

// ─── Appearance Settings ───

function loadAppearanceSettings() {
    fetch('/api/settings')
        .then(r => r.json())
        .then(data => {
            const opacity = data.card_opacity !== undefined ? data.card_opacity : 0.05;
            const color = data.card_color || '#ffffff';
            const blur = data.card_blur !== undefined ? data.card_blur : 2;
            document.getElementById('cardOpacitySlider').value = Math.round(opacity * 100);
            document.getElementById('opacityValue').textContent = Math.round(opacity * 100) + '%';
            document.getElementById('cardColorPicker').value = color;
            document.getElementById('cardColorHex').textContent = color;
            document.getElementById('cardBlurSlider').value = blur;
            document.getElementById('blurValue').textContent = blur + 'px';
            applyAppearancePreview(opacity, color, blur);
        })
        .catch(err => { showMsg('appearanceMsg', '加载外观设置失败: ' + err.message, 'error'); });
}

function onOpacityChange() {
    const pct = parseInt(this.value);
    document.getElementById('opacityValue').textContent = pct + '%';
    const opacity = pct / 100;
    const color = document.getElementById('cardColorPicker').value;
    const blur = parseInt(document.getElementById('cardBlurSlider').value);
    applyAppearancePreview(opacity, color, blur);
}

function onColorChange() {
    const color = this.value;
    document.getElementById('cardColorHex').textContent = color;
    const pct = parseInt(document.getElementById('cardOpacitySlider').value);
    const opacity = pct / 100;
    const blur = parseInt(document.getElementById('cardBlurSlider').value);
    applyAppearancePreview(opacity, color, blur);
}

function onBlurChange() {
    const blur = parseInt(this.value);
    document.getElementById('blurValue').textContent = blur + 'px';
    const pct = parseInt(document.getElementById('cardOpacitySlider').value);
    const opacity = pct / 100;
    const color = document.getElementById('cardColorPicker').value;
    applyAppearancePreview(opacity, color, blur);
}

function applyAppearancePreview(opacity, color, blur) {
    const hex = /^#[0-9a-fA-F]{6}$/.test(color) ? color : '#ffffff';
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    document.documentElement.style.setProperty('--ha-card-bg', `rgba(${r}, ${g}, ${b}, ${opacity})`);

    // Perceived luminance: blend card color over dark base (#101E2E ≈ 16,30,46)
    const effR = r * opacity + 16 * (1 - opacity);
    const effG = g * opacity + 30 * (1 - opacity);
    const effB = b * opacity + 46 * (1 - opacity);
    const luminance = 0.299 * effR + 0.587 * effG + 0.114 * effB;
    document.documentElement.style.setProperty('--ha-card-color', luminance > 128 ? '#111111' : '#ffffff');

    if (blur !== undefined && blur !== null) {
        document.documentElement.style.setProperty('--ha-card-blur', blur + 'px');
    }
}

function saveAppearanceSettings() {
    const opacity = parseInt(document.getElementById('cardOpacitySlider').value) / 100;
    const color = document.getElementById('cardColorPicker').value;
    const blur = parseInt(document.getElementById('cardBlurSlider').value);

    fetch('/api/settings/appearance', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_opacity: opacity, card_color: color, card_blur: blur })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                showMsg('appearanceMsg', '外观设置保存成功', 'success');
                applyAppearancePreview(d.card_opacity, d.card_color, d.card_blur);
            } else {
                showMsg('appearanceMsg', '保存失败: ' + (d.error || '未知错误'), 'error');
            }
        })
        .catch(err => { showMsg('appearanceMsg', '保存失败: ' + err.message, 'error'); });
}

function resetAppearanceSettings() {
    if (!confirm('确定要恢复默认外观设置吗？')) return;
    document.getElementById('cardOpacitySlider').value = 5;
    document.getElementById('opacityValue').textContent = '5%';
    document.getElementById('cardColorPicker').value = '#ffffff';
    document.getElementById('cardColorHex').textContent = '#ffffff';
    document.getElementById('cardBlurSlider').value = 2;
    document.getElementById('blurValue').textContent = '2px';
    applyAppearancePreview(0.05, '#ffffff', 2);
    showMsg('appearanceMsg', '已恢复默认值，请点击保存', 'success');
}

// ─── Background Management ───

function loadBackgrounds() {
    fetch('/api/settings/background')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('bgThumbnails');
            if (!container) return;
            container.innerHTML = '';
            if (!data.backgrounds || data.backgrounds.length === 0) {
                container.innerHTML = '<div class="bg-placeholder">未上传任何背景图片</div>';
                return;
            }
            data.backgrounds.forEach(filename => {
                const isActive = filename === data.active;
                const thumb = document.createElement('div');
                thumb.className = 'bg-thumb' + (isActive ? ' active' : '');
                thumb.innerHTML = '<img src="/uploads/backgrounds/' + filename + '" alt="' + filename + '">' +
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
    if (!fileInput.files.length) { showMsg('bgUploadMsg', '请选择要上传的图片', 'error'); return; }
    const file = fileInput.files[0];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['jpg','jpeg','png','webp'].includes(ext)) { showMsg('bgUploadMsg', '仅支持 jpg、jpeg、png、webp 格式', 'error'); return; }
    const formData = new FormData();
    formData.append('file', file);
    const btn = document.getElementById('uploadBgBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 上传中...'; btn.disabled = true;
    fetch('/api/settings/background/upload', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { showMsg('bgUploadMsg', '上传成功', 'success'); fileInput.value = ''; loadBackgrounds(); }
            else showMsg('bgUploadMsg', d.error || '上传失败', 'error');
        })
        .catch(err => { showMsg('bgUploadMsg', '上传失败: ' + err.message, 'error'); })
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
                showMsg('bgUploadMsg', '背景已切换', 'success');
                loadBackgrounds();
                if (filename) {
                    document.body.classList.add('has-background');
                    document.body.style.backgroundImage = 'url(/uploads/backgrounds/' + filename + ')';
                } else {
                    document.body.classList.remove('has-background');
                    document.body.style.backgroundImage = '';
                }
            } else showMsg('bgUploadMsg', d.error || '设置失败', 'error');
        })
        .catch(err => { showMsg('bgUploadMsg', '设置失败: ' + err.message, 'error'); });
}

// ─── Utilities ───

function showMsg(elId, msg, type) {
    const el = document.getElementById(elId);
    if (!el) return;
    el.textContent = msg; el.style.display = 'block';
    el.style.color = type === 'error' ? '#f72585' : '#4cc9f0';
    setTimeout(() => { el.style.display = 'none'; }, 3000);
}

// ─── System Backup ───

function triggerBackup() {
    const btn = document.getElementById('backupBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在打包...'; btn.disabled = true;
    showMsg('backupMsg', '', 'success');

    fetch('/api/settings/backup')
        .then(r => {
            if (!r.ok) return r.json().then(d => { throw new Error(d.error || '备份失败'); });
            return r.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const disposition = blob.type === 'application/zip' ? 'backup' : 'data';
            a.download = '3d_inventory_backup.zip';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showMsg('backupMsg', '备份完成，文件已开始下载', 'success');
        })
        .catch(err => {
            showMsg('backupMsg', '备份失败: ' + err.message, 'error');
        })
        .finally(() => {
            btn.innerHTML = '<i class="fas fa-download"></i> 一键备份系统数据';
            btn.disabled = false;
        });
}

// ─── Excel Export ───

function triggerExcelExport() {
    const btn = document.getElementById('exportExcelBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在生成...'; btn.disabled = true;
    showMsg('exportExcelMsg', '', 'success');

    fetch('/api/export/excel')
        .then(r => {
            if (!r.ok) return r.json().then(d => { throw new Error(d.error || '导出失败'); });
            return r.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '3d_inventory_export.xlsx';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showMsg('exportExcelMsg', '导出完成，文件已开始下载', 'success');
        })
        .catch(err => {
            showMsg('exportExcelMsg', '导出失败: ' + err.message, 'error');
        })
        .finally(() => {
            btn.innerHTML = '<i class="fas fa-download"></i> 导出 Excel 表格';
            btn.disabled = false;
        });
}

// ─── System Status ───

function loadSystemStatus() {
    fetch('/api/system/status')
        .then(r => r.json())
        .then(d => {
            document.getElementById('statusProgramVersion').textContent = d.program_version;
            document.getElementById('statusSchemaVersion').textContent = d.schema_version;
            document.getElementById('statusDataHealth').textContent = d.data_status;
            document.getElementById('statusDataHealth').style.color =
                d.data_status.includes('正常') ? 'var(--success)' : 'var(--warning)';
        })
        .catch(() => {
            document.getElementById('statusProgramVersion').textContent = '—';
            document.getElementById('statusSchemaVersion').textContent = '—';
            document.getElementById('statusDataHealth').textContent = '无法获取状态';
        });
}
