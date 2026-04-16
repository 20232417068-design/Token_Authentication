from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from flask_cors import CORS
from extensions import db
from models import User
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
CORS(app)

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

# Init
db.init_app(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# ------------------ PAGES ------------------ #

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register-page')
def register_page():
    return render_template("register.html")

@app.route('/dashboard-page')
def dashboard_page():
    return render_template("dashboard.html")

# ------------------ AUTH ------------------ #

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    hashed_password = bcrypt.generate_password_hash(
        data['password']
    ).decode('utf-8')

    user = User(
        username=data['username'],
        password=hashed_password,
        has_voted=False,
        vote=None
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
    try:
        user_id = int(get_jwt_identity())

        user = db.session.get(User, user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "username": user.username,
            "has_voted": user.has_voted,
            "vote": user.vote
        })

    except Exception as e:
        print("Dashboard Error:", e)
        return jsonify({"error": "Server error"}), 500
# ------------------ VOTING ------------------ #

@app.route('/vote', methods=['POST'])
@jwt_required()
def vote():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    candidate = data.get("candidate")

    if candidate not in ["A", "B", "C", "D"]:
        return jsonify({"message": "Invalid candidate"}), 400

    if user.has_voted:
        return jsonify({"message": "You already voted"}), 400

    user.vote = candidate
    user.has_voted = True

    db.session.commit()

    return jsonify({"message": f"Vote submitted for {candidate}"})


# ------------------ RESULTS ------------------ #

@app.route('/results', methods=['GET'])
def results():
    users = User.query.all()

    result = {"A": 0, "B": 0, "C": 0, "D": 0}
    total_votes = 0

    for user in users:
        if user.vote and user.vote in result:
            result[user.vote] += 1
            total_votes += 1

    percentage = {
        key: round((result[key] / total_votes) * 100, 2) if total_votes > 0 else 0
        for key in result
    }

    # Winner logic
    winner = None
    if total_votes > 0:
        max_votes = max(result.values())
        winners = [k for k, v in result.items() if v == max_votes]

        if len(winners) == 1:
            winner = winners[0]
        else:
            winner = "Tie: " + ", ".join(winners)

    return jsonify({
        "votes": result,
        "percentage": percentage,
        "total": total_votes,
        "winner": winner
    })


# ------------------ DB ------------------ #

with app.app_context():
    db.create_all()


# ------------------ RUN ------------------ #

if __name__ == '__main__':
    app.run(debug=True)