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
        document.getElementById('restoreDefaultBgBtn').addEventListener('click', restoreDefaultBackground);
        document.getElementById('clearBgBtn').addEventListener('click', clearBackground);
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
    if (document.getElementById('restoreBackupBtn')) {
        document.getElementById('restoreBackupBtn').addEventListener('click', triggerRestore);
    }
});

// ─── General Settings ───

function loadGeneralSettings() {
    fetch('/api/settings')
        .then(r => r.json())
        .then(data => {
            document.getElementById('thresholdInput').value = data.threshold;
            document.getElementById('defaultWeightInput').value = data.default_weight;
        });
    fetch('/api/system/config')
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success' && d.data && d.data.system_language) {
                var sel = document.getElementById('systemLanguage');
                if (sel) sel.value = d.data.system_language;
            }
        });
}

function saveGeneralSettings() {
    var threshold = parseFloat(document.getElementById('thresholdInput').value);
    var defaultWeight = parseFloat(document.getElementById('defaultWeightInput').value);
    if (!threshold || threshold <= 0 || !defaultWeight || defaultWeight <= 0) {
        showMsg('settingsMsg', _i('msg_invalid_settings', '请输入有效的设置值'), 'error'); return;
    }
    var lang = document.getElementById('systemLanguage') ? document.getElementById('systemLanguage').value : 'zh';
    var prevLang = localStorage.getItem('lang');
    localStorage.setItem('lang', lang);

    Promise.all([
        fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ threshold: threshold, default_weight: defaultWeight })
        }),
        fetch('/api/system/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ system_language: lang })
        })
    ])
        .then(function (results) { return Promise.all([results[0].json(), results[1].json()]); })
        .then(function (data) {
            showMsg('settingsMsg', _i('msg_settings_saved', '设置保存成功'), 'success');
            if (lang !== prevLang) { setTimeout(function () { location.reload(); }, 500); }
        })
        .catch(function (err) { showMsg('settingsMsg', _i('msg_save_failed', '保存失败') + ': ' + err.message, 'error'); });
}

function resetGeneralSettings() {
    if (!confirm(_i('confirm_reset_settings', '确定要恢复默认设置吗？'))) return;
    document.getElementById('thresholdInput').value = 200;
    document.getElementById('defaultWeightInput').value = 1000;
    showMsg('settingsMsg', _i('reset_to_defaults', '已恢复默认值，请点击保存'), 'success');
}

// ─── Appearance Settings ───

function loadAppearanceSettings() {
    fetch('/api/settings')
        .then(r => r.json())
        .then(data => {
            const opacity = data.card_opacity !== undefined ? data.card_opacity : 0.15;
            const color = data.card_color || '#ffffff';
            const blur = data.card_blur !== undefined ? data.card_blur : 1;
            document.getElementById('cardOpacitySlider').value = Math.round(opacity * 100);
            document.getElementById('opacityValue').textContent = Math.round(opacity * 100) + '%';
            document.getElementById('cardColorPicker').value = color;
            document.getElementById('cardColorHex').textContent = color;
            document.getElementById('cardBlurSlider').value = blur;
            document.getElementById('blurValue').textContent = blur + 'px';
            applyAppearancePreview(opacity, color, blur);
        })
        .catch(err => { showMsg('appearanceMsg', _i('appearance_load_failed', '加载外观设置失败') + ': ' + err.message, 'error'); });
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
                showMsg('appearanceMsg', _i('msg_appearance_saved', '外观设置保存成功'), 'success');
                applyAppearancePreview(d.card_opacity, d.card_color, d.card_blur);
            } else {
                showMsg('appearanceMsg', _i('appearance_save_failed', '保存失败') + ': ' + (d.error || _i('msg_unknown_error', '未知错误')), 'error');
            }
        })
        .catch(err => { showMsg('appearanceMsg', _i('appearance_save_failed', '保存失败') + ': ' + err.message, 'error'); });
}

