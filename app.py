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

# ------------------ CONFIG ------------------ #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

# ------------------ INIT ------------------ #
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

    # ✅ validation
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"message": "All fields required"}), 400

    # ✅ check duplicate user
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "User already exists"}), 400

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
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    return jsonify({
        "message": f"Welcome {user.username}",
        "has_voted": user.has_voted,
        "vote": user.vote
    })


@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)

    return jsonify(access_token=new_access_token)

# ------------------ DATABASE ------------------ #
with app.app_context():
    db.create_all()

# ------------------ VOTING ------------------ #
@app.route('/vote', methods=['POST'])
@jwt_required()
def vote():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    data = request.get_json()

    if not data or "candidate" not in data:
        return jsonify({"message": "Invalid data"}), 400

    candidate = data["candidate"]

    if candidate not in ["A", "B", "C", "D"]:
        return jsonify({"message": "Invalid candidate"}), 400

    # ✅ prevent multiple voting
    if user.has_voted:
        return jsonify({"message": "You already voted"}), 400

    user.vote = candidate
    user.has_voted = True

    db.session.commit()

    return jsonify({"message": f"✅ Vote submitted for {candidate}"})


# ------------------ USER STATUS ------------------ #
@app.route('/user-status', methods=['GET'])
@jwt_required()
def user_status():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    return jsonify({
        "has_voted": user.has_voted,
        "vote": user.vote
    })


# -----@app.route('/results', methods=['GET'])
def results():
    try:
        users = User.query.all()

        # Initialize vote count
        result = {"A": 0, "B": 0, "C": 0, "D": 0}
        total_votes = 0

        for user in users:
            # ✅ Safe check (prevents crash if column missing)
            if hasattr(user, "vote") and user.vote and user.vote in result:
                result[user.vote] += 1
                total_votes += 1

        # ✅ Percentage calculation
        percentage = {}
        for key in result:
            if total_votes > 0:
                percentage[key] = round((result[key] / total_votes) * 100, 2)
            else:
                percentage[key] = 0

        # 🏆 Winner logic (handles tie also)
        winner = None
        winners = []

        if total_votes > 0:
            max_votes = max(result.values())
            winners = [k for k, v in result.items() if v == max_votes]

            # if only one winner
            if len(winners) == 1:
                winner = winners[0]
            else:
                winner = "Tie between " + ", ".join(winners)

        return jsonify({
            "votes": result,
            "percentage": percentage,
            "total": total_votes,
            "winner": winner
        })

    except Exception as e:
        return jsonify({"error": str(e)})#------------- RESULTS ------------------ #


# ------------------ RUN ------------------ #
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))