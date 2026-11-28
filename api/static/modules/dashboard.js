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
    const maxChartValue = Math.max(totalIncome, herbalSales * 100000, totalTransactions * 10000, 1);
    const revenueBars = [
        { label: 'Kunjungan', value: Math.max(0, totalIncome - (herbalSales * 10000)), icon: 'fa-stethoscope' },
        { label: 'Produk', value: herbalSales * 10000, icon: 'fa-leaf' },
        { label: 'Transaksi', value: totalTransactions * 10000, icon: 'fa-receipt' },
        { label: 'Total', value: totalIncome, icon: 'fa-chart-line' },
    ];
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
                tone: 'warning',
                badge: 'Stok rendah'
            })),
            ...outOfStockItems.map(item => ({
                icon: 'fa-leaf',
                title: item.name,
                meta: `Stok habis (${item.quantity} ${item.unit || ''})`,
                tone: 'danger',
                badge: 'Habis'
            }))
        ];
        if (!items.length) {
            return `
                <div class="empty-state">
                    <div class="empty-state-icon">
                        <i class="fas fa-check-circle text-success"></i>
                    </div>
                    <div class="empty-state-content">
                        <h4>Stok Aman</h4>
                        <p>Tidak ada stok kritis saat ini</p>
                    </div>
                </div>
            `;
        }
        return items.slice(0, 6).map((item, index) => `
            <div class="list-item list-item-${item.tone} animate-fadeIn" style="animation-delay: ${0.8 + (index * 0.05)}s;">
                <div class="list-item-icon bg-${item.tone}">
                    <i class="fas ${item.icon}"></i>
                </div>
                <div class="list-item-content">
                    <div class="list-item-title">${escapeHtml(item.title)}</div>
                    <div class="list-item-meta">${escapeHtml(item.meta)}</div>
                </div>
                <span class="badge badge-${item.tone}">${item.badge}</span>
            </div>
        `).join('');
    };
    const renderRecentTransactions = () => {
        if (!recentTransactions.length) {
            return `
                <div class="empty-state">
                    <div class="empty-state-icon">
                        <i class="fas fa-receipt text-muted"></i>
                    </div>
                    <div class="empty-state-content">
                        <h4>Belum Ada Transaksi</h4>
                        <p>Transaksi terbaru akan muncul di sini</p>
                    </div>
                </div>
            `;
        }
        return recentTransactions.map((item, index) => `
            <div class="list-item animate-fadeIn" style="animation-delay: ${1.2 + (index * 0.05)}s;">
                <div class="list-item-icon bg-primary">
                    <i class="fas fa-stethoscope"></i>
                </div>
                <div class="list-item-content">
                    <div class="list-item-title">${escapeHtml(item.title)}</div>
                    <div class="list-item-meta">${escapeHtml(item.subtitle)} • ${escapeHtml(item.date)}</div>
                </div>
                <div class="list-item-value text-success" title="${escapeHtml(formatRupiah(item.amount))}">${formatRupiah(item.amount)}</div>
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
                <p>Angka di bawah adalah total data klinik. Diperbarui pada ${lastUpdated}.</p>
            </div>
            <div class="ops-status ${stockStatus > 0 ? 'attention' : ''}">
                <i class="fas ${stockStatus > 0 ? 'fa-exclamation-triangle' : 'fa-check-circle'}"></i>
                <span>${stockStatus > 0 ? `${stockStatus} item perlu dicek` : 'Stok aman'}</span>
            </div>
        </div>

        <div class="dashboard-shell">
            <section class="dashboard-main">
                <div class="stats-grid dashboard-stats">
            <div class="card-stats card-stats-hover animate-fadeIn">
                <div class="card-stats-icon bg-info">
                    <i class="fas fa-user-injured"></i>
                </div>
                <div class="card-stats-content">
                    <div class="card-stats-label">Total Pasien</div>
                    <div class="card-stats-value" title="${totalPatients.toLocaleString('id-ID')}">${totalPatients.toLocaleString('id-ID')}</div>
                    <div class="card-stats-trend">
                        <i class="fas fa-chart-line"></i>
                        <span>Semua pasien terdaftar</span>
                    </div>
                </div>
            </div>
            <div class="card-stats card-stats-hover animate-fadeIn" style="animation-delay: 0.1s;">
                <div class="card-stats-icon bg-primary">
                    <i class="fas fa-stethoscope"></i>
                </div>
                <div class="card-stats-content">
                    <div class="card-stats-label">Total Transaksi</div>
                    <div class="card-stats-value" title="${totalTransactions.toLocaleString('id-ID')}">${totalTransactions.toLocaleString('id-ID')}</div>
                    <div class="card-stats-trend">
                        <span class="badge badge-info">${totalVisits} kunjungan</span>
                        <span class="badge badge-success">${herbalSales} herbal</span>
                    </div>
                </div>
            </div>
            <div class="card-stats card-stats-hover animate-fadeIn" style="animation-delay: 0.2s;">
                <div class="card-stats-icon bg-success">
                    <i class="fas fa-money-bill-wave"></i>
                </div>
                <div class="card-stats-content">
                    <div class="card-stats-label">Total Pemasukan</div>
                    <div class="card-stats-value" title="${escapeHtml(totalIncomeLabel)}">${totalIncomeLabel}</div>
                    <div class="card-stats-trend">
                        <i class="fas fa-arrow-up text-success"></i>
                        <span>Akumulasi pendapatan</span>
                    </div>
                </div>
            </div>
            <div class="card-stats card-stats-hover animate-fadeIn ${lowStockInventory > 0 ? 'card-stats-warning' : ''}" style="animation-delay: 0.3s;">
                <div class="card-stats-icon ${lowStockInventory > 0 ? 'bg-warning' : 'bg-success'}">
                    <i class="fas fa-box-open"></i>
                </div>
                <div class="card-stats-content">
                    <div class="card-stats-label">Alat Kritis</div>
                    <div class="card-stats-value ${lowStockInventory > 0 ? 'text-warning' : ''}" title="${lowStockInventory.toLocaleString('id-ID')}">${lowStockInventory.toLocaleString('id-ID')}</div>
                    <div class="card-stats-trend">
                        ${lowStockInventory > 0 ? '<span class="badge badge-warning"><i class="fas fa-exclamation-triangle"></i> Perlu restock</span>' : '<span class="badge badge-success"><i class="fas fa-check"></i> Stok aman</span>'}
                    </div>
                </div>
            </div>
            <div class="card-stats card-stats-hover animate-fadeIn ${outOfStockHerbals > 0 ? 'card-stats-danger' : ''}" style="animation-delay: 0.4s;">
                <div class="card-stats-icon ${outOfStockHerbals > 0 ? 'bg-danger' : 'bg-success'}">
                    <i class="fas fa-leaf"></i>
                </div>
                <div class="card-stats-content">
                    <div class="card-stats-label">Herbal Habis</div>
                    <div class="card-stats-value ${outOfStockHerbals > 0 ? 'text-danger' : ''}" title="${outOfStockHerbals.toLocaleString('id-ID')}">${outOfStockHerbals.toLocaleString('id-ID')}</div>
                    <div class="card-stats-trend">
                        ${outOfStockHerbals > 0 ? '<span class="badge badge-danger"><i class="fas fa-times"></i> Segera restock</span>' : '<span class="badge badge-success"><i class="fas fa-check"></i> Stok tersedia</span>'}
                    </div>
                </div>
            </div>
                </div>

                <div class="dashboard-insight-grid">
                    <section class="glass-panel revenue-panel">
                        <div class="panel-heading-row">
                            <div>
                                <span class="section-kicker">Revenue</span>
                                <h3>Komposisi Pendapatan</h3>
                            </div>
                            <span class="status-pill status-paid"><i class="fas fa-circle" aria-hidden="true"></i> Aktif</span>
                        </div>
                        <div class="revenue-chart" role="img" aria-label="Ilustrasi komposisi pendapatan, bukan rincian akurat">
                            ${revenueBars.map((bar, index) => {
        const height = Math.max(18, Math.round((bar.value / maxChartValue) * 100));
        return `
                                    <div class="revenue-bar-wrap" style="--bar-height:${height}%; animation-delay:${0.08 * index}s;" role="img" aria-label="${escapeHtml(bar.label)}: ${escapeHtml(formatRupiah(bar.value))}">
                                        <div class="revenue-bar-value" aria-hidden="true">${formatRupiah(bar.value)}</div>
                                        <div class="revenue-bar" aria-hidden="true"><span></span></div>
                                        <div class="revenue-bar-label" aria-hidden="true"><i class="fas ${bar.icon}"></i>${escapeHtml(bar.label)}</div>
                                    </div>`;
    }).join('')}
                        </div>
                    </section>
                    <section class="glass-panel top-service-panel">
                        <div class="panel-heading-row">
                            <div>
                                <span class="section-kicker">Prioritas</span>
                                <h3>Ringkasan Aktivitas</h3>
                            </div>
                            <span class="status-pill status-pending"><i class="fas fa-clock" aria-hidden="true"></i> Hari ini</span>
                        </div>
                        <div class="top-service-list">
                            <div><strong>Kunjungan</strong><span>${totalVisits.toLocaleString('id-ID')} kunjungan tercatat</span><b>${Math.max(0, Math.round((totalVisits / Math.max(totalTransactions, 1)) * 100))}%</b></div>
                            <div><strong>Produk / Herbal</strong><span>${herbalSales.toLocaleString('id-ID')} transaksi produk</span><b>${herbalSales}</b></div>
                            <div><strong>Stok perlu dicek</strong><span>Inventory dan herbal kritis</span><b>${stockStatus}</b></div>
                        </div>
                    </section>
                </div>

                <div class="card dashboard-panel animate-slideUp">
                    <div class="card-header compact-card-header clean-header">
                        <h3><i class="fas fa-bolt text-warning"></i> Aksi Cepat</h3>
                        <p class="text-muted">Navigasi cepat ke fitur utama</p>
                    </div>
                    <div class="quick-action-grid">
                        ${quickActions.map((action, index) => `
                            <button type="button" class="btn btn-outline btn-lg quick-action-btn animate-fadeIn" data-dashboard-tab="${action.tab}" style="animation-delay: ${0.5 + (index * 0.05)}s;">
                                <div class="quick-action-icon">
                                    <i class="fas ${action.icon}" aria-hidden="true"></i>
                                </div>
                                <div class="quick-action-content">
                                    <span class="quick-action-label">${escapeHtml(action.label)}</span>
                                    <small class="quick-action-note">${escapeHtml(action.note)}</small>
                                </div>
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
                <div class="card dashboard-panel attention-panel animate-slideUp" style="animation-delay: 0.6s;">
                    <div class="card-header compact-card-header clean-header">
                        <h3><i class="fas fa-exclamation-triangle text-warning"></i> Perlu Tindakan</h3>
                        <span class="badge badge-${stockStatus > 0 ? 'warning' : 'success'}">${stockStatus} item</span>
                    </div>
                    <div class="attention-list">
                        ${renderStockItems()}
                    </div>
                </div>

                <div class="card dashboard-panel recent-panel animate-slideUp" style="animation-delay: 0.7s;">
                    <div class="card-header compact-card-header clean-header">
                        <h3><i class="fas fa-clock text-info"></i> Transaksi Terbaru</h3>
                        <span class="badge badge-info">${recentTransactions.length} transaksi</span>
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