function resetAppearanceSettings() {
    if (!confirm(_i('confirm_reset_appearance', '确定要恢复默认外观设置吗？'))) return;
    document.getElementById('cardOpacitySlider').value = 15;
    document.getElementById('opacityValue').textContent = '15%';
    document.getElementById('cardColorPicker').value = '#ffffff';
    document.getElementById('cardColorHex').textContent = '#ffffff';
    document.getElementById('cardBlurSlider').value = 1;
    document.getElementById('blurValue').textContent = '1px';
    applyAppearancePreview(0.15, '#ffffff', 1);
    showMsg('appearanceMsg', _i('reset_to_defaults', '已恢复默认值，请点击保存'), 'success');
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
                container.innerHTML = '<div class="bg-placeholder">' + _i('no_bg_uploaded', '未上传任何背景图片') + '</div>';
                return;
            }
            data.backgrounds.forEach(filename => {
                const isActive = filename === data.active;
                const isDefault = filename === 'Background.png';
                const thumb = document.createElement('div');
                thumb.className = 'bg-thumb' + (isActive ? ' active' : '');
                let overlayHtml = '<div class="bg-thumb-overlay">';
                if (!isActive) {
                    overlayHtml += '<button class="btn btn-primary set-bg-btn" data-filename="' + filename + '">' + _i('set_as_bg', '设为背景') + '</button>';
                } else {
                    overlayHtml += '<span style="color:#4cc9f0;font-size:0.8rem;">' + _i('currently_active', '当前使用') + '</span>';
                }
                if (!isDefault) {
                    overlayHtml += '<button class="btn btn-danger del-bg-btn" data-filename="' + filename + '" style="font-size:0.7rem;padding:0.2rem 0.5rem;"><i class="fas fa-trash"></i></button>';
                }
                overlayHtml += '</div>';
                thumb.innerHTML = '<img src="/uploads/backgrounds/' + filename + '" alt="' + filename + '">' + overlayHtml;
                container.appendChild(thumb);
            });
            document.querySelectorAll('.set-bg-btn').forEach(b => {
                b.addEventListener('click', function () { setActiveBackground(this.dataset.filename); });
            });
            document.querySelectorAll('.del-bg-btn').forEach(b => {
                b.addEventListener('click', function () { deleteBackground(this.dataset.filename); });
            });
        })
        .catch(err => { console.error(_i('bg_load_list_failed', '加载背景列表失败') + ':', err); });
}

function uploadBackground() {
    const fileInput = document.getElementById('backgroundFile');
    if (!fileInput.files.length) { showMsg('bgUploadMsg', _i('bg_upload_select_file', '请选择要上传的图片'), 'error'); return; }
    const file = fileInput.files[0];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['jpg','jpeg','png','webp'].includes(ext)) { showMsg('bgUploadMsg', _i('bg_format_restriction', '仅支持 jpg、jpeg、png、webp 格式'), 'error'); return; }
    const formData = new FormData();
    formData.append('file', file);
    const btn = document.getElementById('uploadBgBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + _i('uploading', '上传中...'); btn.disabled = true;
    fetch('/api/settings/background/upload', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') { showMsg('bgUploadMsg', _i('upload_success', '上传成功'), 'success'); fileInput.value = ''; loadBackgrounds(); }
            else showMsg('bgUploadMsg', d.error || _i('bg_upload_failed', '上传失败'), 'error');
        })
        .catch(err => { showMsg('bgUploadMsg', _i('bg_upload_failed', '上传失败') + ': ' + err.message, 'error'); })
        .finally(() => { btn.innerHTML = '<i class="fas fa-upload"></i> ' + _i('btn_upload', '上传'); btn.disabled = false; });
}

function deleteBackground(filename) {
    if (!confirm(_i('bg_delete_confirm', '确定要删除背景图片「{filename}」吗？').replace('{filename}', filename))) return;
    fetch('/api/settings/background/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                showMsg('bgUploadMsg', _i('deleted', '已删除'), 'success');
                loadBackgrounds();
                if (filename === document.body.style.backgroundImage?.match(/[^/]+(?=\))/)?.[0]) {
                    loadCurrentBg();
                }
            } else {
                showMsg('bgUploadMsg', d.error || _i('bg_delete_failed', '删除失败'), 'error');
            }
        });
}

function restoreDefaultBackground() {
    if (!confirm(_i('confirm_restore_default_bg', '确定要恢复为系统默认背景吗？'))) return;
    fetch('/api/settings/background/set', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: 'Background.png' })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                document.body.classList.add('has-background');
                document.body.style.backgroundImage = 'url(/uploads/backgrounds/Background.png)';
                showMsg('bgUploadMsg', _i('restored_default_bg', '已恢复为默认背景'), 'success');
                loadBackgrounds();
            }
        });
}

function clearBackground() {
    if (!confirm(_i('confirm_clear_bg', '确定要移除背景图片吗？'))) return;
    fetch('/api/settings/background/set', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: '' })
    })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                document.body.classList.remove('has-background');
                document.body.style.backgroundImage = '';
                showMsg('bgUploadMsg', _i('bg_removed', '已移除背景'), 'success');
                loadBackgrounds();
            }
        });
}

