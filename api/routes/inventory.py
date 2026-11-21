from fastapi import APIRouter, HTTPException, Form, Request
from api.admin_pin import require_admin_pin
from api.database_manager import db
from api.license_guard import require_valid_license

router = APIRouter()

@router.get("/inventory")
def get_inventory():
    try:
        return db.get_all_inventory()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _inventory_meta(item_id):
    try:
        return next((item for item in db.get_all_inventory() if int(item.get("id")) == int(item_id)), {}) or {}
    except Exception:
        return {}

@router.post("/update_inventory")
async def update_inventory(
    request: Request,
    item_id: int = Form(...),
    quantity_change: int = Form(...),
    multiplier: int = Form(1),
    note: str = Form("")
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if multiplier < 1:
            raise ValueError("Multiplier minimal 1.")
        total_change = quantity_change * multiplier
        before = _inventory_meta(item_id)
        success = db.update_stock(
            item_id,
            total_change,
            transaction_type="stock_in" if total_change > 0 else "stock_out",
            note=note.strip() or None,
        )
        if not success:
            raise ValueError("Item not found")
        after = _inventory_meta(item_id)
        db.log_audit("inventory_stock_corrected", "inventory", item_id, "Stok inventory dikoreksi.", {
            "item_name": before.get("item_name") or after.get("item_name"),
            "change": total_change,
            "quantity_before": before.get("quantity"),
            "quantity_after": after.get("quantity"),
            "unit": before.get("unit") or after.get("unit"),
        })
        return {"status": "success", "message": f"Stok inventory berhasil diperbarui. Bersih: {total_change} satuan."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/add_inventory")
async def add_inventory(
    request: Request,
    item_name: str = Form(...),
    item_type: str = Form("consumable"),
    unit: str = Form("pcs"),
    min_stock: int = Form(10),
    initial_qty: int = Form(0),
    package_unit: str = Form(""),
    package_size: int = Form(1),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if not item_name.strip():
            raise ValueError("Nama inventory wajib diisi.")
        if initial_qty < 0:
            raise ValueError("Stok awal tidak boleh negatif.")
        if min_stock < 0:
            raise ValueError("Stok minimum tidak boleh negatif.")
        item_id = db.add_inventory_item(item_name, unit, min_stock, initial_qty, package_unit.strip() or None, package_size, item_type)
        db.log_audit("inventory_created", "inventory", item_id, "Inventory baru ditambahkan.", {
            "item_name": item_name.strip(),
            "item_type": item_type,
            "unit": unit,
            "package_unit": package_unit.strip(),
            "package_size": package_size,
            "min_stock": min_stock,
            "initial_qty": initial_qty,
        })
        return {"status": "success", "message": "Item inventory berhasil didaftarkan."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/edit_inventory")
async def edit_inventory(
    request: Request,
    item_id: int = Form(...),
    item_name: str = Form(...),
    item_type: str = Form("consumable"),
    quantity: int = Form(...),
    unit: str = Form("pcs"),
    min_stock: int = Form(10),
    package_unit: str = Form(""),
    package_size: int = Form(1),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if not item_name.strip():
            raise ValueError("Nama inventory wajib diisi.")
        if quantity < 0:
            raise ValueError("Stok inventory tidak boleh negatif.")
        if min_stock < 0:
            raise ValueError("Stok minimum tidak boleh negatif.")
        before = _inventory_meta(item_id)
        success = db.update_inventory_item(item_id, item_name, quantity, unit, min_stock, package_unit.strip() or None, package_size, item_type)
        if not success:
            raise ValueError("Inventory not found")
        db.log_audit("inventory_updated", "inventory", item_id, "Data inventory diperbarui.", {
            "item_name": item_name.strip(),
            "old_item_name": before.get("item_name"),
            "item_type": item_type,
            "quantity": quantity,
            "quantity_before": before.get("quantity"),
            "unit": unit,
            "package_unit": package_unit.strip(),
            "package_size": package_size,
            "min_stock": min_stock,
        })
        return {"status": "success", "message": "Data inventory berhasil diperbarui."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/delete_inventory")
async def delete_inventory(request: Request, item_id: int = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        before = _inventory_meta(item_id)
        success = db.delete_inventory_item(item_id)
        if not success:
            raise ValueError("Inventory not found")
        db.log_audit("inventory_deactivated", "inventory", item_id, "Inventory dinonaktifkan.", {
            "item_name": before.get("item_name"),
            "quantity": before.get("quantity"),
            "unit": before.get("unit"),
        })
        return {"status": "success", "message": "Inventory berhasil dinonaktifkan."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
