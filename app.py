from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from flask_cors import CORS

from extensions import db
from models import User

app = Flask(__name__)
CORS(app)
# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

# Initialize
db.init_app(app)
jwt = JWTManager(app)

@app.route('/')
def home():
    return "API is running 🚀"
# -------- ROUTES -------- #


from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    hashed_password = bcrypt.generate_password_hash(
        data['password']
    ).decode('utf-8')

    user = User(
        username=data['username'],
        password=hashed_password
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    user = User.query.filter_by(username=data['username']).first()

    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify(
            access_token=access_token,
            refresh_token=refresh_token
        )

    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify({"message": f"Welcome {user.username}"})

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)

    return jsonify(access_token=new_access_token)
# -------- DATABASE -------- #
with app.app_context():
    db.create_all()
# 🗳️ Vote 
@app.route('/vote', methods=['POST'])
@jwt_required()
def vote():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    data = request.get_json()

    if not data or "candidate" not in data:
        return jsonify({"message": "Invalid data"}), 400

    candidate = data["candidate"]

    # ✅ FIX: allow only valid candidates
    if candidate not in ["A", "B", "C", "D"]:
        return jsonify({"message": "Invalid candidate"}), 400

    # ✅ FIX: safe access
    if not hasattr(user, "has_voted"):
        user.has_voted = False

    if not hasattr(user, "vote"):
        user.vote = None

    if user.has_voted:
        return jsonify({"message": "You already voted"}), 400

    user.vote = candidate
    user.has_voted = True

    db.session.commit()

    return jsonify({"message": f"Vote submitted for {candidate}"})
# 📊 Results API
@app.route('/results', methods=['GET'])
def results():
    try:
        users = User.query.all()

        result = {
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0
        }

        total_votes = 0

        for user in users:
             if hasattr(user, "vote") and user.vote and user.vote in result:
                result[user.vote] += 1
                total_votes += 1

        percentage = {}
        for key in result:
            if total_votes > 0:
                percentage[key] = round((result[key] / total_votes) * 100, 2)
            else:
                percentage[key] = 0

        return jsonify({
            "votes": result,
            "percentage": percentage,
            "total": total_votes
        })

    except Exception as e:
        return jsonify({"error": str(e)})
import os
print("Columns:", User.__table__.columns.keys())
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))