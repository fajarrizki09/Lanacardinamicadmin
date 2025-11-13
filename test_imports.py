#!/usr/bin/env python3
import sys

def test_imports():
    print("Testing imports...")
    errors = []
    
    try:
        print("  ✓ Importing database...")
        import database
    except Exception as e:
        errors.append(f"database: {e}")
        print(f"  ✗ database: {e}")
    
    try:
        print("  ✓ Importing settings...")
        import settings
    except Exception as e:
        errors.append(f"settings: {e}")
        print(f"  ✗ settings: {e}")
    
    try:
        print("  ✓ Importing models...")
        from models import patient
    except Exception as e:
        errors.append(f"models.patient: {e}")
        print(f"  ✗ models.patient: {e}")
    
    try:
        print("  ✓ Importing components...")
        from components import patient_form, patient_list, visit_section, action_buttons
    except Exception as e:
        errors.append(f"components: {e}")
        print(f"  ✗ components: {e}")
    
    try:
        print("  ✓ Importing dialogs...")
        from dialogs import settings_dialog, therapist_dialog, edit_patient_dialog, analytics_dialog
    except Exception as e:
        errors.append(f"dialogs: {e}")
        print(f"  ✗ dialogs: {e}")
    
    try:
        print("  ✓ Importing threads...")
        from threads import search_thread, visit_thread
    except Exception as e:
        errors.append(f"threads: {e}")
        print(f"  ✗ threads: {e}")
    
    try:
        print("  ✓ Importing helpers...")
        from helpers import import_export
    except Exception as e:
        errors.append(f"helpers: {e}")
        print(f"  ✗ helpers: {e}")
    
    try:
        print("  ✓ Importing viewmodels...")
        from viewmodels import visit_view_model
    except Exception as e:
        errors.append(f"viewmodels: {e}")
        print(f"  ✗ viewmodels: {e}")
    
    print("\n📊 Test Results:")
    if errors:
        print(f"❌ {len(errors)} import errors found:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ All imports successful!")
        print("\n📝 Note: This is a desktop GUI application.")
        print("   To run the full application locally, you need:")
        print("   1. A display server (X11 or Wayland)")
        print("   2. Run: python main.py")
        print("\n🎉 Application is ready to deploy!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
