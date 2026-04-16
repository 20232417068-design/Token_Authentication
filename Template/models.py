from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

    has_voted = db.Column(db.Boolean, default=False)
    vote = db.Column(db.String(50))