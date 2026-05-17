"use strict";
// DASHBOARD
async function renderDashboard() {
    const response = await fetch('/dashboard_stats');
    if (!response.ok)
        throw new Error('Gagal memuat statistik dashboard');
    const stats = await response.json();
    const totalPatients = Number(stats.total_patients || 0);
    const totalVisits = Number(stats.total_visits || 0);
    const totalTransactions = Number(stats.total_transactions || totalVisits);
    const totalIncome = Number(stats.total_income || 0);
    const herbalSales = Number(stats.total_herbal_sales || 0);
    const lowStockInventory = Number(stats.low_stock_inventory || 0);
    const outOfStockHerbals = Number(stats.out_of_stock_herbals || 0);
    const stockStatus = lowStockInventory + outOfStockHerbals;
    const lowStockItems = Array.isArray(stats.low_stock_items) ? stats.low_stock_items : [];
    const outOfStockItems = Array.isArray(stats.out_of_stock_items) ? stats.out_of_stock_items : [];
    const recentTransactions = Array.isArray(stats.recent_transactions) ? stats.recent_transactions : [];
    const discountSummary = stats.discount_summary || {};
    const lastUpdated = new Date().toLocaleString('id-ID', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    const totalIncomeLabel = formatRupiah(totalIncome);
    const quickActions = [
        { tab: 'patients', icon: 'fa-user-plus', label: 'Tambah Pasien', note: 'Buka data pasien' },
        { tab: 'visits', icon: 'fa-notes-medical', label: 'Catat Kunjungan', note: 'Input terapi baru' },
        { tab: 'inventory', icon: 'fa-box-open', label: 'Cek Stok Alat', note: `${lowStockInventory} perlu dicek` },
        { tab: 'herbals', icon: 'fa-leaf', label: 'Cek Herbal', note: `${outOfStockHerbals} habis` },
    ];
    const renderStockItems = () => {
        const items = [
            ...lowStockItems.map(item => ({
                icon: 'fa-box-open',
                title: item.name,
                meta: `${item.quantity} ${item.unit || ''} tersisa, minimal ${item.min_stock}`,
                tone: 'warning'
            })),
            ...outOfStockItems.map(item => ({
                icon: 'fa-leaf',
                title: item.name,
                meta: `Stok habis (${item.quantity} ${item.unit || ''})`,
                tone: 'danger'
            }))
        ];
        if (!items.length) {
            return `
                <div class="dashboard-empty compact">
                    <i class="fas fa-check-circle"></i>
                    <span>Tidak ada stok kritis saat ini.</span>
                </div>
            `;
        }
        return items.slice(0, 6).map(item => `
            <div class="attention-item ${item.tone}">
                <div class="attention-icon"><i class="fas ${item.icon}"></i></div>
                <div>
                    <strong>${escapeHtml(item.title)}</strong>
                    <span>${escapeHtml(item.meta)}</span>
                </div>
            </div>
        `).join('');
    };
    const renderRecentTransactions = () => {
        if (!recentTransactions.length) {
            return `
                <div class="dashboard-empty">
                    <i class="fas fa-receipt"></i>
                    <span>Belum ada transaksi yang tercatat.</span>
                </div>
            `;
        }
        return recentTransactions.map(item => `
            <div class="recent-row">
                <div class="recent-icon"><i class="fas fa-stethoscope"></i></div>
                <div class="recent-main">
                    <strong>${escapeHtml(item.title)}</strong>
                    <span>${escapeHtml(item.subtitle)} - ${escapeHtml(item.date)}</span>
                </div>
                <div class="recent-amount" title="${escapeHtml(formatRupiah(item.amount))}">${formatRupiah(item.amount)}</div>
            </div>
        `).join('');
    };
    const formatDashboardDiscountValue = (rule) => {
        if (!rule)
            return '-';
        if (rule.discount_type === 'percent')
            return `${Number(rule.discount_value || 0)}%`;
        return formatRupiah(Number(rule.discount_value || 0));
    };
    const formatDashboardDiscountRule = (rule) => {
        if (!rule) {
            return `
                <div class="dashboard-empty compact">
                    <i class="fas fa-tags"></i>
                    <span>Belum ada diskon atau voucher.</span>
                </div>
            `;
        }
        const typeLabels = {
            visit_count: 'Reward kunjungan',
            voucher: 'Voucher',
            manual: 'Harga manual',
            period: 'Periode',
        };
        const condition = rule.type === 'visit_count'
            ? `mulai kunjungan ke-${Number(rule.condition_value || 0)} dan seterusnya`
            : rule.type === 'voucher'
                ? `kode ${rule.voucher_code || '-'}`
                : rule.type === 'period'
                    ? `${rule.start_date || 'mulai sekarang'} s/d ${rule.end_date || 'tanpa batas'}`
                    : 'saat harga diubah manual';
        return `
            <div class="discount-dashboard-row ${rule.is_active ? 'active' : 'inactive'}">
                <div>
                    <strong>${escapeHtml(rule.name)}</strong>
                    <span>${escapeHtml(typeLabels[rule.type] || rule.type)} - ${escapeHtml(condition)}</span>
                </div>
                <div>
                    <b>${escapeHtml(formatDashboardDiscountValue(rule))}</b>
                    <small>${rule.is_active ? 'Aktif' : 'Nonaktif'}</small>
                </div>
            </div>
        `;
    };
    const renderActiveDiscountItems = () => {
        const items = Array.isArray(discountSummary.active_items) ? discountSummary.active_items : [];
        if (!items.length) {
            return `
                <div class="dashboard-empty compact">
                    <i class="fas fa-power-off"></i>
                    <span>Tidak ada diskon aktif. Semua kunjungan memakai harga normal kecuali gratis manual.</span>
                </div>
            `;
        }
        return items.map(formatDashboardDiscountRule).join('');
    };
    const html = `
        <div class="ops-summary">
            <div>
                <span class="section-kicker">Ringkasan operasional</span>
                <h2>Operasional Klinik</h2>
                <p>Angka di bawah adalah total data tersimpan. Diperbarui dari database lokal pada ${lastUpdated}.</p>
            </div>
            <div class="ops-status ${stockStatus > 0 ? 'attention' : ''}">
                <i class="fas ${stockStatus > 0 ? 'fa-exclamation-triangle' : 'fa-check-circle'}"></i>
                <span>${stockStatus > 0 ? `${stockStatus} item perlu dicek` : 'Stok aman'}</span>
            </div>
        </div>

        <div class="dashboard-shell">
            <section class="dashboard-main">
                <div class="stats-grid dashboard-stats">
            <div class="stat-card">
                <div class="stat-icon blue"><i class="fas fa-user-injured"></i></div>
                <div class="stat-details">
                    <h4>Total Pasien</h4>
                    <h2 class="dashboard-kpi-value" title="${totalPatients.toLocaleString('id-ID')}">${totalPatients.toLocaleString('id-ID')}</h2>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon purple"><i class="fas fa-stethoscope"></i></div>
                <div class="stat-details">
                    <h4>Total Transaksi</h4>
                    <h2 class="dashboard-kpi-value" title="${totalTransactions.toLocaleString('id-ID')}">${totalTransactions.toLocaleString('id-ID')}</h2>
                    <p>${totalVisits} kunjungan, ${herbalSales} herbal</p>
                </div>
            </div>
            <div class="stat-card income-stat-card">
                <div class="stat-icon green"><i class="fas fa-money-bill-wave"></i></div>
                <div class="stat-details">
                    <h4>Total Pemasukan</h4>
                    <h2 class="dashboard-kpi-value dashboard-money-value" title="${escapeHtml(totalIncomeLabel)}">${totalIncomeLabel}</h2>
                </div>
            </div>
            <div class="stat-card ${lowStockInventory > 0 ? 'needs-attention' : ''}">
                <div class="stat-icon orange"><i class="fas fa-box-open"></i></div>
                <div class="stat-details">
                    <h4>Alat Kritis</h4>
                    <h2 class="dashboard-kpi-value" title="${lowStockInventory.toLocaleString('id-ID')}" style="color:${lowStockInventory > 0 ? 'var(--warning)' : 'var(--text-main)'};">${lowStockInventory.toLocaleString('id-ID')}</h2>
                </div>
            </div>
            <div class="stat-card ${outOfStockHerbals > 0 ? 'needs-danger' : ''}">
                <div class="stat-icon ${outOfStockHerbals > 0 ? 'red' : 'green'}"><i class="fas fa-leaf"></i></div>
                <div class="stat-details">
                    <h4>Herbal Habis</h4>
                    <h2 class="dashboard-kpi-value" title="${outOfStockHerbals.toLocaleString('id-ID')}" style="color:${outOfStockHerbals > 0 ? 'var(--danger)' : 'var(--text-main)'};">${outOfStockHerbals.toLocaleString('id-ID')}</h2>
                </div>
            </div>
                </div>

                <div class="card dashboard-panel">
                    <div class="card-header compact-card-header clean-header">
                        <h3><i class="fas fa-bolt"></i> Aksi Cepat</h3>
                    </div>
                    <div class="quick-action-grid">
                        ${quickActions.map(action => `
                            <button type="button" class="quick-action" data-dashboard-tab="${action.tab}">
                                <i class="fas ${action.icon}"></i>
                                <span>${escapeHtml(action.label)}</span>
                                <small>${escapeHtml(action.note)}</small>
                            </button>
                        `).join('')}
                    </div>
                </div>

                <div class="card dashboard-panel discount-dashboard-panel">
                    <div class="card-header compact-card-header clean-header">
                        <h3><i class="fas fa-tags"></i> Diskon & Voucher Aktif</h3>
                    </div>
                    <div class="discount-dashboard-summary">
                        <div><strong>${Number(discountSummary.active_count || 0)}</strong><span>Diskon aktif</span></div>
                        <div><strong>${Number(discountSummary.active_voucher_count || 0)}</strong><span>Voucher aktif</span></div>
                        <div><strong>${Number(discountSummary.active_visit_count || 0)}</strong><span>Reward kunjungan</span></div>
                    </div>
                    <div class="discount-dashboard-note">
                        <i class="fas fa-info-circle"></i>
                        Diskon kunjungan dihitung dari total riwayat pasien dan berlaku mulai kunjungan ke-N dan seterusnya.
                    </div>
                    <div class="discount-dashboard-list">
                        ${renderActiveDiscountItems()}
                    </div>
                    <div class="discount-dashboard-history">
                        <div>
                            <span>Diskon terbaru</span>
                            ${formatDashboardDiscountRule(discountSummary.newest)}
                        </div>
                        <div>
                            <span>Diskon sebelumnya</span>
                            ${formatDashboardDiscountRule(discountSummary.previous)}
                        </div>
                    </div>
                </div>

                <div id="calendar-widget-container"></div>
            </section>

            <aside class="dashboard-side">
                <div class="card dashboard-panel attention-panel">
                    <div class="card-header compact-card-header clean-header">
                        <h3><i class="fas fa-clipboard-check"></i> Perlu Tindakan</h3>
                    </div>
                    <div class="attention-list">
                        ${renderStockItems()}
                    </div>
                </div>

                <div class="card dashboard-panel recent-panel">
                    <div class="card-header compact-card-header clean-header">
                        <h3><i class="fas fa-clock"></i> Transaksi Terbaru</h3>
                    </div>
                    <div class="recent-list">
                        ${renderRecentTransactions()}
                    </div>
                </div>
            </aside>
        </div>
    `;
    document.getElementById('display-area').innerHTML = html;
    document.getElementById('calendar-widget-container').innerHTML = renderCalendarWidget();
    document.querySelectorAll('[data-dashboard-tab]').forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-dashboard-tab');
            const navItem = document.querySelector(`.nav-links li[data-tab="${tabName}"]`);
            if (navItem)
                navItem.click();
        });
    });
}
function getSunnahDates(year, month) {
    const dates = [];
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    try {
        const formatter = new Intl.DateTimeFormat('id-ID-u-ca-islamic-umalqura', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
        for (let d = 1; d <= daysInMonth; d++) {
            const date = new Date(year, month, d);
            const parts = formatter.formatToParts(date);
            const hijriDayStr = parts.find(p => p.type === 'day')?.value;
            const hijriMonthName = parts.find(p => p.type === 'month')?.value;
            if (hijriDayStr === '17' || hijriDayStr === '19' || hijriDayStr === '21') {
                dates.push({
                    gDate: date,
                    hDay: hijriDayStr,
                    hMonth: hijriMonthName
                });
            }
        }
    }
    catch (e) {
        console.warn('Islamic calendar not supported in this browser.', e);
    }
    return dates;
}
function renderCalendarWidget() {
    const today = new Date();
    const currYear = today.getFullYear();
    const currMonth = today.getMonth();
    const sunnahDates = getSunnahDates(currYear, currMonth);
    const sunnahDays = sunnahDates.map(d => d.gDate.getDate());
    const firstDay = new Date(currYear, currMonth, 1).getDay();
    const daysInMonth = new Date(currYear, currMonth + 1, 0).getDate();
    const monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
    let calHTML = `
        <div class="card calendar-card">
            <div class="card-header compact-card-header">
                <h3><i class="far fa-calendar-alt"></i> Kalender ${monthNames[currMonth]} ${currYear}</h3>
            </div>
            <div class="calendar-body">
                <div class="calendar-weekdays">
                    <div class="danger-text">Aha</div><div>Sen</div><div>Sel</div><div>Rab</div><div>Kam</div><div>Jum</div><div class="primary-text">Sab</div>
                </div>
                <div class="calendar-grid">
    `;
    for (let i = 0; i < firstDay; i++) {
        calHTML += '<div class="calendar-empty"></div>';
    }
    for (let d = 1; d <= daysInMonth; d++) {
        const isToday = d === today.getDate();
        const isSunnah = sunnahDays.includes(d);
        const classes = [
            'calendar-day',
            isToday ? 'today' : '',
            isSunnah ? 'sunnah' : ''
        ].filter(Boolean).join(' ');
        const badgeHTML = isToday
            ? '<span class="today-badge">Hari ini</span>'
            : isSunnah
                ? '<span class="sunnah-dot"></span>'
                : '';
        calHTML += `<div class="${classes}">${d}${badgeHTML}</div>`;
    }
    calHTML += '</div></div></div>';
    let listHTML = `
        <div class="card sunnah-card">
            <div class="card-header compact-card-header">
                <h3><i class="fas fa-moon"></i> Jadwal Terapi Sunnah</h3>
            </div>
            <div class="sunnah-list">
    `;
    if (sunnahDates.length === 0) {
        listHTML += `
            <div class="empty-state">
                <i class="fas fa-calendar-times"></i>
                <span>Browser tidak mendukung kalender Hijriah otomatis atau tidak ada jadwal.</span>
            </div>
        `;
    }
    else {
        const weekdays = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
        listHTML += '<ul>';
        sunnahDates.forEach((sd) => {
            const gD = sd.gDate.getDate();
            const gM = monthNames[sd.gDate.getMonth()];
            const gY = sd.gDate.getFullYear();
            const dayName = weekdays[sd.gDate.getDay()];
            listHTML += `
                <li>
                    <div class="hijri-date">
                        ${sd.hDay}<span>${sd.hMonth.substring(0, 3)}</span>
                    </div>
                    <div>
                        <strong>${dayName}, ${gD} ${gM} ${gY}</strong>
                        <p>Tanggal ${sd.hDay} ${sd.hMonth} untuk jadwal terapi sunnah.</p>
                    </div>
                </li>
            `;
        });
        listHTML += `</ul>
            <div class="calendar-note">
                <i class="fas fa-exclamation-triangle"></i>
                Tanggal Hijriah pada kalender Masehi dapat bergeser +/- 1 hari mengikuti metode Rukyatul Hilal setempat.
            </div>
        `;
    }
    listHTML += '</div></div>';
    return `
        <div id="sunnah-grid" class="dashboard-grid">
            ${calHTML}
            ${listHTML}
        </div>
    `;
}
window.renderDashboard = renderDashboard;
