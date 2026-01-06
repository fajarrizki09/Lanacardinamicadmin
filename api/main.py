from fastapi import FastAPI, HTTPException
from database import Database
import os

app = FastAPI(title="Lancar Dinamic API")

# Gunakan database yang sama dengan aplikasi desktop
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.db"))
db = Database(f"sqlite:///{db_path}")

@app.get("/")
def read_root():
    return {"message": "Lancar Dinamic API is running", "database": db_path}

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
