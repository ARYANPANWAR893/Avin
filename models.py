from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    credits = db.Column(db.Integer, default=0)
    public_profile = db.Column(db.Boolean, default=True)


class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    original_text = db.Column(db.Text)
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(50))
    location = db.Column(db.String(120))
    severity = db.Column(db.String(20))
    status = db.Column(db.String(30))
    created_at = db.Column(db.DateTime)
    estimated_days = db.Column(db.Integer, nullable=True)


    def to_dict(self):
        return {
            "id": self.id,
            "text": self.original_text,
            "category": self.category,
            "subcategory": self.subcategory,
            "location": self.location,
            "severity": self.severity,
            "status": self.status
        }


class Mission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    category = db.Column(db.String(50))
    location = db.Column(db.String(120))
    blockchain_tx = db.Column(db.String)
    status = db.Column(db.String(30))
    created_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)


class LedgerEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    mission_id = db.Column(db.Integer)
    category = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "mission_id": self.mission_id,
            "category": self.category,
            "timestamp": self.timestamp.isoformat()
        }

class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    min_credits = db.Column(db.Integer)
    description = db.Column(db.String)
