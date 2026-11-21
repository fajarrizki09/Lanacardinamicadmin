class PatientMixin:
    """
    Backward-compatible marker mixin.

    Runtime implementations live on Database in database.py. The duplicate
    method bodies were removed so Python MRO cannot hide stale patient logic
    here if Database is refactored later.
    """
    pass