function loadCurrentBg() {
    fetch('/api/settings/background')
        .then(r => r.json())
        .then(d => {
            if (d.active) {
                document.body.classList.add('has-background');
                document.body.style.backgroundImage = 'url(/uploads/backgrounds/' + d.active + ')';
            } else {
                document.body.classList.remove('has-background');
                document.body.style.backgroundImage = '';
            }
        });
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
                showMsg('bgUploadMsg', _i('bg_switched', '背景已切换'), 'success');
                loadBackgrounds();
                if (filename) {
                    document.body.classList.add('has-background');
                    document.body.style.backgroundImage = 'url(/uploads/backgrounds/' + filename + ')';
                } else {
                    document.body.classList.remove('has-background');
                    document.body.style.backgroundImage = '';
                }
            } else showMsg('bgUploadMsg', d.error || _i('bg_set_failed', '设置失败'), 'error');
        })
        .catch(err => { showMsg('bgUploadMsg', _i('bg_set_failed', '设置失败') + ': ' + err.message, 'error'); });
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
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + _i('backup_packing', '正在打包...'); btn.disabled = true;
    showMsg('backupMsg', '', 'success');

    fetch('/api/settings/backup')
        .then(r => {
            if (!r.ok) return r.json().then(d => { throw new Error(d.error || _i('backup_failed_prefix', '备份失败')); });
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
            showMsg('backupMsg', _i('backup_done', '备份完成') + '，' + _i('backup_downloading', '文件已开始下载'), 'success');
        })
        .catch(err => {
            showMsg('backupMsg', _i('backup_failed_prefix', '备份失败') + ': ' + err.message, 'error');
        })
        .finally(() => {
            btn.innerHTML = '<i class="fas fa-download"></i> ' + _i('btn_backup', '一键备份系统数据');
            btn.disabled = false;
        });
}

// ─── Backup Restore ───

function triggerRestore() {
    const fileInput = document.getElementById('restoreBackupFile');
    if (!fileInput.files.length) { showMsg('restoreBackupMsg', _i('select_zip_backup', '请选择 .zip 备份文件'), 'error'); return; }
    if (!confirm(_i('backup_import_confirm', '导入备份将会完全覆盖当前系统的数据库与所有上传的图片，此操作不可逆！\n\n系统将在导入完成后自动尝试数据库版本兼容与升级。\n\n是否确定继续？'))) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const btn = document.getElementById('restoreBackupBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + _i('importing', '导入中...'); btn.disabled = true;

    fetch('/api/settings/backup/restore', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                showMsg('restoreBackupMsg', _i('system_data_restored', '系统数据热还原成功，页面即将刷新'), 'success');
                setTimeout(() => location.reload(), 2000);
            } else {
                showMsg('restoreBackupMsg', d.error || _i('import_failed', '导入失败'), 'error');
            }
        })
        .catch(err => showMsg('restoreBackupMsg', _i('import_failed', '导入失败') + ': ' + err.message, 'error'))
        .finally(() => { btn.innerHTML = '<i class="fas fa-upload"></i> ' + _i('btn_import_backup', '导入备份'); btn.disabled = false; });
}

// ─── Excel Export ───

function triggerExcelExport() {
    const btn = document.getElementById('exportExcelBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + _i('export_generating', '正在生成...'); btn.disabled = true;
    showMsg('exportExcelMsg', '', 'success');

    fetch('/api/export/excel')
        .then(r => {
            if (!r.ok) return r.json().then(d => { throw new Error(d.error || _i('excel_export_failed_prefix', '导出失败')); });
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
            showMsg('exportExcelMsg', _i('export_done', '导出完成') + '，' + _i('backup_downloading', '文件已开始下载'), 'success');
        })
        .catch(err => {
            showMsg('exportExcelMsg', _i('excel_export_failed_prefix', '导出失败') + ': ' + err.message, 'error');
        })
        .finally(() => {
            btn.innerHTML = '<i class="fas fa-download"></i> ' + _i('btn_export_excel', '导出 Excel 表格');
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
                d.data_status.indexOf('Normal') !== -1 ? 'var(--success)' : 'var(--warning)';
        })
        .catch(() => {
            document.getElementById('statusProgramVersion').textContent = '—';
            document.getElementById('statusSchemaVersion').textContent = '—';
            document.getElementById('statusDataHealth').textContent = _i('status_unavailable', '无法获取状态');
        });
}
