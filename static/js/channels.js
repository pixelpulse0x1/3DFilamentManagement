// Channel Management JS
let currentChannelId = null;

document.addEventListener('DOMContentLoaded', function () {
    loadChannels();
    document.getElementById('addChannelBtn').addEventListener('click', openAdd);
    document.getElementById('saveChannelBtn').addEventListener('click', saveChannel);
    document.getElementById('cancelChannelBtn').addEventListener('click', closeModal);
    document.querySelectorAll('.close-modal').forEach(b => b.addEventListener('click', closeModal));
});

function loadChannels() {
    fetch('/api/channels')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('channelsTableBody');
            if (!Array.isArray(data) || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><i class="fas fa-store"></i><p>' + _i('no_channels_hint', '暂无渠道，点击上方按钮添加') + '</p></div></td></tr>';
                return;
            }
            tbody.innerHTML = '';
            data.forEach(ch => {
                const tr = document.createElement('tr');
                tr.innerHTML = '<td>' + ch.id + '</td><td>' + ch.name + '</td><td>' + (ch.description || '-') + '</td>' +
                    '<td><button class="btn btn-outline edit-ch-btn" data-id="' + ch.id + '" data-name="' + ch.name + '" data-desc="' + (ch.description||'') + '" style="margin-right:4px;height:30px;font-size:0.8rem;"><i class="fas fa-edit"></i></button>' +
                    '<button class="btn btn-danger del-ch-btn" data-id="' + ch.id + '" data-name="' + ch.name + '" style="height:30px;font-size:0.8rem;"><i class="fas fa-trash"></i></button></td>';
                tbody.appendChild(tr);
            });
            document.querySelectorAll('.edit-ch-btn').forEach(b => b.addEventListener('click', function () { openEdit(this.dataset.id, this.dataset.name, this.dataset.desc); }));
            document.querySelectorAll('.del-ch-btn').forEach(b => b.addEventListener('click', function () { deleteChannel(this.dataset.id, this.dataset.name); }));
        })
        .catch(err => showError(_i('msg_load_failed', '加载失败') + ': ' + err.message));
}

function openAdd() {
    currentChannelId = null;
    document.getElementById('channelModalTitle').textContent = _i('add_channel_title', '添加渠道');
    document.getElementById('channelName').value = '';
    document.getElementById('channelDescription').value = '';
    document.getElementById('channelModal').style.display = 'flex';
}

function openEdit(id, name, desc) {
    currentChannelId = id;
    document.getElementById('channelModalTitle').textContent = _i('edit_channel_title', '编辑渠道');
    document.getElementById('channelName').value = name;
    document.getElementById('channelDescription').value = desc;
    document.getElementById('channelModal').style.display = 'flex';
}

function closeModal() { document.getElementById('channelModal').style.display = 'none'; }

function saveChannel() {
    const name = document.getElementById('channelName').value.trim();
    if (!name) { alert(_i('msg_enter_channel_name', '请输入渠道名称')); return; }
    const url = currentChannelId ? '/api/channels/' + currentChannelId : '/api/channels';
    fetch(url, {
        method: currentChannelId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description: document.getElementById('channelDescription').value.trim() })
    })
        .then(r => r.json())
        .then(d => { if (d.status === 'success') { closeModal(); loadChannels(); } else alert(d.error || _i('msg_save_failed', '保存失败')); })
        .catch(err => alert(_i('msg_save_failed', '保存失败') + ': ' + err.message));
}

function deleteChannel(id, name) {
    if (!confirm(_i('confirm_delete_channel', '确定要删除渠道「{name}」吗？').replace('{name}', name))) return;
    fetch('/api/channels/' + id, { method: 'DELETE' })
        .then(r => r.json())
        .then(d => { if (d.status === 'success') loadChannels(); else alert(d.error || _i('msg_delete_failed', '删除失败')); })
        .catch(err => alert(_i('msg_delete_failed', '删除失败') + ': ' + err.message));
}

function showError(msg) {
    const el = document.getElementById('channelError');
    el.textContent = msg; el.style.display = 'block';
}
