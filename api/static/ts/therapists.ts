interface Window {
    renderTherapists?: (data: Therapist[]) => void;
    toggleTherapist?: (id: number | string, btn: HTMLButtonElement) => Promise<void>;
    deleteTherapist?: (id: number | string) => Promise<void>;
    setTherapistFilter?: (filter: TherapistFilter) => void;
    openAddTherapistModal?: () => void;
    openEditTherapistModal?: (id: number | string) => void;
    filterTherapistCapabilityChoices?: (value: string) => void;
    syncTherapistCapabilitySelection?: () => void;
}

type TherapistFilter = 'active' | 'inactive' | 'all';

window._therapistFilter = window._therapistFilter || 'active';

let therapistDelegationReady = false;

function ensureTherapistEventDelegation(): void {
    if (therapistDelegationReady) return;
    therapistDelegationReady = true;

    document.addEventListener('click', (event) => {
        const target = event.target as HTMLElement | null;
        if (target?.id === 'therapist-modal-overlay') {
            closeTherapistModal();
            return;
        }

        const actionElement = target?.closest<HTMLElement>('[data-therapist-action]');
        if (!actionElement) return;
        const action = actionElement.dataset.therapistAction || '';
        if (!action) return;
        if (action === 'capability-sync') return;
        event.preventDefault();

        switch (action) {
            case 'filter':
                setTherapistFilter((actionElement.dataset.filter || 'active') as TherapistFilter);
                break;
            case 'open-add':
                openAddTherapistModal();
                break;
            case 'edit':
                openEditTherapistModal(actionElement.dataset.therapistId || '');
                break;
            case 'toggle':
                toggleTherapist(actionElement.dataset.therapistId || '', actionElement as HTMLButtonElement);
                break;
            case 'delete':
                deleteTherapist(actionElement.dataset.therapistId || '');
                break;
            case 'close-modal':
                closeTherapistModal();
                break;
        }
    });

    document.addEventListener('input', (event) => {
        const target = event.target as HTMLInputElement | null;
        if (target?.dataset?.therapistAction === 'capability-filter') {
            filterTherapistCapabilityChoices(target.value);
        }
    });

    document.addEventListener('change', (event) => {
        const target = event.target as HTMLElement | null;
        if (target?.dataset?.therapistAction === 'capability-sync') {
            syncTherapistCapabilitySelection();
        }
    });
}

