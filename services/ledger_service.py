from models import db, LedgerEntry
from datetime import datetime

def add_ledger_entry(user_id, mission_id, category):

    entry = LedgerEntry(
        user_id=user_id,
        mission_id=mission_id,
        category=category,
        timestamp=datetime.utcnow()
    )

    db.session.add(entry)
    db.session.commit()
