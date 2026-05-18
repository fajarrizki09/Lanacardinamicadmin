# Flowchart 11 — Reports / Analytics / Owner Report

## Scope

Logic dashboard, analytics, report export, Excel export, KPI cards, owner report, revenue rules, dan pencegahan double count.

```mermaid
flowchart TD
    A[Admin buka Dashboard/Reports] --> B[api/static/modules/dashboard.js / analytics.js / owner_report.js]
    B --> C[Call API reports/analytics]

    C --> D[api/routes/analytics.py]
    C --> E[api/routes/reports.py]
    C --> F[api/routes/owner_report.py]

    D --> G[helpers/dashboard_stats_helper.py]
    E --> H[helpers/report_export_helper.py]
    F --> I[helpers/owner_report_helper.py]
    G --> J[helpers/revenue_rules.py]
    H --> J
    I --> J

    J --> K[(SQLite DB)]
    K --> L[Visits]
    K --> M[Herbal Transactions]
    K --> N[Invoices]
    K --> O[Inventory]
    K --> P[Patients]

    L --> Q{invoice_status = void?}
    M --> Q
    Q -->|Ya| R[revenue = 0]
    Q -->|Tidak| S{payment_status}
    S -->|paid| T[revenue = total]
    S -->|partial| U[revenue = amount_paid]
    S -->|unpaid/pending/failed/expired/void| V[revenue = 0]

    T --> W[Aggregate revenue]
    U --> W
    V --> W
    R --> W

    M --> X{Herbal terkait visit?}
    X -->|Ya| Y[Jangan hitung dobel sebagai herbal mandiri]
    X -->|Tidak| Z[Hitung sebagai transaksi herbal mandiri]
    Y --> W
    Z --> W

    P --> AA[Patient metrics]
    O --> AB[Stock metrics]
    W --> AC[Charts / KPI Cards]
    AA --> AC
    AB --> AC

    AC --> AD{Export?}
    AD -->|Tidak| AE[Tampilkan UI]
    AD -->|Ya| AF[Generate Excel/PDF/CSV]
    AF --> AG[exports/]
```

## Rekomendasi Helper

`helpers/revenue_rules.py` sebagai single source of truth revenue:

- `invoice_status = void` => revenue `0`.
- `payment_status = paid` => revenue `total`.
- `payment_status = partial` => revenue `amount_paid`.
- `payment_status = unpaid/pending/failed/expired/void` => revenue `0`.

Helper ini harus dipakai oleh:

- dashboard
- analytics
- owner_report
- report export
- Excel export
- KPI cards

## Logic Notes

- Semua angka revenue harus memakai helper/rule yang sama.
- Herbal terkait visit jangan dihitung dobel sebagai herbal mandiri.
- Herbal mandiri dihitung sebagai transaksi sendiri.
- Visit invoice total boleh mencakup layanan + herbal terkait visit.
- Owner report dan dashboard harus memakai rule yang sama agar angka tidak berbeda.
- Void invoice tidak masuk revenue.
