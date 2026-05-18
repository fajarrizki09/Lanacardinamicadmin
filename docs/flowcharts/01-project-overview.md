# Flowchart 01 — Project Overview

## Scope

Gambaran besar arsitektur aktif LancarDinamicAdmin.

```mermaid
flowchart TD
    A[User membuka aplikasi desktop] --> B[main.py]
    B --> C[PySide6 WebEngine Shell]
    B --> D[FastAPI Local Server]
    C --> E[Load Web UI]
    D --> F[api/templates/index.html]
    F --> G[api/static/modules/*.js]

    G --> H[Dashboard]
    G --> I[Patients & Visits]
    G --> J[Invoices]
    G --> K[Inventory]
    G --> L[Herbals]
    G --> M[CRM Follow-up]
    G --> N[Reports & Analytics]
    G --> O[Settings / Backup / License]

    H --> P[api/routes/analytics.py]
    I --> Q[api/routes/patients.py]
    J --> R[api/routes/invoices.py]
    J --> S[api/routes/payments.py]
    K --> T[api/routes/inventory.py]
    L --> U[api/routes/herbals.py]
    M --> V[api/routes/crm.py]
    N --> W[api/routes/reports.py / owner_report.py]
    O --> X[api/routes/settings.py / license_guard.py]

    P --> Y[api/database_manager.py]
    Q --> Y
    R --> Y
    S --> Y
    T --> Y
    U --> Y
    V --> Y
    W --> Y
    X --> Y

    Y --> Z[(SQLite Local Database)]
    Z --> AA[db_models.py]

    R --> AB[helpers/invoice_helper.py]
    V --> AC[helpers/crm_analysis_helper.py]
    W --> AD[helpers/report/helper layer]
    O --> AE[helpers/backup_helper.py]

    AB --> AF[invoices/ PDF output]
    AE --> AG[backups/]
    X --> AH[settings.json]
    D --> AI[logs/]
```

## Logic Notes

- App berjalan lokal, bukan cloud SaaS.
- Backend FastAPI menjadi pusat API.
- Web UI modular berada di `api/static/modules/`.
- Database utama adalah SQLite lokal via SQLAlchemy models.
- Output runtime utama: PDF invoice, backup database, settings, logs.