function renderTherapists(data: Therapist[]): void {
    ensureTherapistEventDelegation();
    window._therapistMap = {};
    data.forEach(therapist => { window._therapistMap![therapist.id] = therapist; });
    const currentFilter = window._therapistFilter || 'active';
    const activeCount = data.filter(therapist => therapist.is_active).length;
    const inactiveCount = data.length - activeCount;
    const visibleTherapists = data.filter(therapist => {
        if (currentFilter === 'inactive') return !therapist.is_active;
        if (currentFilter === 'all') return true;
        return !!therapist.is_active;
    });
    const filterButton = (filter: TherapistFilter, label: string, count: number) => `
        <button type="button" data-therapist-action="filter" data-filter="${filter}"
            class="therapist-filter-btn ${currentFilter === filter ? 'is-active' : ''}">
            ${label} <span>${count}</span>
        </button>
    `;

    let html = `
        <div class="therapist-page">
            <!-- Header action; counts are shown once in the filter tabs below. -->
            <div class="therapist-page-header">
                <div class="therapist-page-title">
                    <h2><i class="fas fa-user-md"></i> Manajemen Terapis</h2>
                    <p class="therapist-page-subtitle">${data.length} terapis terdaftar</p>
                </div>
                <div class="therapist-page-actions">
                    <button type="button" class="btn btn-primary therapist-add-btn" data-therapist-action="open-add">
                        <i class="fas fa-user-plus"></i> Tambah Terapis
                    </button>
                </div>
            </div>

            <!-- Filter tabs -->
            <div class="therapist-filter-tabs">
                ${filterButton('active', 'Aktif', activeCount)}
                ${filterButton('inactive', 'Nonaktif', inactiveCount)}
                ${filterButton('all', 'Semua', data.length)}
            </div>`;

    if (visibleTherapists.length === 0) {
        html += `<div class="therapist-empty-state">
            <i class="fas fa-user-slash"></i>
            <p>${data.length === 0 ? 'Belum ada data terapis.' : 'Tidak ada terapis pada filter ini.'}</p>
        </div>`;
    } else {
        html += `<div class="therapist-card-grid">`;
        visibleTherapists.forEach(therapist => {
            const isActive = therapist.is_active;
            const genderClass = therapist.gender === 'Laki-laki' ? 'male' : 'female';
            const genderIcon = therapist.gender === 'Laki-laki' ? 'fa-male' : 'fa-female';
            const capabilities = (therapist.service_capabilities || []).filter(item => item.is_active !== false);
            const capabilitySummary = capabilities.length
                ? capabilities.map(item => `<span>${escapeHtml(item.name || '')}</span>`).join('')
                : '<small>Terapis belum memiliki layanan yang ditangani.</small>';

            html += `
            <div class="therapist-card ${isActive ? 'is-active' : 'is-inactive'}">
                <!-- Card header with avatar and status -->
                <div class="therapist-card-header">
                    <div class="therapist-card-avatar ${genderClass}">
                        <i class="fas ${genderIcon}"></i>
                    </div>
                    <span class="therapist-card-status ${isActive ? 'active' : 'inactive'}">
                        <i class="fas fa-circle"></i>
                        ${isActive ? 'Aktif' : 'Nonaktif'}
                    </span>
                </div>

                <!-- Card body -->
                <div class="therapist-card-body">
                    <h4 class="therapist-card-name">${escapeHtml(therapist.name)}</h4>
                    <p class="therapist-card-specialization">
                        <i class="fas fa-tag"></i>
                        ${escapeHtml(therapist.specialization) || 'Belum ada spesialisasi'}
                    </p>
                    ${therapist.can_handle_any_gender ? `
                    <div class="therapist-card-badge">
                        <i class="fas fa-venus-mars"></i>
                        Lintas gender
                    </div>
                    ` : ''}
                    <div class="therapist-service-summary ${capabilities.length ? '' : 'is-empty'}">
                        <strong>Layanan ditangani</strong>
                        <div>${capabilitySummary}</div>
                    </div>
                </div>

                <!-- Card actions -->
                <div class="therapist-card-actions">
                    <button type="button" data-therapist-action="edit" data-therapist-id="${escapeHtml(therapist.id)}"
                        title="Edit Terapis"
                        class="therapist-card-btn edit">
                        <i class="fas fa-pen"></i>
                    </button>
                    <button type="button" data-therapist-action="toggle" data-therapist-id="${escapeHtml(therapist.id)}"
                        title="${isActive ? 'Nonaktifkan' : 'Aktifkan'}"
                        class="therapist-card-btn toggle ${isActive ? 'active' : 'inactive'}">
                        <i class="fas ${isActive ? 'fa-toggle-on' : 'fa-toggle-off'}"></i>
                    </button>
                    <button type="button" data-therapist-action="delete" data-therapist-id="${escapeHtml(therapist.id)}"
                        title="Hapus Terapis"
                        class="therapist-card-btn delete">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>`;
        });
        html += `</div>`;
    }

    html += `</div>`;

    const displayArea = document.getElementById('display-area');
    if (displayArea) displayArea.innerHTML = html;
}

async function ensureTherapistCapabilityServicesLoaded(): Promise<AdminService[]> {
    try {
        const response = await fetch('/services?active_only=true');
        if (!response.ok) throw new Error('Gagal memuat layanan');
        const services = await response.json();
        window._therapistCapabilityServices = Array.isArray(services) ? services : [];
    } catch (error) {
        window._therapistCapabilityServices = [];
    }
    return window._therapistCapabilityServices || [];
}

