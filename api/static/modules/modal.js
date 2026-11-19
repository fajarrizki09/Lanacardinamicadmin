"use strict";
// ─── GLOBAL MODALS ────────────────────────────────────────────────────────────
let runtimeModalDelegationReady = false;
function ensureRuntimeModalEventDelegation() {
    if (runtimeModalDelegationReady)
        return;
    runtimeModalDelegationReady = true;
    document.addEventListener('click', async (event) => {
        const target = event.target;
        if (!target)
            return;
        if (target.id === 'full-edit-modal') {
            closeFullEditModal();
            return;
        }
        if (target.id === 'therapist-modal' || target.id === 'generic-modal') {
            closeModal();
            return;
        }
        const actionElement = target.closest('[data-modal-action]');
        if (!actionElement)
            return;
        const action = actionElement.dataset.modalAction || '';
        if (!action)
            return;
        event.preventDefault();
        switch (action) {
            case 'submit-full-edit':
                submitFullEdit();
                break;
            case 'close-full-edit':
                closeFullEditModal();
                break;
            case 'delete-patient': {
                const id = document.getElementById('fe-id')?.value || '';
                const ok = await showConfirm('Hapus pasien ini beserta SELURUH riwayat kunjungannya secara permanen?');
                if (ok)
                    deletePatient(id);
                break;
            }
            case 'delete-visit': {
                const visitId = Number(actionElement.dataset.visitId || 0);
                const ok = await showConfirm('Hapus kunjungan ini?');
                if (ok)
                    deleteVisit(visitId);
                break;
            }
            case 'close-generic':
                closeModal();
                break;
            case 'submit-edit':
                submitEdit();
                break;
        }
    });
    document.addEventListener('change', (event) => {
        const target = event.target;
        if (target?.dataset?.modalAction === 'refresh-full-edit-therapists') {
            _refreshFullEditTherapistOptions();
        }
        if (target?.classList.contains('fe-v-therapist')) {
            _syncFullEditTherapistHelp(target.closest('.fe-visit-row'), document.getElementById('fe-gender')?.value || '');
        }
    });
}
function initModals() {
    if (document.getElementById('modal-container'))
        return;
    const container = document.createElement('div');
    container.id = 'modal-container';
    container.innerHTML = `
        <!-- ── FULL EDIT MODAL (Pasien & Kunjungan) ──────────────────────────── -->
        <div id="full-edit-modal"
             style="display:none; position:fixed; inset:0; z-index:9999;
                    background:rgba(15,23,42,0.65); backdrop-filter:blur(4px);
                    align-items:center; justify-content:center;">
            <div class="runtime-modal-panel full-edit-panel" style="background:var(--color-surface); border-radius:16px; width:1100px; max-width:96vw; max-height:90vh; display:flex; flex-direction:column;
                        box-shadow:0 24px 64px rgba(0,0,0,0.3); animation:modalIn 0.2s ease; overflow:hidden;">
                
                <!-- HEADER -->
                <div class="runtime-modal-header" style="display:flex; justify-content:space-between; align-items:center; padding:18px 24px; background:var(--color-surface-muted); border-bottom:1px solid var(--color-border);">
                    <h3 style="font-size:18px; font-weight:700; margin:0; color:var(--text-main);">
                        <i class="fas fa-user-edit" style="color:var(--primary); margin-right:8px;"></i> Edit Pasien & Riwayat Kunjungan
                    </h3>
                    <div style="display:flex; gap:12px;">
                        <button type="button" data-modal-action="submit-full-edit" class="btn btn-primary" style="padding:8px 16px; font-size:13px;">
                            <i class="fas fa-save"></i> Simpan Semua Perubahan
                        </button>
                        <button type="button" class="runtime-modal-close" data-modal-action="close-full-edit" style="background:none; border:none; font-size:24px; color:var(--text-muted); cursor:pointer; line-height:1;">&times;</button>
                    </div>
                </div>

                <!-- BODY -->
                <div style="padding:24px; overflow-y:auto; flex:1; display:flex; flex-direction:column; gap:20px;">
                    <div id="fe-result" style="display:none; padding:12px; border-radius:8px; font-size:13px; font-weight:500;"></div>
                    
                    <input type="hidden" id="fe-id">
                    
                    <!-- Bio Section -->
                    <div class="card" style="margin:0; padding:18px;">
                        <h4 style="margin-top:0; margin-bottom:14px; font-size:14px; color:var(--text-main); border-bottom:1px solid var(--border-color); padding-bottom:8px;">
                            <i class="fas fa-id-card" style="color:var(--text-muted); margin-right:6px;"></i> Biodata Pasien
                        </h4>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                            <div class="form-group" style="margin:0;"><label>Nama Lengkap</label><input type="text" id="fe-name" required></div>
                            <div class="form-group" style="margin:0;"><label>Telepon</label><input type="text" id="fe-phone"></div>
                            <div class="form-group" style="margin:0;"><label>Alamat</label><input type="text" id="fe-address"></div>
                            <div class="form-group" style="margin:0;"><label>Jenis Kelamin</label>
                                <select id="fe-gender" data-modal-action="refresh-full-edit-therapists"><option value="Laki-laki">Laki-laki</option><option value="Perempuan">Perempuan</option></select>
                            </div>
                        </div>
                    </div>

                    <!-- Visits Section -->
                    <div class="card" style="margin:0; padding:0; overflow:hidden;">
                        <div class="runtime-modal-header" style="padding:14px 18px; background:var(--color-surface-muted); border-bottom:1px solid var(--color-border); display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0; font-size:14px; color:var(--text-main);">
                                <i class="fas fa-history" style="color:var(--text-muted); margin-right:6px;"></i> Riwayat Kunjungan
                            </h4>
                            <span id="fe-visit-count" style="font-size:12px; color:var(--color-text-muted); font-weight:600; background:var(--color-surface-raised); padding:3px 8px; border-radius:12px;"></span>
                        </div>
                        <div id="fe-visits-container" style="max-height:360px; overflow-y:auto; padding:10px;">
                            <!-- Injected by JS -->
                        </div>
                    </div>
                    
                    <div style="text-align:right;">
                        <button type="button" data-modal-action="delete-patient"
                                style="background:none; border:none; color:var(--danger); font-size:13px; font-weight:600; cursor:pointer; text-decoration:underline;">
                            <i class="fas fa-trash-alt"></i> Hapus Pasien Secara Permanen
                        </button>
                    </div>

                </div>
            </div>
        </div>

        <!-- ── THERAPIST EDIT MODAL ──────────────────────────────────────────────── -->
        <div id="therapist-modal"
             style="display:none; position:fixed; inset:0; z-index:9999;
                    background:rgba(15,23,42,0.55); backdrop-filter:blur(4px);
                    align-items:center; justify-content:center;">
            <div class="runtime-modal-panel" style="background:var(--color-surface); border-radius:16px; padding:28px; width:560px; max-width:94vw; max-height:90vh; overflow:auto;
                        box-shadow:0 24px 64px rgba(0,0,0,0.2); animation: modalIn 0.2s ease;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:22px;">
                    <h3 style="font-size:16px; font-weight:700; color:var(--text-main);">
                        <i class="fas fa-user-edit" style="color:var(--primary); margin-right:8px;"></i> Edit Terapis
                    </h3>
                    <button type="button" class="runtime-modal-close runtime-modal-icon-close" data-modal-action="close-generic"
                        style="background:none; border:none; font-size:22px; color:var(--text-muted); cursor:pointer; line-height:1; padding:4px 8px; border-radius:6px;">
                        &times;
                    </button>
                </div>
                <input type="hidden" id="edit-id">
                <div class="form-group">
                    <label>Nama Lengkap</label>
                    <input type="text" id="edit-name" required placeholder="Nama terapis...">
                </div>
                <div class="form-group">
                    <label>Jenis Kelamin</label>
                    <select id="edit-gender">
                        <option value="Laki-laki">Laki-laki</option>
                        <option value="Perempuan">Perempuan</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Spesialisasi</label>
                    <input type="text" id="edit-spec" placeholder="Contoh: Terapi nyeri, refleksi...">
                </div>
                <div class="form-group">
                    <label>Izin Gender Pasien</label>
                    <label style="display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface-muted);cursor:pointer;text-transform:none;letter-spacing:0;">
                        <input type="checkbox" id="edit-any-gender" value="true" style="width:16px;height:16px;margin-top:2px;accent-color:var(--primary);">
                        <span style="display:flex;flex-direction:column;gap:2px;">
                            <strong style="font-size:13px;color:var(--color-text);">Bisa menangani beda gender</strong>
                            <small style="font-size:11px;line-height:1.35;color:var(--color-text-muted);">Centang jika terapis ini boleh dipilih untuk pasien laki-laki dan perempuan.</small>
                        </span>
                    </label>
                </div>
                <div style="display:flex; gap:10px; margin-top:22px;">
                    <button type="button" class="runtime-modal-close" data-modal-action="close-generic"
                        style="flex:1; padding:11px; border:1.5px solid var(--border-color); border-radius:8px;
                               background:transparent; color:var(--text-muted); font-weight:600; cursor:pointer; font-size:14px;">
                        Batal
                    </button>
                    <button type="button" data-modal-action="submit-edit"
                        style="flex:2; padding:11px; background:linear-gradient(135deg,var(--primary),var(--primary-light));
                               border:none; border-radius:8px; color:white; font-weight:700; cursor:pointer; font-size:14px;
                               box-shadow:0 4px 12px rgba(79,70,229,0.35);">
                        <i class="fas fa-save"></i> Simpan Perubahan
                    </button>
                </div>
                <div id="edit-result" style="margin-top:12px;"></div>
            </div>
        </div>
        <!-- ── GENERIC MODAL ────────────────────────────────────────────────────── -->
        <div id="generic-modal"
             style="display:none; position:fixed; inset:0; z-index:9999;
                    background:rgba(15,23,42,0.55); backdrop-filter:blur(4px);
                    align-items:center; justify-content:center;">
            <div class="runtime-modal-panel" style="background:var(--color-surface); border-radius:16px; padding:28px; width:620px; max-width:94vw; max-height:90vh; overflow:auto;
                        box-shadow:0 24px 64px rgba(0,0,0,0.2); animation: modalIn 0.2s ease;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:22px;">
                    <h3 id="generic-modal-title" style="font-size:16px; font-weight:700; color:var(--text-main);"></h3>
                    <button type="button" class="runtime-modal-icon-close" data-modal-action="close-generic"
                        style="background:none; border:none; font-size:22px; color:var(--text-muted); cursor:pointer; line-height:1; padding:4px 8px; border-radius:6px;">
                        &times;
                    </button>
                </div>
                <div id="generic-modal-body"></div>
            </div>
        </div>
    `;
    document.body.appendChild(container);
    ensureRuntimeModalEventDelegation();
    // Append styles directly
    const style = document.createElement('style');
    style.innerHTML = `
        @keyframes modalIn {
            from { opacity:0; transform:scale(0.98) translateY(10px); }
            to   { opacity:1; transform:scale(1) translateY(0); }
        }
        .edit-btn-hover { opacity:0.3; transition:opacity 0.2s; }
        [id^="pcard-"]:hover .edit-btn-hover { opacity:1; }
        .runtime-modal-icon-close:hover {
            background: var(--color-surface-muted) !important;
        }
        .fe-delete-visit-btn:hover {
            background: var(--danger) !important;
            color: white !important;
        }
        .fe-visit-row, .visit-edit-grid {
            background:var(--color-surface);
            border:1px solid var(--border-color);
            border-radius:10px;
            padding:12px;
            margin-bottom:10px;
            display:grid;
            grid-template-columns: minmax(160px, 0.9fr) minmax(260px, 1.4fr) minmax(90px, 0.55fr) minmax(150px, 0.9fr) minmax(320px, 1.8fr) 44px;
            gap:12px;
            align-items:start;
        }
        .fe-visit-row .form-group,
        .fe-visit-row .fe-visit-field {
            margin:0;
            min-width:0;
        }
        .fe-visit-row input,
        .fe-visit-row select,
        .fe-visit-row textarea {
            width:100%;
            min-width:0;
            height:36px;
            padding:8px 10px;
            font-size:13px;
        }
        .fe-visit-row textarea {
            height:72px;
            min-height:72px;
            max-height:150px;
            line-height:1.4;
            resize:vertical;
            overflow:auto;
        }
        .fe-visit-row label {
            display:block;
            height:14px;
            font-size:10px;
            line-height:14px;
            margin:0 0 5px;
            color:var(--text-muted);
            font-weight:800;
            letter-spacing:.04em;
            text-transform:uppercase;
            white-space:nowrap;
        }
        .fe-visit-price-meta {
            margin-top:5px;
            min-height:32px;
            font-size:10px;
            line-height:1.25;
            color:var(--color-text-muted);
        }
        .visit-therapist-select, .fe-v-therapist {
            width: 100%;
            min-width: 240px;
        }
        .visit-therapist-warning, .fe-v-therapist-help {
            margin-top: 6px;
            font-size: 12px;
            line-height: 1.35;
            max-width: 260px;
            color: var(--color-warning);
        }
        .fe-visit-notes {
            white-space:normal;
        }
        .fe-visit-delete-cell {
            padding-top:19px;
            display:flex;
            justify-content:center;
        }
        @media (max-width: 900px) {
            .fe-visit-row, .visit-edit-grid {
                grid-template-columns: 1fr 1fr;
            }
            .fe-visit-delete-cell {
                grid-column: span 2;
                justify-content: flex-end;
                padding-top: 10px;
                border-top: 1px dashed var(--border-color);
            }
        }
        @media (max-width: 640px) {
            .fe-visit-row, .visit-edit-grid {
                grid-template-columns: 1fr;
            }
            .fe-visit-delete-cell {
                grid-column: auto;
                border-top: 1px dashed var(--border-color);
            }
        }
    `;
    document.head.appendChild(style);
}
// ── FULL EDIT MODAL LOGIC (Patient) ──────────────────────────────────────────
function _fullEditTherapistOptions(gender, selectedId) {
    const therapistsList = window._therapistsList || [];
    const therapists = therapistsList.filter(t => !gender || t.gender === gender || t.can_handle_any_gender);
    const selectedTherapist = selectedId
        ? therapistsList.find(t => String(t.id) === String(selectedId))
        : null;
    const hasMismatch = selectedTherapist && gender && selectedTherapist.gender !== gender && !selectedTherapist.can_handle_any_gender;
    if (therapists.length === 0) {
        return `<option value="">Belum ada terapis aktif yang bisa menangani pasien ${escapeHtml(gender || 'ini')}</option>`;
    }
    let opts = `<option value=""${hasMismatch ? ' selected' : ''}>${hasMismatch ? 'Pilih terapis pengganti' : '- Pilih Terapis -'}</option>`;
    therapists.forEach(t => {
        const selected = String(t.id) === String(selectedId || '') ? ' selected' : '';
        const scope = t.can_handle_any_gender && gender && t.gender !== gender ? ' - lintas gender' : '';
        opts += `<option value="${t.id}"${selected}>${escapeHtml(t.name)}${scope}</option>`;
    });
    return opts;
}
function _fullEditTherapistHelp(gender, selectedId) {
    const therapistsList = window._therapistsList || [];
    const matching = therapistsList.filter(t => !gender || t.gender === gender || t.can_handle_any_gender);
    const selectedTherapist = selectedId
        ? therapistsList.find(t => String(t.id) === String(selectedId))
        : null;
    if (window._therapistsLoadError) {
        return {
            type: 'error',
            text: 'Data terapis belum bisa dimuat. Muat ulang halaman sebelum menyimpan perubahan kunjungan.'
        };
    }
    if (matching.length === 0) {
        return {
            type: 'error',
            text: `Belum ada terapis aktif yang bisa menangani pasien ${gender || 'ini'}. Tambahkan terapis sesuai gender atau aktifkan opsi lintas gender.`
        };
    }
    if (selectedTherapist && gender && selectedTherapist.gender !== gender && !selectedTherapist.can_handle_any_gender) {
        return {
            type: 'warning',
            text: `${selectedTherapist.name} tidak sesuai dengan jenis kelamin pasien. Pilih terapis ${gender} lain atau aktifkan opsi lintas gender.`
        };
    }
    return {
        type: 'info',
        text: `Pilihan mencakup terapis ${gender || 'sesuai pasien'} dan terapis yang diizinkan menangani lintas gender.`
    };
}
function _syncFullEditTherapistHelp(row, gender, previousSelectedId = '') {
    if (!row)
        return;
    const helper = row.querySelector('.fe-v-therapist-help');
    const select = row.querySelector('.fe-v-therapist');
    if (!helper || !select)
        return;
    const selectedId = previousSelectedId || select.value;
    const help = _fullEditTherapistHelp(gender, selectedId);
    helper.textContent = help.text;
    helper.style.color = help.type === 'error' ? 'var(--danger)' : (help.type === 'warning' ? '#b45309' : 'var(--text-muted)');
}
function _refreshFullEditTherapistOptions() {
    const gender = document.getElementById('fe-gender').value;
    document.querySelectorAll('.fe-v-therapist').forEach(sel => {
        const selectedId = sel.value;
        sel.innerHTML = _fullEditTherapistOptions(gender, selectedId);
        if (selectedId && Array.from(sel.options).some(opt => opt.value === selectedId))
            sel.value = selectedId;
        _syncFullEditTherapistHelp(sel.closest('.fe-visit-row'), gender, selectedId);
    });
}
function openFullEditModal(idx) {
    const p = (window._patientsData || [])[idx];
    if (!p)
        return;
    // Bio
    document.getElementById('fe-id').value = String(p.id || '');
    document.getElementById('fe-name').value = p.name || '';
    document.getElementById('fe-phone').value = p.phone && p.phone.startsWith('TEMP-') ? '' : (p.phone || '');
    document.getElementById('fe-address').value = p.address || '';
    document.getElementById('fe-gender').value = p.gender || 'Laki-laki';
    const res = document.getElementById('fe-result');
    res.style.display = 'none';
    res.className = '';
    // Visits
    const container = document.getElementById('fe-visits-container');
    const vcount = document.getElementById('fe-visit-count');
    container.innerHTML = '';
    const visits = p.visits || [];
    vcount.textContent = `${visits.length} Kunjungan`;
    if (visits.length === 0) {
        container.innerHTML = '<div style="padding:30px; text-align:center; color:var(--text-muted); font-size:13px;">Belum ada kunjungan tercatat.</div>';
    }
    else {
        // Loop visits
        visits.forEach((v, vi) => {
            // Calculate local ISO string for datetime-local input
            const dtObj = new Date(v.date);
            const tzOffset = dtObj.getTimezoneOffset() * 60000;
            const localISOTime = new Date(dtObj.getTime() - tzOffset).toISOString().slice(0, 16);
            const finalPrice = Number(v.final_price ?? v.price ?? 0);
            const discountInfo = typeof getVisitDiscountInfo === 'function'
                ? getVisitDiscountInfo(v)
                : {
                    title: v.is_free_visit ? 'Kunjungan gratis' : (v.discount_applied ? 'Diskon terpakai' : 'Harga normal'),
                    detail: v.is_free_visit ? (v.free_visit_reason || '-') : (v.discount_rule_name || 'Tanpa voucher atau rule diskon'),
                    finalPrice,
                    color: v.is_free_visit ? '#059669' : (v.discount_applied ? '#7c3aed' : '#475569'),
                    bg: v.is_free_visit ? '#ecfdf5' : (v.discount_applied ? '#f5f3ff' : '#f8fafc'),
                    border: v.is_free_visit ? '#a7f3d0' : (v.discount_applied ? '#ddd6fe' : '#e2e8f0')
                };
            const row = document.createElement('div');
            row.className = 'fe-visit-row';
            row.dataset.vid = String(v.id || '');
            row.innerHTML = `
                <div class="fe-visit-field">
                    <label>Tanggal & Jam</label>
                    <input type="datetime-local" class="fe-v-date" value="${localISOTime}" style="width:100%; border:1px solid var(--color-border); border-radius:6px; background:var(--color-surface-muted); color:var(--color-text); font-weight:500;">
                </div>
                <div class="form-group visit-therapist-field">
                    <label>Terapis</label>
                    <select class="fe-v-therapist visit-therapist-select">${_fullEditTherapistOptions(p.gender, v.therapist_id)}</select>
                    <div class="fe-v-therapist-help visit-therapist-warning"></div>
                </div>
                <div class="form-group">
                    <label>Jumlah Layanan</label>
                    <input type="number" class="fe-v-points" value="${v.point_count || 0}" min="0">
                </div>
                <div class="form-group">
                    <label>Harga Akhir (Rp)</label>
                    <input type="number" class="fe-v-price" value="${finalPrice}" min="0">
                    <div class="fe-visit-price-meta">
                        <span style="display:inline-block;font-weight:700;color:${discountInfo.color};background:${discountInfo.bg};border:1px solid ${discountInfo.border};border-radius:999px;padding:1px 7px;">${escapeHtml(discountInfo.title)}</span>
                        <div style="margin-top:3px;">${escapeHtml(discountInfo.detail)}</div>
                    </div>
                </div>
                <div class="form-group visit-notes-field">
                    <label>Catatan Medis</label>
                    <textarea class="fe-v-notes fe-visit-notes" rows="3">${escapeHtml(v.medical_notes || '')}</textarea>
                </div>
                <div class="fe-visit-delete-cell">
                    <button type="button" data-modal-action="delete-visit" data-visit-id="${escapeHtml(v.id)}" class="fe-delete-visit-btn"
                            title="Hapus Kunjungan"
                            style="width:34px; height:34px; border-radius:8px; border:1px solid #fecaca; background:#fef2f2; color:var(--danger); cursor:pointer; font-size:13px; display:flex; align-items:center; justify-content:center; transition:all 0.15s;">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            `;
            container.appendChild(row);
            const therapistSelect = row.querySelector('.fe-v-therapist');
            _syncFullEditTherapistHelp(row, p.gender, String(v.therapist_id || ''));
        });
    }
    document.getElementById('full-edit-modal').style.display = 'flex';
}
function closeFullEditModal() {
    document.getElementById('full-edit-modal').style.display = 'none';
}
async function submitFullEdit() {
    const btn = document.querySelector('#full-edit-modal .btn-primary');
    const ogHtml = btn.innerHTML;
    const res = document.getElementById('fe-result');
    const id = document.getElementById('fe-id').value;
    const name = document.getElementById('fe-name').value.trim();
    const phone = document.getElementById('fe-phone').value.trim();
    const address = document.getElementById('fe-address').value.trim();
    const gender = document.getElementById('fe-gender').value;
    if (!name) {
        res.style.display = 'block';
        res.style.background = '#fef2f2';
        res.style.color = 'var(--danger)';
        res.style.border = '1px solid #fecaca';
        res.innerHTML = '<i class="fas fa-exclamation-circle"></i> Nama pasien wajib diisi.';
        return;
    }
    if (phone && (!/^\d+$/.test(phone) || !phone.startsWith('08') || phone.length < 10 || phone.length > 13)) {
        res.style.display = 'block';
        res.style.background = '#fef2f2';
        res.style.color = 'var(--danger)';
        res.style.border = '1px solid #fecaca';
        res.innerHTML = '<i class="fas fa-exclamation-circle"></i> Nomor HP harus diawali 08 dan berisi 10-13 digit.';
        return;
    }
    // Collect all visits
    const visits = [];
    let visitTherapistError = '';
    document.querySelectorAll('.fe-visit-row').forEach(row => {
        const therapistSelect = row.querySelector('.fe-v-therapist');
        const therapistId = therapistSelect.value;
        const help = _fullEditTherapistHelp(gender, therapistId);
        if (!visitTherapistError && (!therapistId || help.type === 'error')) {
            visitTherapistError = help.type === 'error' ? help.text : 'Pilih terapis pengganti untuk setiap kunjungan sebelum menyimpan.';
            _syncFullEditTherapistHelp(row, gender);
        }
        visits.push({
            id: row.dataset.vid,
            date: row.querySelector('.fe-v-date').value,
            therapist_id: therapistId,
            points: row.querySelector('.fe-v-points').value || 0,
            price: row.querySelector('.fe-v-price').value || 0,
            notes: row.querySelector('.fe-v-notes').value || ''
        });
    });
    if (visitTherapistError) {
        res.style.display = 'block';
        res.style.background = '#fef2f2';
        res.style.color = 'var(--danger)';
        res.style.border = '1px solid #fecaca';
        res.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + escapeHtml(visitTherapistError);
        return;
    }
    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
        const form = new FormData();
        form.append('patient_id', id);
        form.append('name', name);
        form.append('phone', phone);
        form.append('address', address);
        form.append('gender', gender);
        form.append('visits', JSON.stringify(visits));
        const r = await fetch('/update_patient_full', { method: 'POST', body: form });
        const d = await r.json();
        res.style.display = 'block';
        if (d.status === 'success') {
            res.style.background = '#ecfdf5';
            res.style.color = 'var(--success)';
            res.style.border = '1px solid #a7f3d0';
            res.innerHTML = '<i class="fas fa-check-circle"></i> ' + d.message;
            setTimeout(() => { closeFullEditModal(); loadTab('patients'); }, 700);
        }
        else {
            const message = typeof formatUserMessage === 'function'
                ? formatUserMessage(d.detail, 'Gagal menyimpan.')
                : (d.detail || 'Gagal menyimpan.');
            res.style.background = '#fef2f2';
            res.style.color = 'var(--danger)';
            res.style.border = '1px solid #fecaca';
            res.innerHTML = '<i class="fas fa-exclamation-triangle"></i> ' + escapeHtml(message);
        }
    }
    catch (e) {
        res.style.display = 'block';
        res.style.background = '#fef2f2';
        res.style.color = 'var(--danger)';
        res.style.border = '1px solid #fecaca';
        res.innerHTML = '<i class="fas fa-times"></i> Error: ' + escapeHtml(e.message);
    }
    finally {
        btn.disabled = false;
        btn.innerHTML = ogHtml;
    }
}
async function deletePatient(id) {
    const form = new FormData();
    form.append('patient_id', id);
    try {
        const r = await fetch('/delete_patient', { method: 'POST', body: form });
        const d = await r.json();
        if (d.status === 'success') {
            closeFullEditModal();
            loadTab('patients');
        }
        else
            alert(d.detail || 'Gagal menghapus pasien.');
    }
    catch (e) {
        alert('Error: ' + e.message);
    }
}
async function deleteVisit(visitId) {
    const form = new FormData();
    form.append('visit_id', visitId);
    try {
        const r = await fetch('/delete_visit', { method: 'POST', body: form });
        const d = await r.json();
        if (d.status === 'success') {
            // Remove row from modal UI
            const row = document.querySelector(`.fe-visit-row[data-vid="${visitId}"]`);
            if (row)
                row.remove();
            // Reload DataTable if active
            if (window._patientsDT) {
                window._patientsDT.ajax.reload(null, false);
            }
        }
        else
            alert(d.detail || 'Gagal menghapus kunjungan.');
    }
    catch (e) {
        alert('Error: ' + e.message);
    }
}
// ── EDIT MODAL LOGIC (Therapist) ─────────────────────────────────────────────
function openEditModal(id) {
    const t = (window._therapistMap || {})[id];
    if (!t) {
        alert('Data tidak ditemukan.');
        return;
    }
    document.getElementById('edit-id').value = String(t.id || '');
    document.getElementById('edit-name').value = t.name || '';
    document.getElementById('edit-spec').value = t.specialization || '';
    document.getElementById('edit-gender').value = t.gender || 'Laki-laki';
    const anyGender = document.getElementById('edit-any-gender');
    if (anyGender) {
        anyGender.checked = t.can_handle_any_gender === true;
    }
    document.getElementById('edit-result').innerHTML = '';
    const modal = document.getElementById('therapist-modal');
    modal.style.display = 'flex';
}
function openModal(title, htmlContent) {
    const modal = document.getElementById('generic-modal');
    const titleEl = document.getElementById('generic-modal-title');
    const bodyEl = document.getElementById('generic-modal-body');
    if (modal && titleEl && bodyEl) {
        titleEl.innerHTML = title;
        bodyEl.innerHTML = htmlContent;
        modal.style.display = 'flex';
    }
}
function closeModal() {
    const tModal = document.getElementById('therapist-modal');
    if (tModal)
        tModal.style.display = 'none';
    const gModal = document.getElementById('generic-modal');
    if (gModal)
        gModal.style.display = 'none';
}
async function submitEdit() {
    const id = document.getElementById('edit-id').value;
    const name = document.getElementById('edit-name').value.trim();
    const gender = document.getElementById('edit-gender').value;
    const spec = document.getElementById('edit-spec').value.trim();
    const canHandleAnyGender = document.getElementById('edit-any-gender')?.checked || false;
    const resultDiv = document.getElementById('edit-result');
    if (!name) {
        resultDiv.innerHTML = '<p style="color:var(--danger);font-size:13px;margin:0;"><i class="fas fa-exclamation-circle"></i> Nama tidak boleh kosong.</p>';
        return;
    }
    const form = new FormData();
    form.append('therapist_id', id);
    form.append('name', name);
    form.append('gender', gender);
    form.append('specialization', spec);
    form.append('is_active', 'true');
    form.append('can_handle_any_gender', canHandleAnyGender ? 'true' : 'false');
    resultDiv.innerHTML = '<span style="color:var(--primary);font-size:13px;"><i class="fas fa-spinner fa-spin"></i> Menyimpan...</span>';
    try {
        const res = await fetch('/update_therapist', { method: 'POST', body: form });
        const data = await res.json();
        if (data.status === 'success') {
            resultDiv.innerHTML = '<span style="color:var(--success);font-size:13px;"><i class="fas fa-check-circle"></i> Tersimpan!</span>';
            setTimeout(() => { closeModal(); loadTab('therapists'); }, 700);
        }
        else {
            resultDiv.innerHTML = `<span style="color:var(--danger);font-size:13px;">${data.detail || 'Gagal menyimpan.'}</span>`;
        }
    }
    catch (e) {
        resultDiv.innerHTML = `<span style="color:var(--danger);font-size:13px;">Error: ${e.message}</span>`;
    }
}
