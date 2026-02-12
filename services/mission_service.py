from models import db, Mission
from datetime import datetime

def generate_missions(issue):

    missions = []

    title = f"Resolve {issue.subcategory} in {issue.location}"

    mission = Mission(
        issue_id=issue.id,
        user_id=issue.user_id,
        title=title,
        category=issue.category,
        location=issue.location,
        status="OPEN",
        created_at=datetime.utcnow()
    )

    db.session.add(mission)
    db.session.commit()

    missions.append({
        "mission_id": mission.id,
        "title": mission.title
    })

    return missions
