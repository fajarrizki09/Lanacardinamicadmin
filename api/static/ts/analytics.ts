// ─── ANALYTICS ────────────────────────────────────────────────────────────────
// Rich analytics dashboard with charts and detailed tables.

type AnalyticsPeriodKey = "7d" | "30d" | "6m" | "1y" | "all";

function renderAnalytics(data: AnalyticsSummary = {}) {
    window._analyticsProfitData = data || {};
    const vf: Partial<Record<"1" | "2-4" | "5+", number>> = data.visit_frequency || {};
    const top = data.top_therapists || [];
    const recent = data.recent_transactions || data.recent_visits || [];
    const labels = data.monthly_labels || [];
    const mVisits = data.monthly_visits || [];
    const mIncome = data.monthly_income || [];

    // Max values for bar scaling
    const maxVisit = Math.max(...mVisits, 1);
    const maxIncome = Math.max(...mIncome, 1);
    const maxTherapist = top.length > 0 ? top[0].visits! : 1;

    // ── Month bar colors (gradient blue shades) ──
    const barColors = ['#bfdbfe', '#93c5fd', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8'];

    // ── Helper: mini bar chart row ───────────────────────────────────────────
    function monthBars(
        values: number[],
        max: number,
        colorFn: (index: number) => string,
        fmtFn: (value: number) => string
    ): string {
        return labels.map((lbl, i) => {
            const pct = max > 0 ? (values[i] / max * 100).toFixed(1) : 0;
            return `
            <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:4px; min-width:0;">
                <div style="font-size:9px; color:var(--text-muted); font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:100%;">${fmtFn(values[i])}</div>
                <div style="width:100%; background:#f0f4ff; border-radius:4px 4px 0 0; height:80px; display:flex; align-items:flex-end; overflow:hidden;">
                    <div style="width:100%; height:${pct}%; background:${colorFn(i)}; border-radius:4px 4px 0 0; transition:height 0.4s ease; min-height:${values[i] > 0 ? '3px' : '0'};"></div>
                </div>
                <div style="font-size:8px; color:var(--text-muted); text-align:center; line-height:1.2; font-weight:500;">${lbl}</div>
            </div>`;
        }).join('');
    }

    // ── Gender donut (CSS only) ─────────────────────────────────────────────
    const total = (data.male_count || 0) + (data.female_count || 0);
    const malePct = total > 0 ? Math.round((data.male_count! / total) * 100) : 0;
    const femalePct = 100 - malePct;
    const mAngle = malePct * 3.6; // degrees

    const activePeriod = (window._analyticsPeriod || '6m') as AnalyticsPeriodKey;
    const periodMap: Record<AnalyticsPeriodKey, string> = {
        '7d': '7 Hari',
        '30d': '30 Hari',
        '6m': '6 Bulan',
        '1y': '1 Tahun',
        'all': 'Semua'
    };
    const periodTitle = periodMap[activePeriod] || '6 Bulan';
    const visitPerPatient = data.total_patients! > 0 ? (data.total_visits! / data.total_patients!).toFixed(1) : '0';

    let html = `
    <!-- ── Filter Period ─────────────────────────────────────────────────── -->
    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:15px;">
        <h2 style="font-size:18px; margin:0;"><i class="fas fa-chart-pie" style="color:var(--primary); margin-right:8px;"></i> Ringkasan ${periodTitle} Terakhir</h2>
        <div style="display:flex; background:white; border:1px solid var(--border-color); border-radius:20px; overflow:hidden; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
            ${Object.entries(periodMap).map(([k, v]) => `
                <button onclick="window._analyticsPeriod='${k}'; loadTab('analytics')" 
                        style="border:none; background:${activePeriod === k ? 'var(--primary)' : 'transparent'}; 
                               color:${activePeriod === k ? 'white' : 'var(--text-muted)'}; 
                               padding:6px 16px; font-size:12px; font-weight:600; cursor:pointer; transition:all 0.2s;">
                    ${v}
                </button>
            `).join('')}
        </div>
    </div>

    <!-- ── KPI Cards ─────────────────────────────────────────────────────── -->
    <div class="stats-grid" style="grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); margin-bottom:20px;">
        <div class="stat-card" style="padding:16px;">
            <div class="stat-icon blue"><i class="fas fa-users"></i></div>
            <div class="stat-details"><h4>TOTAL PASIEN</h4><h2 style="font-size:20px;">${data.total_patients}</h2></div>
        </div>
        <div class="stat-card" style="padding:16px;">
            <div class="stat-icon purple"><i class="fas fa-stethoscope"></i></div>
            <div class="stat-details">
                <h4>TRANSAKSI B.INI</h4>
                <div style="display:flex; align-items:flex-end; gap:8px;">
                    <h2 style="font-size:20px;">${data.current_month_transactions || data.current_month_visits || 0}</h2>
                    <span style="font-size:11px; font-weight:600; padding-bottom:3px; color:${(data.visits_growth_pct || 0) >= 0 ? 'var(--success)' : 'var(--danger)'};">
                        <i class="fas fa-arrow-${(data.visits_growth_pct || 0) >= 0 ? 'up' : 'down'}"></i> ${Math.abs(data.visits_growth_pct || 0)}%
                    </span>
                </div>
            </div>
        </div>
        <div class="stat-card" style="padding:16px;">
            <div class="stat-icon green"><i class="fas fa-money-bill-wave"></i></div>
            <div class="stat-details" style="min-width:0;">
                <h4>PENDAPATAN BERSIH B.INI</h4>
                <div style="display:flex; align-items:flex-end; gap:8px; flex-wrap:wrap;">
                    <h2 style="font-size:16px; word-break: break-word; line-height: 1.2;">${formatRupiah(data.current_month_income || 0)}</h2>
                    <span style="font-size:11px; font-weight:600; padding-bottom:2px; color:${(data.income_growth_pct || 0) >= 0 ? 'var(--success)' : 'var(--danger)'};">
                        <i class="fas fa-arrow-${(data.income_growth_pct || 0) >= 0 ? 'up' : 'down'}"></i> ${Math.abs(data.income_growth_pct || 0)}%
                    </span>
                </div>
            </div>
        </div>
        <div class="stat-card" style="padding:16px;">
            <div class="stat-icon orange"><i class="fas fa-leaf"></i></div>
            <div class="stat-details" style="min-width:0;">
                <h4>TOTAL ASET HERBAL</h4>
                <h2 style="font-size:16px; word-break: break-word; line-height: 1.2;" title="${formatRupiah(data.total_herbal_value || 0)}">${formatRupiah(data.total_herbal_value || 0)}</h2>
            </div>
        </div>
        <div class="stat-card" style="padding:16px; border-left: 4px solid ${data.low_stock_count! > 0 ? 'var(--danger)' : 'var(--success)'};">
            <div class="stat-icon ${data.low_stock_count! > 0 ? 'red' : 'green'}" style="${data.low_stock_count! > 0 ? 'background:#fee2e2;' : ''}">
                <i class="fas fa-exclamation-triangle" style="${data.low_stock_count! > 0 ? 'color:var(--danger);' : ''}"></i>
            </div>
            <div class="stat-details">
                <h4>STOK KRITIS</h4>
                <h2 style="font-size:20px; color:${data.low_stock_count! > 0 ? 'var(--danger)' : 'var(--success)'};">${data.low_stock_count}</h2>
            </div>
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
        <div class="analytics-monitor-item ${data.low_stock_count! > 0 ? 'danger' : ''}">
            <span>Pemantauan stok</span>
            <strong>${data.low_stock_count || 0}</strong>
            <small>Item inventori atau produk/herbal yang perlu dicek admin.</small>
        </div>
    </div>

    <div class="analytics-monitor-grid" style="margin-bottom:16px;">
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

    <div class="card" style="padding:20px; margin-bottom:16px;">
        <div class="card-header" style="margin-bottom:14px;">
            <h3><i class="fas fa-balance-scale" style="color:#0f766e;"></i> Neraca Laba Rugi</h3>
        </div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; align-items:end;">
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
            <div class="form-group" style="margin:0;">
                <label>Biaya Operasional</label>
                <input type="number" id="profit-operational-expense" value="0" min="0" oninput="updateProfitLossPreview()" style="height:42px;">
            </div>
            <div class="analytics-monitor-item">
                <span>Laba Kotor</span>
                <strong>${formatRupiah(data.gross_profit || 0)}</strong>
                <small>Sebelum biaya operasional.</small>
            </div>
            <div class="analytics-monitor-item" style="border-left:4px solid #0f766e;">
                <span>Laba Bersih</span>
                <strong id="profit-net-preview">${formatRupiah(data.gross_profit || 0)}</strong>
                <small>Laba kotor dikurangi biaya operasional.</small>
            </div>
        </div>
    </div>

    <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">

        <div class="card" style="padding:20px;">
            <div class="card-header" style="margin-bottom:16px;">
                <h3><i class="fas fa-chart-bar" style="color:#3b82f6;"></i> Kunjungan</h3>
            </div>
            <div style="display:flex; gap:6px; align-items:flex-end; height:120px; overflow-x:auto; padding-bottom:5px;">
                ${monthBars(mVisits, maxVisit, (i) => barColors[i] || '#3b82f6', (v) => v + 'x')}
            </div>
        </div>

        <div class="card" style="padding:20px;">
            <div class="card-header" style="margin-bottom:16px;">
                <h3><i class="fas fa-chart-area" style="color:#10b981;"></i> Pendapatan Bersih Kunjungan & Herbal</h3>
            </div>
            <div style="display:flex; gap:6px; align-items:flex-end; height:120px; overflow-x:auto; padding-bottom:5px;">
                ${monthBars(mIncome, maxIncome,
        (i) => `hsl(${150 - i * 5}, 65%, ${55 + i * 3}%)`,
        (v) => v >= 1000000 ? (v / 1000000).toFixed(1) + 'jt' : (v / 1000).toFixed(0) + 'rb'
    )}
            </div>
        </div>
    </div>

    <!-- ── Row 3: Therapists + Gender + Frequency ────────────────────────── -->
    <div style="display:grid; grid-template-columns:2fr 1fr 1fr; gap:16px; margin-bottom:16px;">

        <!-- Top Therapists -->
        <div class="card" style="padding:20px;">
            <div class="card-header" style="margin-bottom:14px;">
                <h3><i class="fas fa-trophy" style="color:#f59e0b;"></i> Top Terapis</h3>
            </div>
            ${top.length === 0
            ? `<div style="text-align:center; color:var(--text-muted); padding:20px; font-style:italic;">Belum ada data kunjungan.</div>`
            : top.map((t, i) => {
                const pct = Math.round(t.visits! / maxTherapist * 100);
                const medals = ['1.', '2.', '3.', '4.', '5.'];
                return `
                    <div style="margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:600; font-size:13px;">${medals[i] || ''} ${escapeHtml(t.name)}</span>
                            <span style="font-size:12px; color:var(--text-muted);">${t.visits}x - <span style="font-weight:600;color:var(--primary);">${t.points || 0} ttk</span></span>
                        </div>
                        <div style="background:#f0f4ff; border-radius:20px; height:8px; overflow:hidden;">
                            <div style="height:100%; width:${pct}%; background:linear-gradient(90deg,#3b82f6,#8b5cf6); border-radius:20px; transition:width 0.5s ease;"></div>
                        </div>
                    </div>`;
            }).join('')
        }
        </div>

        <!-- Gender Breakdown -->
        <div class="card" style="padding:20px; text-align:center;">
            <div class="card-header" style="margin-bottom:14px;">
                <h3><i class="fas fa-venus-mars" style="color:#8b5cf6;"></i> Gender</h3>
            </div>
            <div style="position:relative; width:100px; height:100px; margin:0 auto 12px;">
                <div style="
                    width:100px; height:100px; border-radius:50%;
                    background: conic-gradient(#3b82f6 0deg ${mAngle}deg, #f472b6 ${mAngle}deg 360deg);
                "></div>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:60px; height:60px; background:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; color:var(--text-main);">
                    ${total}
                </div>
            </div>
            <div style="display:flex; gap:10px; justify-content:center; font-size:12px;">
                <span><span style="display:inline-block;width:10px;height:10px;background:#3b82f6;border-radius:2px;margin-right:4px;"></span>L: ${data.male_count} (${malePct}%)</span>
                <span><span style="display:inline-block;width:10px;height:10px;background:#f472b6;border-radius:2px;margin-right:4px;"></span>P: ${data.female_count} (${femalePct}%)</span>
            </div>
        </div>

        <!-- Visit Frequency -->
        <div class="card" style="padding:20px;">
            <div class="card-header" style="margin-bottom:14px;">
                <h3><i class="fas fa-redo" style="color:#10b981;"></i> Frekuensi</h3>
            </div>
            <p style="font-size:11px; color:var(--text-muted); margin-bottom:12px;">Berapa kali pasien datang berkunjung</p>
            ${([
            { label: '1x kunjungan', key: '1', color: '#fbbf24' },
            { label: '2-4x kunjungan', key: '2-4', color: '#3b82f6' },
            { label: '5x+ (loyal)', key: '5+', color: '#10b981' },
        ] as Array<{ label: string; key: "1" | "2-4" | "5+"; color: string }>).map(f => {
            const count = vf[f.key] || 0;
            const pct = total > 0 ? Math.round(count / total * 100) : 0;
            return `
                <div style="margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
                        <span>${f.label}</span>
                        <span style="font-weight:700; color:${f.color};">${count} pasien</span>
                    </div>
                    <div style="background:#f0f4ff; border-radius:20px; height:7px; overflow:hidden;">
                        <div style="height:100%; width:${pct}%; background:${f.color}; border-radius:20px;"></div>
                    </div>
                </div>`;
        }).join('')}
        </div>
    </div>

    <!-- ── Row 4: Recent Visits Table ────────────────────────────────────── -->
    <div class="card" style="padding:0;">
        <div class="card-header" style="padding:16px 20px 12px;">
            <h3><i class="fas fa-history" style="color:#6366f1;"></i> 10 Transaksi Terbaru</h3>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Tanggal</th>
                        <th>Transaksi</th>
                        <th>Keterangan</th>
                        <th style="text-align:center;">Qty/Titik</th>
                        <th style="text-align:right;">Nilai</th>
                    </tr>
                </thead>
                <tbody>
                    ${recent.length === 0
            ? `<tr><td colspan="5" style="text-align:center;padding:30px;color:var(--text-muted);">Belum ada transaksi.</td></tr>`
            : recent.map((r, i) => {
                const isHerbal = r.type === 'herbal';
                const isReturn = r.transaction_type === 'return' || r.transaction_type === 'retur';
                const badge = isHerbal
                    ? `<span style="font-size:10px; color:${isReturn ? '#b45309' : '#047857'}; background:${isReturn ? '#fef3c7' : '#d1fae5'}; padding:2px 6px; border-radius:999px; font-weight:700;">${isReturn ? 'RETUR' : 'HERBAL'}</span>`
                    : '<span style="font-size:10px; color:#1d4ed8; background:#dbeafe; padding:2px 6px; border-radius:999px; font-weight:700;">KUNJUNGAN</span>';
                const statusBadge = r.invoice_status === 'void'
                    ? '<span style="font-size:10px; color:#b91c1c; background:#fee2e2; padding:2px 6px; border-radius:999px; font-weight:800;">VOID</span>'
                    : '';
                return `
                        <tr style="${i % 2 === 1 ? 'background:#fafbff;' : ''}">
                            <td style="color:var(--text-muted); font-size:13px;">${escapeHtml(r.date)}</td>
                            <td style="font-weight:600;">
                                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                                    ${badge}
                                    ${statusBadge}
                                    <span>${escapeHtml(r.patient)}</span>
                                </div>
                            </td>
                            <td style="color:var(--text-muted);">${escapeHtml(r.therapist)}</td>
                            <td style="text-align:center; font-weight:700;">${r.point_count} <span style="font-size:10px;font-weight:normal;color:#aaa;">${isHerbal ? 'pcs' : 'pt'}</span></td>
                            <td style="text-align:right; font-weight:700; color:#27ae60;">${formatRupiah(r.price)}</td>
                        </tr>`;
            }).join('')
        }
                </tbody>
            </table>
        </div>
    </div>`;

    document.getElementById('display-area')!.innerHTML = html;
    updateProfitLossPreview();
}

function updateProfitLossPreview(): void {
    const data = window._analyticsProfitData || {};
    const expenseInput = document.getElementById('profit-operational-expense') as HTMLInputElement | null;
    const expense = Math.max(0, Number(expenseInput?.value || 0));
    const grossProfit = Number(data.gross_profit || 0);
    const target = document.getElementById('profit-net-preview');
    if (target) target.textContent = formatRupiah(grossProfit - expense);
}

window.renderAnalytics = renderAnalytics;
window.updateProfitLossPreview = updateProfitLossPreview;
