import traceback
from database import Database
from fastapi.encoders import jsonable_encoder

def test():
    db = Database()
    try:
        patients = db.get_all_patients()
        therapists = db.get_all_therapists(active_only=True)
        res = {"patients": patients, "therapists": therapists}
        
        # Test serialization that FastAPI does internally
        encoded = jsonable_encoder(res)
        print("Success! Encoding worked:", str(encoded)[:100])
        
    except Exception as e:
        traceback.print_exc()

if __name__ == '__main__':
    test()
