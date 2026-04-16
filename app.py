from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)


from extensions import db
from models import User

app = Flask(__name__)

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
    return jsonify({"message": f"Welcome User {user_id}"})

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)

    return jsonify(access_token=new_access_token)
# -------- DATABASE -------- #
with app.app_context():
    db.create_all()


# -------- RUN -------- #
import os

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))