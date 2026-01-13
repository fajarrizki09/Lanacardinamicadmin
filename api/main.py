from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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
            <title>Lancar Dinamic - Web Dashboard</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; background: #f5f6fa; }
                .header { background: #2c3e50; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
                .tab-bar { background: #34495e; display: flex; padding: 0 20px; }
                .tab { padding: 15px 25px; cursor: pointer; color: #bdc3c7; border-bottom: 3px solid transparent; transition: 0.3s; }
                .tab:hover { color: white; background: rgba(255,255,255,0.1); }
                .tab.active { color: white; border-bottom-color: #3498db; font-weight: bold; background: rgba(255,255,255,0.05); }
                .content { flex: 1; padding: 30px; overflow-y: auto; }
                .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { text-align: left; padding: 12px; border-bottom: 1px solid #eee; }
                th { background: #f8f9fa; color: #7f8c8d; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }
                .status-badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
                .status-low { background: #fff5f5; color: #e53e3e; }
                .status-ok { background: #f0fff4; color: #38a169; }
                .loading { display: none; text-align: center; padding: 50px; color: #7f8c8d; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; color: #2c3e50; font-weight: bold; }
                input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
                .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
                .btn:hover { background: #2980b9; }
            </style>
        </head>
        <body>
            <div class="header">
                <div style="font-size: 20px; font-weight: bold;">🏥 Lancar Dinamic Dashboard</div>
                <div style="font-size: 14px; opacity: 0.8;">Live Database Sync</div>
            </div>
            <div class="tab-bar">
                <div class="tab active" onclick="showTab('patients')">👥 Pasien</div>
                <div class="tab" onclick="showTab('inventory')">📦 Inventori</div>
                <div class="tab" onclick="showTab('herbals')">🌿 Herbal</div>
                <div class="tab" onclick="window.open('/docs', '_blank')">⚙️ API Docs</div>
            </div>
            
            <div id="content" class="content">
                <div id="loading" class="loading">Memuat data...</div>
                <div id="display-area"></div>
            </div>

            <script>
                async function showTab(tabName) {
                    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                    const tabs = Array.from(document.querySelectorAll('.tab'));
                    const targetText = tabName === 'patients' ? 'Pasien' : tabName === 'inventory' ? 'Inventori' : 'Herbal';
                    const activeTab = tabs.find(t => t.textContent.includes(targetText));
                    if (activeTab) activeTab.classList.add('active');
                    
                    const displayArea = document.getElementById('display-area');
                    const loading = document.getElementById('loading');
                    
                    displayArea.innerHTML = '';
                    loading.style.display = 'block';
                    
                    try {
                        const response = await fetch('/' + tabName);
                        const data = await response.json();
                        loading.style.display = 'none';
                        
                        if (tabName === 'patients') renderPatients(data);
                        else if (tabName === 'inventory') renderInventory(data);
                        else if (tabName === 'herbals') renderHerbals(data);
                    } catch (e) {
                        displayArea.innerHTML = '<div class="card" style="color:red">Gagal memuat data: ' + e.message + '</div>';
                        loading.style.display = 'none';
                    }
                }

                function renderPatients(data) {
                    let html = `
                        <div class="card">
                            <h3>➕ Tambah Pasien Baru</h3>
                            <form action="/add_patient" method="post">
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                    <div class="form-group">
                                        <label>Nama Lengkap</label>
                                        <input type="text" name="name" required placeholder="Nama Pasien">
                                    </div>
                                    <div class="form-group">
                                        <label>Nomor Telepon</label>
                                        <input type="text" name="phone" required placeholder="08xxxx">
                                    </div>
                                    <div class="form-group">
                                        <label>Alamat</label>
                                        <input type="text" name="address" placeholder="Alamat Lengkap">
                                    </div>
                                    <div class="form-group">
                                        <label>Gender</label>
                                        <select name="gender">
                                            <option value="Laki-laki">Laki-laki</option>
                                            <option value="Perempuan">Perempuan</option>
                                        </select>
                                    </div>
                                </div>
                                <button type="submit" class="btn">Daftarkan Pasien</button>
                            </form>
                        </div>
                        <div class="card">
                            <h2>Daftar Pasien Terdaftar</h2>
                            <table>
                                <tr><th>Nama</th><th>Telepon</th><th>Alamat</th><th>Gender</th></tr>`;
                    data.forEach(p => {
                        html += \`<tr><td><b>\${p.name}</b></td><td>\${p.phone}</td><td>\${p.address || '-'}</td><td>\${p.gender}</td></tr>\`;
                    });
                    html += '</table></div>';
                    document.getElementById('display-area').innerHTML = html;
                }

                function renderInventory(data) {
                    let html = '<div class="card"><h2>Stok Alat & Bahan</h2><table><tr><th>Nama Alat</th><th>Stok</th><th>Min</th><th>Status</th></tr>';
                    data.forEach(i => {
                        const isLow = i.quantity <= i.min_stock;
                        html += \`<tr><td>\${i.item_name}</td><td>\${i.quantity} \${i.unit}</td><td>\${i.min_stock}</td>
                                 <td><span class="status-badge \${isLow ? 'status-low' : 'status-ok'}">\${isLow ? 'STOK RENDAH' : 'AMAN'}</span></td></tr>\`;
                    });
                    html += '</table></div>';
                    document.getElementById('display-area').innerHTML = html;
                }

                function renderHerbals(data) {
                    let html = '<div class="card"><h2>Stok Obat Herbal</h2><table><tr><th>Nama Herbal</th><th>Stok</th><th>Harga</th><th>Satuan</th></tr>';
                    data.forEach(h => {
                        html += \`<tr><td><b>\${h.name}</b></td><td>\${h.stock}</td><td>Rp \${h.price.toLocaleString()}</td><td>\${h.unit}</td></tr>\`;
                    });
                    html += '</table></div>';
                    document.getElementById('display-area').innerHTML = html;
                }

                window.onload = () => showTab('patients');
            </script>
        </body>
    </html>
    """

@app.get("/patients")
def get_patients():
    try:
        return db.get_all_patients()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_patient")
async def add_patient(name: str = Form(...), phone: str = Form(...), address: str = Form(""), gender: str = Form("Laki-laki")):
    try:
        db.add_patient(name, phone, address, gender)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
