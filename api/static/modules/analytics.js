"use strict";
// ─── ANALYTICS ────────────────────────────────────────────────────────────────
// Rich analytics dashboard with charts and detailed tables.
let analyticsDelegationReady = false;
function ensureAnalyticsEventDelegation() {
    if (analyticsDelegationReady)
        return;
    analyticsDelegationReady = true;
    document.addEventListener('click', (event) => {
        const actionElement = event.target?.closest('[data-analytics-action]');
        if (!actionElement)
            return;
        const action = actionElement.dataset.analyticsAction || '';
        if (!action)
            return;
        event.preventDefault();
        if (action === 'period') {
            window._analyticsPeriod = (actionElement.dataset.period || '6m');
            loadTab('analytics');
        }
    });
    document.addEventListener('input', (event) => {
        const target = event.target;
        if (target?.dataset?.analyticsAction === 'profit-preview') {
            updateProfitLossPreview();
        }
    });
}
function renderAnalytics(data = {}) {
    ensureAnalyticsEventDelegation();
    window._analyticsProfitData = data || {};
    const vf = data.visit_frequency || {};
    const top = data.top_therapists || [];
    const recent = data.recent_transactions || data.recent_visits || [];
    const labels = data.monthly_labels || [];
    const mVisits = data.monthly_visits || [];
    const mIncome = data.monthly_income || [];
    // Max values for bar scaling
    const maxVisit = Math.max(...mVisits, 1);
    const maxIncome = Math.max(...mIncome, 1);
    const maxTherapist = top.length > 0 ? top[0].visits : 1;
    // ── Month bar colors (gradient blue shades) ──
    const barColors = ['#bfdbfe', '#93c5fd', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8'];
    // ── Helper: mini bar chart row ───────────────────────────────────────────
    function monthBars(values, max, colorFn, fmtFn) {
        return labels.map((lbl, i) => {
            const pct = max > 0 ? (values[i] / max * 100).toFixed(1) : 0;
            return `
            <div class="analytics-chart-bar-col">
                <div class="analytics-chart-bar-value">${fmtFn(values[i])}</div>
                <div class="analytics-chart-bar-track">
                    <div class="analytics-chart-bar-fill" style="height:${pct}%; background:${colorFn(i)}; min-height:${values[i] > 0 ? '3px' : '0'};"></div>
                </div>
                <div class="analytics-chart-bar-label">${lbl}</div>
            </div>`;
        }).join('');
    }
    // ── Gender donut (CSS only) ─────────────────────────────────────────────
    const total = (data.male_count || 0) + (data.female_count || 0);
    const malePct = total > 0 ? Math.round((data.male_count / total) * 100) : 0;
    const femalePct = 100 - malePct;
    const mAngle = malePct * 3.6; // degrees
    const activePeriod = (window._analyticsPeriod || '6m');
    const periodMap = {
        '7d': '7 Hari',
        '30d': '30 Hari',
        '6m': '6 Bulan',
        '1y': '1 Tahun',
        'all': 'Semua'
    };
    const periodTitle = periodMap[activePeriod] || '6 Bulan';
    const visitPerPatient = data.total_patients > 0 ? (data.total_visits / data.total_patients).toFixed(1) : '0';
    const bestTherapist = top[0];
    const peakIncome = mIncome.length > 0 ? Math.max(...mIncome) : 0;
    const peakIncomeIndex = mIncome.indexOf(peakIncome);
    const peakIncomeLabel = peakIncomeIndex >= 0 ? labels[peakIncomeIndex] : '-';
    const stockTone = data.low_stock_count > 0 ? 'danger' : 'ok';
    const stockLabel = data.low_stock_count > 0 ? 'Perlu restock' : 'Stok aman';
    let html = `
    <div class="analytics-premium-page" data-ui-revision="phase3d-r3-reopened">
    <!-- ── Executive Summary ─────────────────────────────────────────────── -->
    <section class="analytics-hero glass-panel">
        <div class="analytics-hero-copy">
            <span class="analytics-eyebrow"><i class="fas fa-signal"></i> Live clinic analytics</span>
            <h2>Ringkasan Operasional ${periodTitle}</h2>
            <p>Pantau revenue, kunjungan, performa terapis, stok, dan koreksi transaksi dalam satu layar kerja.</p>
            <div class="analytics-hero-meta">
                <span><i class="fas fa-receipt"></i> ${data.total_transactions || 0} transaksi</span>
                <span><i class="fas fa-user-check"></i> ${data.total_visits || 0} kunjungan</span>
                <span class="${stockTone}"><i class="fas fa-boxes-stacked"></i> ${stockLabel}</span>
            </div>
        </div>
        <div class="analytics-hero-controls">
            <div class="analytics-period-filter analytics-period-filter-premium" role="group" aria-label="Filter periode analytics">
                ${Object.entries(periodMap).map(([k, v]) => `
                    <button type="button" data-analytics-action="period" data-period="${escapeHtml(k)}"
                            class="${activePeriod === k ? 'active' : ''}">
                        ${v}
                    </button>
                `).join('')}
            </div>
            <div class="analytics-hero-highlight">
                <span>Pendapatan bersih</span>
                <strong>${formatRupiah(data.current_month_income || 0)}</strong>
                <small class="${(data.income_growth_pct || 0) >= 0 ? 'up' : 'down'}">
                    <i class="fas fa-arrow-${(data.income_growth_pct || 0) >= 0 ? 'up' : 'down'}"></i>
                    ${Math.abs(data.income_growth_pct || 0)}% bulan ini
                </small>
            </div>
        </div>
    </section>

    <!-- ── KPI Cards ─────────────────────────────────────────────────────── -->
    <div class="analytics-kpi-strip analytics-kpi-strip-premium">
        <div class="stat-card analytics-kpi-card-compact analytics-metric-card">
            <div class="stat-icon blue"><i class="fas fa-users"></i></div>
            <div class="stat-details"><h4>Total Pasien</h4><h2>${data.total_patients}</h2><small>${visitPerPatient}x kunjungan/pasien</small></div>
        </div>
        <div class="stat-card analytics-kpi-card-compact analytics-metric-card">
            <div class="stat-icon purple"><i class="fas fa-stethoscope"></i></div>
            <div class="stat-details">
                <h4>Transaksi Bulan Ini</h4>
                <div class="analytics-kpi-value-row">
                    <h2>${data.current_month_transactions || data.current_month_visits || 0}</h2>
                    <span class="analytics-trend ${(data.visits_growth_pct || 0) >= 0 ? 'up' : 'down'}">
                        <i class="fas fa-arrow-${(data.visits_growth_pct || 0) >= 0 ? 'up' : 'down'}"></i> ${Math.abs(data.visits_growth_pct || 0)}%
                    </span>
                </div>
            </div>
        </div>
        <div class="stat-card analytics-kpi-card-compact analytics-metric-card is-featured">
            <div class="stat-icon green"><i class="fas fa-money-bill-wave"></i></div>
            <div class="stat-details">
                <h4>Pendapatan Bersih Bulan Ini</h4>
                <div class="analytics-kpi-value-row wrap">
                    <h2 class="analytics-kpi-money">${formatRupiah(data.current_month_income || 0)}</h2>
                    <span class="analytics-trend ${(data.income_growth_pct || 0) >= 0 ? 'up' : 'down'}">
                        <i class="fas fa-arrow-${(data.income_growth_pct || 0) >= 0 ? 'up' : 'down'}"></i> ${Math.abs(data.income_growth_pct || 0)}%
                    </span>
                </div>
            </div>
        </div>
        <div class="stat-card analytics-kpi-card-compact analytics-metric-card">
            <div class="stat-icon orange"><i class="fas fa-leaf"></i></div>
            <div class="stat-details">
                <h4>Total Aset Herbal</h4>
                <h2 class="analytics-kpi-money" title="${formatRupiah(data.total_herbal_value || 0)}">${formatRupiah(data.total_herbal_value || 0)}</h2>
                <small>Nilai stok berjalan</small>
            </div>
        </div>
        <div class="stat-card analytics-kpi-card-compact analytics-metric-card analytics-stock-card ${stockTone}">
            <div class="stat-icon ${data.low_stock_count > 0 ? 'red' : 'green'}">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="stat-details">
                <h4>Stok Kritis</h4>
                <h2>${data.low_stock_count}</h2>
                <small>${stockLabel}</small>
            </div>
        </div>
    </div>

    <div class="analytics-insight-grid">
        <div class="analytics-insight-card">
            <span><i class="fas fa-crown"></i> Terapis teratas</span>
            <strong>${bestTherapist ? escapeHtml(bestTherapist.name) : 'Belum ada data'}</strong>
            <small>${bestTherapist ? `${bestTherapist.visits || 0} kunjungan, ${bestTherapist.points || 0} titik` : 'Data muncul setelah ada kunjungan.'}</small>
        </div>
        <div class="analytics-insight-card">
            <span><i class="fas fa-chart-line"></i> Bulan revenue tertinggi</span>
            <strong>${peakIncome > 0 ? peakIncomeLabel : '-'}</strong>
            <small>${peakIncome > 0 ? formatRupiah(peakIncome) : 'Belum ada pendapatan pada periode ini.'}</small>
        </div>
        <div class="analytics-insight-card ${Number(data.void_invoice_total || 0) > 0 ? 'danger' : ''}">
            <span><i class="fas fa-shield-alt"></i> Kontrol koreksi</span>
            <strong>${data.void_invoice_count || 0} invoice void</strong>
            <small>Retur ${(data.correction_summary && data.correction_summary.herbal_returns) || 0}, koreksi stok ${(data.correction_summary && data.correction_summary.stock_corrections) || 0}.</small>
        </div>
    </div>

    <!-- ── Row 2: Charts ──────────────────────────────────────────────────── -->
    <div class="analytics-monitor-grid">
        <div class="analytics-monitor-item">
            <span>Rata-rata transaksi</span>
            <strong>${formatRupiah(data.avg_income || 0)}</strong>
            <small>Gabungan kunjungan dan produk/herbal pada periode aktif.</small>
        </div>
        <div class="analytics-monitor-item">
            <span>Transaksi periode</span>
            <strong>${data.total_transactions || 0}</strong>
            <small>${data.total_visits || 0} kunjungan, ${data.total_herbal_sales || 0} penjualan produk/herbal.</small>
        </div>
        <div class="analytics-monitor-item">
            <span>Rasio kunjungan pasien</span>
            <strong>${visitPerPatient}x</strong>
            <small>Rata-rata kunjungan per pasien pada periode ini.</small>
        </div>
        <div class="analytics-monitor-item ${data.low_stock_count > 0 ? 'danger' : ''}">
            <span>Pemantauan stok</span>
            <strong>${data.low_stock_count || 0}</strong>
            <small>Item inventori atau produk/herbal yang perlu dicek admin.</small>
        </div>
    </div>

    <div class="analytics-monitor-grid analytics-monitor-grid-spaced">
        <div class="analytics-monitor-item">
            <span>Gross Visit Revenue</span>
            <strong>${formatRupiah(data.gross_visit_revenue || 0)}</strong>
            <small>Nilai kunjungan sebelum invoice void dipisahkan.</small>
        </div>
        <div class="analytics-monitor-item ${Number(data.void_visit_revenue || 0) > 0 ? 'danger' : ''}">
            <span>Void Visit Revenue</span>
            <strong>${formatRupiah(data.void_visit_revenue || 0)}</strong>
            <small>Kunjungan dengan invoice berstatus VOID.</small>
        </div>
        <div class="analytics-monitor-item">
            <span>Net Visit Revenue</span>
            <strong>${formatRupiah(data.net_visit_revenue || 0)}</strong>
            <small>Gross kunjungan dikurangi invoice void.</small>
        </div>
        <div class="analytics-monitor-item">
            <span>Net Herbal Sales</span>
            <strong>${formatRupiah(data.net_herbal_sales || 0)}</strong>
            <small>Gross ${formatRupiah(data.gross_herbal_sales || 0)} - retur ${formatRupiah(data.herbal_returns || 0)}.</small>
        </div>
        <div class="analytics-monitor-item">
            <span>HPP Herbal</span>
            <strong>${formatRupiah(data.herbal_cogs || 0)}</strong>
            <small>Modal produk/herbal terjual pada periode aktif.</small>
        </div>
        <div class="analytics-monitor-item">
            <span>Laba Kotor</span>
            <strong>${formatRupiah(data.gross_profit || 0)}</strong>
            <small>Pendapatan bersih dikurangi HPP herbal.</small>
        </div>
        <div class="analytics-monitor-item ${Number(data.void_invoice_total || 0) > 0 ? 'danger' : ''}">
            <span>Invoice Aktif / Void</span>
            <strong>${formatRupiah(data.active_invoice_total || 0)}</strong>
            <small>Void: ${formatRupiah(data.void_invoice_total || 0)} (${data.void_invoice_count || 0} invoice).</small>
        </div>
        <div class="analytics-monitor-item">
            <span>Riwayat Koreksi</span>
            <strong>${(data.correction_summary && data.correction_summary.stock_corrections) || 0}</strong>
            <small>Retur ${(data.correction_summary && data.correction_summary.herbal_returns) || 0}, void ${(data.correction_summary && data.correction_summary.void_invoices) || 0}.</small>
        </div>
    </div>

    <div class="card analytics-profit-card">
        <div class="card-header analytics-card-header-spaced">
            <h3><i class="fas fa-balance-scale text-primary"></i> Neraca Laba Rugi</h3>
        </div>
        <div class="profit-loss-grid">
            <div class="analytics-monitor-item">
                <span>Pendapatan Layanan</span>
                <strong>${formatRupiah(data.net_visit_revenue || 0)}</strong>
                <small>Kunjungan aktif setelah void.</small>
            </div>
            <div class="analytics-monitor-item">
                <span>Penjualan Herbal</span>
                <strong>${formatRupiah(data.net_herbal_sales || 0)}</strong>
                <small>Penjualan setelah retur.</small>
            </div>
            <div class="analytics-monitor-item">
                <span>HPP Herbal</span>
                <strong>${formatRupiah(data.herbal_cogs || 0)}</strong>
                <small>Harga modal barang terjual.</small>
            </div>
            <div class="form-group analytics-profit-input-field">
                <label>Biaya Operasional</label>
                <input type="number" id="profit-operational-expense" value="0" min="0" data-analytics-action="profit-preview">
            </div>
            <div class="analytics-monitor-item">
                <span>Laba Kotor</span>
                <strong>${formatRupiah(data.gross_profit || 0)}</strong>
                <small>Sebelum biaya operasional.</small>
            </div>
            <div class="analytics-monitor-item is-accented">
                <span>Laba Bersih</span>
                <strong id="profit-net-preview">${formatRupiah(data.gross_profit || 0)}</strong>
                <small>Laba kotor dikurangi biaya operasional.</small>
            </div>
        </div>
    </div>

    <div class="analytics-chart-grid-2col">

        <div class="card analytics-chart-card">
            <div class="card-header analytics-chart-header">
                <h3><i class="fas fa-chart-bar" style="color:#3b82f6;"></i> Kunjungan</h3>
            </div>
            <div class="analytics-chart-bars">
                ${monthBars(mVisits, maxVisit, (i) => barColors[i] || '#3b82f6', (v) => v + 'x')}
            </div>
        </div>

        <div class="card analytics-chart-card">
            <div class="card-header analytics-chart-header">
                <h3><i class="fas fa-chart-area" style="color:#10b981;"></i> Pendapatan Bersih Kunjungan & Herbal</h3>
            </div>
            <div class="analytics-chart-bars">
                ${monthBars(mIncome, maxIncome, (i) => `hsl(${150 - i * 5}, 65%, ${55 + i * 3}%)`, (v) => v >= 1000000 ? (v / 1000000).toFixed(1) + 'jt' : (v / 1000).toFixed(0) + 'rb')}
            </div>
        </div>
    </div>

    <!-- ── Row 3: Therapists + Gender + Frequency ────────────────────────── -->
    <div class="analytics-chart-grid-3col">

        <!-- Top Therapists -->
        <div class="card analytics-chart-card">
            <div class="card-header analytics-chart-header">
                <h3><i class="fas fa-trophy" style="color:#f59e0b;"></i> Top Terapis</h3>
            </div>
            ${top.length === 0
        ? `<div class="analytics-empty-state">Belum ada data kunjungan.</div>`
        : top.map((t, i) => {
            const pct = Math.round(t.visits / maxTherapist * 100);
            const medals = ['1.', '2.', '3.', '4.', '5.'];
            return `
                    <div class="analytics-top-list-item">
                        <div class="analytics-top-list-row">
                            <span class="analytics-top-list-name">${medals[i] || ''} ${escapeHtml(t.name)}</span>
                            <span class="analytics-top-list-stats">${t.visits}x - <span class="analytics-top-list-stats-primary">${t.points || 0} ttk</span></span>
                        </div>
                        <div class="analytics-top-list-bar-bg">
                            <div class="analytics-top-list-bar-fill" style="width:${pct}%;"></div>
                        </div>
                    </div>`;
        }).join('')}
        </div>

        <!-- Gender Breakdown -->
        <div class="card analytics-gender-card">
            <div class="card-header analytics-chart-header">
                <h3><i class="fas fa-venus-mars" style="color:#8b5cf6;"></i> Gender</h3>
            </div>
            <div class="analytics-donut-wrap">
                <div style="width:100px; height:100px; border-radius:50%; background: conic-gradient(#3b82f6 0deg ${mAngle}deg, #f472b6 ${mAngle}deg 360deg);"></div>
                <div class="analytics-donut-center">
                    ${total}
                </div>
            </div>
            <div class="analytics-legend-row">
                <span class="analytics-legend-item"><span class="analytics-legend-box" style="background:#3b82f6;"></span>L: ${data.male_count} (${malePct}%)</span>
                <span class="analytics-legend-item"><span class="analytics-legend-box" style="background:#f472b6;"></span>P: ${data.female_count} (${femalePct}%)</span>
            </div>
        </div>

        <!-- Visit Frequency -->
        <div class="card analytics-frequency-card">
            <div class="card-header analytics-chart-header">
                <h3><i class="fas fa-redo" style="color:#10b981;"></i> Frekuensi</h3>
            </div>
            <p class="analytics-frequency-desc">Berapa kali pasien datang berkunjung</p>
            ${[
        { label: '1x kunjungan', key: '1', color: '#fbbf24' },
        { label: '2-4x kunjungan', key: '2-4', color: '#3b82f6' },
        { label: '5x+ (loyal)', key: '5+', color: '#10b981' },
    ].map(f => {
        const count = vf[f.key] || 0;
        const pct = total > 0 ? Math.round(count / total * 100) : 0;
        return `
                <div class="analytics-frequency-item">
                    <div class="analytics-frequency-row">
                        <span>${f.label}</span>
                        <span style="font-weight:700; color:${f.color};">${count} pasien</span>
                    </div>
                    <div class="analytics-frequency-bar-bg">
                        <div class="analytics-frequency-bar-fill" style="width:${pct}%; background:${f.color};"></div>
                    </div>
                </div>`;
    }).join('')}
        </div>
    </div>

    <!-- ── Row 4: Recent Visits Table ────────────────────────────────────── -->
    <div class="card analytics-recent-card">
        <div class="card-header analytics-recent-header">
            <h3><i class="fas fa-history" style="color:#6366f1;"></i> 10 Transaksi Terbaru</h3>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Tanggal</th>
                        <th>Transaksi</th>
                        <th>Keterangan</th>
                        <th class="text-center">Qty/Titik</th>
                        <th class="text-right">Nilai</th>
                    </tr>
                </thead>
                <tbody>
                    ${recent.length === 0
        ? `<tr><td colspan="5" class="analytics-recent-empty">Belum ada transaksi.</td></tr>`
        : recent.map((r, i) => {
            const isHerbal = r.type === 'herbal';
            const isReturn = r.transaction_type === 'return' || r.transaction_type === 'retur';
            const badge = isHerbal
                ? `<span class="status-badge ${isReturn ? 'retur' : 'herbal'}">${isReturn ? 'RETUR' : 'HERBAL'}</span>`
                : '<span class="status-badge visit">KUNJUNGAN</span>';
            const statusBadge = r.invoice_status === 'void'
                ? '<span class="status-badge void">VOID</span>'
                : '';
            return `
                        <tr class="${i % 2 === 1 ? 'analytics-recent-row-alt' : ''}">
                            <td class="analytics-recent-cell-muted">${escapeHtml(r.date)}</td>
                            <td class="analytics-recent-cell-bold">
                                <div class="analytics-recent-badge-wrap">
                                    ${badge}
                                    ${statusBadge}
                                    <span>${escapeHtml(r.patient)}</span>
                                </div>
                            </td>
                            <td class="analytics-recent-cell-muted">${escapeHtml(r.therapist)}</td>
                            <td class="analytics-recent-qty-cell">${r.point_count} <span class="analytics-recent-qty-unit">${isHerbal ? 'pcs' : 'pt'}</span></td>
                            <td class="analytics-recent-price-cell">${formatRupiah(r.price)}</td>
                        </tr>`;
        }).join('')}
                </tbody>
            </table>
        </div>
    </div>
    </div>`;
    document.getElementById('display-area').innerHTML = html;
    updateProfitLossPreview();
}
function updateProfitLossPreview() {
    const data = window._analyticsProfitData || {};
    const expenseInput = document.getElementById('profit-operational-expense');
    const expense = Math.max(0, Number(expenseInput?.value || 0));
    const grossProfit = Number(data.gross_profit || 0);
    const target = document.getElementById('profit-net-preview');
    if (target)
        target.textContent = formatRupiah(grossProfit - expense);
}
window.renderAnalytics = renderAnalytics;
window.updateProfitLossPreview = updateProfitLossPreview;
