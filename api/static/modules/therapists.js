"use strict";
window._therapistFilter = window._therapistFilter || 'active';
function renderTherapists(data) {
    window._therapistMap = {};
    data.forEach(therapist => { window._therapistMap[therapist.id] = therapist; });
    const currentFilter = window._therapistFilter || 'active';
    const activeCount = data.filter(therapist => therapist.is_active).length;
    const inactiveCount = data.length - activeCount;
    const visibleTherapists = data.filter(therapist => {
        if (currentFilter === 'inactive')
            return !therapist.is_active;
        if (currentFilter === 'all')
            return true;
        return !!therapist.is_active;
    });
    const filterButton = (filter, label, count) => `
        <button type="button" onclick="setTherapistFilter('${filter}')"
            style="border:1px solid ${currentFilter === filter ? 'var(--primary)' : '#e5e7eb'};
                   background:${currentFilter === filter ? '#eef2ff' : '#fff'};
                   color:${currentFilter === filter ? 'var(--primary)' : 'var(--text-muted)'};
                   border-radius:999px; padding:5px 10px; font-size:12px; font-weight:700; cursor:pointer;">
            ${label} <span style="opacity:.72;">${count}</span>
        </button>
    `;
    let html = `
        <div class="grid-2">
            <!-- LEFT: Form tambah -->
            <div class="card" style="height:fit-content; border-top:3px solid var(--primary);">
                <div class="card-header">
                    <h3><i class="fas fa-user-plus"></i> Registrasi Terapis</h3>
                </div>
                <form action="/add_therapist" method="post">
                    <div class="form-group">
                        <label>Nama Lengkap</label>
                        <input type="text" name="name" required placeholder="Ketik nama terapis...">
                    </div>
                    <div class="form-group">
                        <label>Jenis Kelamin</label>
                        <select name="gender">
                            <option value="Laki-laki">Laki-laki</option>
                            <option value="Perempuan">Perempuan</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Spesialisasi</label>
                        <input type="text" name="specialization" placeholder="Contoh: Terapi nyeri, ruqyah, refleksi...">
                    </div>
                    <div class="form-group">
                        <label>Izin Gender Pasien</label>
                        <label style="display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border:1px solid #c7d2fe;border-radius:8px;background:#eef2ff;cursor:pointer;text-transform:none;letter-spacing:0;">
                            <input type="checkbox" name="can_handle_any_gender" value="true" style="width:16px;height:16px;margin-top:2px;accent-color:var(--primary);">
                            <span style="display:flex;flex-direction:column;gap:2px;">
                                <strong style="font-size:13px;color:#312e81;">Bisa menangani beda gender</strong>
                                <small style="font-size:11px;line-height:1.35;color:#475569;">Centang jika terapis ini boleh dipilih untuk pasien laki-laki dan perempuan.</small>
                            </span>
                        </label>
                    </div>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> Tambah Terapis
                    </button>
                </form>
            </div>

            <!-- RIGHT: Daftar terapis -->
            <div class="card" style="padding:0;">
                <div class="card-header" style="padding:18px 20px 12px;">
                    <h3><i class="fas fa-id-badge"></i> Direktori Terapis
                        <span style="font-size:12px; font-weight:500; color:var(--text-muted); margin-left:6px;">${data.length} terdaftar</span>
                    </h3>
                    <div style="display:flex; gap:8px; font-size:12px;">
                        <span style="background:#ecfdf5; color:#059669; padding:4px 10px; border-radius:999px; font-weight:600; border:1px solid #a7f3d0;">
                            ${activeCount} Aktif
                        </span>
                        <span style="background:#f3f4f6; color:#6b7280; padding:4px 10px; border-radius:999px; font-weight:600; border:1px solid #e5e7eb;">
                            ${inactiveCount} Nonaktif
                        </span>
                    </div>
                </div>
                <div style="padding:0 20px 12px; display:flex; gap:8px; flex-wrap:wrap;">
                    ${filterButton('active', 'Aktif', activeCount)}
                    ${filterButton('inactive', 'Nonaktif', inactiveCount)}
                    ${filterButton('all', 'Semua', data.length)}
                </div>`;
    if (visibleTherapists.length === 0) {
        html += `<div style="padding:50px; text-align:center; color:var(--text-muted);">
            <i class="fas fa-user-slash" style="font-size:40px; opacity:0.15; display:block; margin-bottom:14px;"></i>
            <p>${data.length === 0 ? 'Belum ada data terapis.' : 'Tidak ada terapis pada filter ini.'}</p>
        </div>`;
    }
    else {
        html += `<div style="padding:14px; display:flex; flex-direction:column; gap:8px;">`;
        visibleTherapists.forEach(therapist => {
            const isActive = therapist.is_active;
            const genderColor = therapist.gender === 'Laki-laki' ? '#3b82f6' : '#ec4899';
            const genderBg = therapist.gender === 'Laki-laki' ? '#eff6ff' : '#fdf2f8';
            const genderIcon = therapist.gender === 'Laki-laki' ? 'fa-male' : 'fa-female';
            html += `
            <div style="display:flex; align-items:center; gap:12px; padding:13px 15px;
                        background:${isActive ? '#fafbff' : '#f9fafb'}; border-radius:12px;
                        border:1px solid ${isActive ? '#e0e7ff' : '#e5e7eb'};
                        opacity:${isActive ? 1 : 0.7}; transition:all 0.2s;"
                 onmouseover="this.style.borderColor='#c7d2fe'; this.style.background='#f0f4ff';"
                 onmouseout="this.style.borderColor='${isActive ? '#e0e7ff' : '#e5e7eb'}'; this.style.background='${isActive ? '#fafbff' : '#f9fafb'}';">

                <!-- Avatar -->
                <div style="width:44px; height:44px; border-radius:50%; background:${genderBg};
                            display:flex; align-items:center; justify-content:center;
                            font-size:20px; color:${genderColor}; flex-shrink:0;
                            box-shadow:0 2px 8px ${genderColor}22;">
                    <i class="fas ${genderIcon}"></i>
                </div>

                <!-- Info -->
                <div style="flex:1; min-width:0;">
                    <div style="font-weight:700; font-size:14px; color:${isActive ? 'var(--text-main)' : 'var(--text-muted)'};">
                        ${escapeHtml(therapist.name)}
                    </div>
                    <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                        <i class="fas fa-tag" style="font-size:10px; margin-right:3px;"></i>
                        ${escapeHtml(therapist.specialization) || 'Belum ada spesialisasi'}
                    </div>
                </div>

                <!-- Badge status -->
                <div style="display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end; flex-shrink:0;">
                    <span class="badge ${isActive ? 'badge-ok' : 'badge-low'}">
                        <i class="fas fa-circle" style="font-size:6px;"></i>
                        ${isActive ? 'Aktif' : 'Nonaktif'}
                    </span>
                    ${therapist.can_handle_any_gender ? `<span class="badge" style="background:#eef2ff;color:#4338ca;border:1px solid #c7d2fe;">Lintas gender</span>` : ''}
                </div>

                <!-- Actions - pakai ID agar aman dari karakter khusus -->
                <div style="display:flex; gap:6px; flex-shrink:0;">
                    <button onclick="openEditModal(${therapist.id})"
                        title="Edit Terapis"
                        style="width:32px; height:32px; border-radius:8px; border:1px solid #e0e7ff;
                               background:#f0f4ff; color:var(--primary); cursor:pointer;
                               display:flex; align-items:center; justify-content:center;
                               font-size:13px; transition:all 0.15s;"
                        onmouseover="this.style.background='var(--primary)'; this.style.color='white'; this.style.borderColor='var(--primary)';"
                        onmouseout="this.style.background='#f0f4ff'; this.style.color='var(--primary)'; this.style.borderColor='#e0e7ff';">
                        <i class="fas fa-pen"></i>
                    </button>
                    <button onclick="toggleTherapist(${therapist.id}, this)"
                        title="${isActive ? 'Klik untuk menonaktifkan terapis' : 'Klik untuk mengaktifkan terapis'}"
                        class="activation-action mini ${isActive ? 'is-on' : 'is-off'}">
                        <i class="fas ${isActive ? 'fa-toggle-on' : 'fa-toggle-off'}"></i>
                        <span>
                            <strong>${isActive ? 'Aktif' : 'Nonaktif'}</strong>
                            <small>${isActive ? 'Matikan' : 'Aktifkan'}</small>
                        </span>
                    </button>
                    <button onclick="deleteTherapist(${therapist.id})"
                        title="Hapus Terapis"
                        style="width:32px; height:32px; border-radius:8px; border:1px solid #fecaca;
                               background:#fef2f2; color:var(--danger); cursor:pointer;
                               display:flex; align-items:center; justify-content:center;
                               font-size:13px; transition:all 0.15s;"
                        onmouseover="this.style.background='var(--danger)'; this.style.color='white'; this.style.borderColor='var(--danger)';"
                        onmouseout="this.style.background='#fef2f2'; this.style.color='var(--danger)'; this.style.borderColor='#fecaca';">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>`;
        });
        html += `</div>`;
    }
    html += `</div></div>`;
    const displayArea = document.getElementById('display-area');
    if (displayArea)
        displayArea.innerHTML = html;
}
async function toggleTherapist(id, btn) {
    btn.disabled = true;
    const icon = btn.querySelector('i');
    if (icon)
        icon.className = 'fas fa-spinner fa-spin';
    try {
        const form = new FormData();
        form.append('therapist_id', String(id));
        const data = await apiPostForm('/toggle_therapist', form);
        if (data.status === 'success') {
            loadTab('therapists');
        }
        else {
            btn.disabled = false;
            if (icon)
                icon.className = 'fas fa-user-slash';
            alert(window.LancarApi?.getErrorMessage(data, 'Gagal mengubah status.') || 'Gagal mengubah status.');
        }
    }
    catch (error) {
        btn.disabled = false;
        if (icon)
            icon.className = 'fas fa-user-slash';
        alert('Error: ' + sanitizeAppErrorMessage(error));
    }
}
async function deleteTherapist(id) {
    const therapist = window._therapistMap?.[id];
    const name = typeof therapist === 'string' ? therapist : (therapist?.name || 'terapis ini');
    const ok = await showConfirm(`Hapus permanen terapis "${name}"?\n\nHapus hanya akan berhasil jika terapis belum pernah dipakai di kunjungan. Jika sudah punya riwayat, gunakan tombol Nonaktifkan agar riwayat tetap aman.`, 'error', { confirmText: 'Hapus', cancelText: 'Batal', maxWidth: '440px' });
    if (!ok)
        return;
    try {
        const form = new FormData();
        form.append('therapist_id', String(id));
        const data = await apiPostForm('/delete_therapist', form);
        if (data.status === 'success') {
            showToast(data.message || 'Terapis berhasil dihapus.', 'success');
            loadTab('therapists');
        }
        else {
            showToast(window.LancarApi?.getErrorMessage(data, 'Gagal menghapus terapis.') || 'Gagal menghapus terapis.', 'error');
        }
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal menghapus terapis.'), 'error');
    }
}
function setTherapistFilter(filter) {
    window._therapistFilter = filter;
    renderTherapists(Object.values(window._therapistMap || {}));
}
window.renderTherapists = renderTherapists;
window.toggleTherapist = toggleTherapist;
window.deleteTherapist = deleteTherapist;
window.setTherapistFilter = setTherapistFilter;
