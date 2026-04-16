from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # ✅ ADD THESE
    has_voted = db.Column(db.Boolean, default=False)
    vote = db.Column(db.String(10), nullable=True)