function therapistCapabilityPicker(selectedIds: Array<number | string> = []): string {
    const selected = new Set(selectedIds.map(id => String(id)));
    const services = window._therapistCapabilityServices || [];
    const options = services.length
        ? services.map(service => `
            <label class="therapist-capability-option" data-search="${escapeHtml(String(service.name || '').toLowerCase())}">
                <input type="checkbox" value="${service.id}" ${selected.has(String(service.id)) ? 'checked' : ''} data-therapist-action="capability-sync">
                <span class="therapist-capability-check"><i class="fas fa-check"></i></span>
                <span>${escapeHtml(service.name || 'Layanan')}</span>
            </label>`).join('')
        : '<div class="therapist-capability-empty">Belum ada layanan aktif tersedia.</div>';
    return `
        <div class="form-group therapist-capability-field">
            <label>Layanan/Terapi yang Dikuasai</label>
            <input type="hidden" name="service_ids" id="therapist-service-ids" value="[]">
            <input type="search" class="therapist-capability-search" placeholder="Cari layanan aktif..." data-therapist-action="capability-filter">
            <div class="therapist-capability-list">${options}</div>
            <small id="therapist-capability-help" class="therapist-capability-help"></small>
        </div>`;
}

async function openAddTherapistModal(): Promise<void> {
    ensureTherapistEventDelegation();
    await ensureTherapistCapabilityServicesLoaded();
    const modalHtml = `
        <div class="modal-overlay" id="therapist-modal-overlay">
            <div class="modal-content therapist-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-user-plus"></i> Tambah Terapis Baru</h3>
                    <button type="button" class="modal-close" data-therapist-action="close-modal">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <form action="/add_therapist" method="post" class="therapist-modal-form">
                    <div class="form-group">
                        <label>Nama Lengkap</label>
                        <input type="text" name="name" required placeholder="Ketik nama terapis..." autofocus>
                    </div>
                    ${therapistCapabilityPicker()}
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
                        <label class="therapist-gender-permission">
                            <input type="checkbox" name="can_handle_any_gender" value="true">
                            <span>
                                <strong>Bisa menangani beda gender</strong>
                                <small>Centang jika terapis ini boleh dipilih untuk pasien laki-laki dan perempuan.</small>
                            </span>
                        </label>
                    </div>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-secondary" data-therapist-action="close-modal">Batal</button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Simpan Terapis
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    syncTherapistCapabilitySelection();
}

async function openEditTherapistModal(id: number | string): Promise<void> {
    ensureTherapistEventDelegation();
    const therapist = window._therapistMap?.[id];
    if (!therapist || typeof therapist === 'string') return;
    await ensureTherapistCapabilityServicesLoaded();
    const selectedIds = (therapist.service_capabilities || [])
        .filter(item => item.is_active !== false)
        .map(item => item.service_id || item.id)
        .filter(Boolean) as Array<number | string>;

    const modalHtml = `
        <div class="modal-overlay" id="therapist-modal-overlay">
            <div class="modal-content therapist-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-pen"></i> Edit Terapis</h3>
                    <button type="button" class="modal-close" data-therapist-action="close-modal">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <form action="/update_therapist" method="post" class="therapist-modal-form">
                    <input type="hidden" name="therapist_id" value="${therapist.id}">
                    <div class="form-group">
                        <label>Nama Lengkap</label>
                        <input type="text" name="name" required value="${escapeHtml(therapist.name)}" autofocus>
                    </div>
                    ${therapistCapabilityPicker(selectedIds)}
                    <div class="form-group">
                        <label>Jenis Kelamin</label>
                        <select name="gender">
                            <option value="Laki-laki" ${therapist.gender === 'Laki-laki' ? 'selected' : ''}>Laki-laki</option>
                            <option value="Perempuan" ${therapist.gender === 'Perempuan' ? 'selected' : ''}>Perempuan</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Spesialisasi</label>
                        <input type="text" name="specialization" value="${escapeHtml(therapist.specialization || '')}" placeholder="Contoh: Terapi nyeri, ruqyah, refleksi...">
                    </div>
                    <div class="form-group">
                        <label class="therapist-gender-permission">
                            <input type="checkbox" name="can_handle_any_gender" value="true" ${therapist.can_handle_any_gender ? 'checked' : ''}>
                            <span>
                                <strong>Bisa menangani beda gender</strong>
                                <small>Centang jika terapis ini boleh dipilih untuk pasien laki-laki dan perempuan.</small>
                            </span>
                        </label>
                    </div>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-secondary" data-therapist-action="close-modal">Batal</button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Simpan Perubahan
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    syncTherapistCapabilitySelection();
}

