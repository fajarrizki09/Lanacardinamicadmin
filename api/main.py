from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from database import Database
import os

app = FastAPI(title="Lancar Dinamic API")

# Gunakan database yang sama dengan aplikasi desktop
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.db"))
db = Database(f"sqlite:///{db_path}")

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
        <head>
            <title>Lancar Dinamic API</title>
            <style>
                body { font-family: sans-serif; padding: 40px; line-height: 1.6; }
                .container { max-width: 800px; margin: 0 auto; background: #f4f7f6; padding: 30px; border-radius: 10px; }
                h1 { color: #2c3e50; }
                .endpoints { background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
                code { background: #eee; padding: 2px 5px; border-radius: 4px; }
                .btn { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Lancar Dinamic API is Running</h1>
                <p>Logika inti aplikasi Anda sekarang dapat diakses melalui web.</p>
                <div class="endpoints">
                    <h3>📌 Endpoint Tersedia:</h3>
                    <ul>
                        <li><a href="/patients"><code>/patients</code></a> - Data Pasien</li>
                        <li><a href="/inventory"><code>/inventory</code></a> - Stok Alat</li>
                        <li><a href="/herbals"><code>/herbals</code></a> - Stok Herbal</li>
                        <li><a href="/docs"><code>/docs</code></a> - Dokumentasi API Interaktif</li>
                    </ul>
                </div>
                <p>Database path: <code>""" + db_path + """</code></p>
                <a href="/docs" class="btn">Buka Dokumentasi API</a>
            </div>
        </body>
    </html>
    """

@app.get("/patients")
def get_patients():
    try:
        return db.get_all_patients()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventory")
def get_inventory():
    try:
        return db.get_all_inventory()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/herbals")
def get_herbals():
    try:
        return db.get_all_herbals()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