function filterTherapistCapabilityChoices(value: string): void {
    const query = String(value || '').trim().toLowerCase();
    document.querySelectorAll('.therapist-capability-option').forEach(option => {
        const text = String((option as HTMLElement).dataset.search || '');
        (option as HTMLElement).style.display = !query || text.includes(query) ? '' : 'none';
    });
}

function syncTherapistCapabilitySelection(): void {
    const hidden = document.getElementById('therapist-service-ids');
    const helper = document.getElementById('therapist-capability-help');
    if (!hidden || !helper) return;
    const checked = Array.from(document.querySelectorAll('.therapist-capability-option input:checked'))
        .map(input => Number((input as HTMLInputElement).value))
        .filter(id => id > 0);
    document.querySelectorAll('.therapist-capability-option').forEach(option => {
        const input = option.querySelector<HTMLInputElement>('input[type="checkbox"]');
        option.classList.toggle('is-selected', !!input?.checked);
    });
    (hidden as HTMLInputElement).value = JSON.stringify(checked);
    helper.textContent = checked.length
        ? `${checked.length} layanan dipilih. Dropdown kunjungan akan dibatasi sesuai pilihan ini.`
        : 'Terapis belum memiliki layanan yang ditangani. Semua layanan tetap tersedia saat catat kunjungan.';
    helper.classList.toggle('is-warning', checked.length === 0);
}

function closeTherapistModal(): void {
    const modal = document.getElementById('therapist-modal-overlay');
    if (modal) modal.remove();
}

async function toggleTherapist(id: number | string, btn: HTMLButtonElement): Promise<void> {
    btn.disabled = true;
    const icon = btn.querySelector('i');
    if (icon) icon.className = 'fas fa-spinner fa-spin';

    try {
        const form = new FormData();
        form.append('therapist_id', String(id));
        const data = await apiPostForm<ApiResponse>('/toggle_therapist', form);
        if (data.status === 'success') {
            loadTab('therapists');
        } else {
            btn.disabled = false;
            if (icon) icon.className = 'fas fa-user-slash';
            alert(window.LancarApi?.getErrorMessage(data, 'Gagal mengubah status.') || 'Gagal mengubah status.');
        }
    } catch (error) {
        btn.disabled = false;
        if (icon) icon.className = 'fas fa-user-slash';
        alert('Error: ' + sanitizeAppErrorMessage(error));
    }
}

async function deleteTherapist(id: number | string): Promise<void> {
    const therapist = window._therapistMap?.[id];
    const name = typeof therapist === 'string' ? therapist : (therapist?.name || 'terapis ini');
    const ok = await showConfirm(
        `Hapus permanen terapis "${name}"?\n\nHapus hanya akan berhasil jika terapis belum pernah dipakai di kunjungan. Jika sudah punya riwayat, gunakan tombol Nonaktifkan agar riwayat tetap aman.`,
        'error',
        { confirmText: 'Hapus', cancelText: 'Batal', maxWidth: '440px' }
    );
    if (!ok) return;

    try {
        const form = new FormData();
        form.append('therapist_id', String(id));
        const data = await apiPostForm<ApiResponse>('/delete_therapist', form);
        if (data.status === 'success') {
            showToast(data.message || 'Terapis berhasil dihapus.', 'success');
            loadTab('therapists');
        } else {
            showToast(window.LancarApi?.getErrorMessage(data, 'Gagal menghapus terapis.') || 'Gagal menghapus terapis.', 'error');
        }
    } catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal menghapus terapis.'), 'error');
    }
}

function setTherapistFilter(filter: TherapistFilter): void {
    window._therapistFilter = filter;
    renderTherapists(Object.values(window._therapistMap || {}) as Therapist[]);
}

window.renderTherapists = renderTherapists;
window.toggleTherapist = toggleTherapist;
window.deleteTherapist = deleteTherapist;
window.setTherapistFilter = setTherapistFilter;
window.openAddTherapistModal = openAddTherapistModal;
window.openEditTherapistModal = openEditTherapistModal;
window.closeTherapistModal = closeTherapistModal;
window.filterTherapistCapabilityChoices = filterTherapistCapabilityChoices;
window.syncTherapistCapabilitySelection = syncTherapistCapabilitySelection;
