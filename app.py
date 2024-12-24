from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["TestDatabase"]
movies_collection = db["movies"]
users_collection = db["users"]


# ratings_collection = db["ratings"]


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":  # Handle form submission
        email = request.form.get("email")
        password = request.form.get("password")

        user = users_collection.find_one({"email": email})

        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])  # Store user ID in session
            return redirect(url_for('home'))  # Redirect to the home page
        return render_template("login.html", error="Invalid credentials")  # Render error

    # Render login page on GET request
    return render_template("login.html")

@app.route("/home", methods=["GET"])
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    movies = list(movies_collection.find())
    return render_template("home.html", movies=movies)

@app.route("/film/<movie_id>", methods=['GET'])
def film(movie_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    movie = movies_collection.find_one({"_id": ObjectId(movie_id)})
    if not movie:
        return "Movie not found", 404
    return render_template('film.html', movie=movie)

@app.route("/logout", methods=["GET"])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route("/profile")
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        return "User not found", 404

    return render_template("profile.html", user=user)

@app.route("/createaccount", methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if users_collection.find_one({"email": email}):
            return render_template("createaccount.html", error="Account already exists!")

        hashed_password = generate_password_hash(password)
        users_collection.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password
        })
        return redirect(url_for('login'))

    return render_template("createaccount.html")

@app.route("/update-watchlist", methods=["POST"])
def update_watchlist():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        user_id = session['user_id']
        movie_id = request.json.get("movie_id")
        movie_title = request.json.get("movie_title")

        if not movie_title or not movie_id:
            return jsonify({"error": "Missing movie_title or movie_id"}), 400

        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"watchlist": {"movie_id": ObjectId(movie_id), "title": movie_title}}}
        )
        if result.modified_count == 0:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": f"'{movie_title}' added to watchlist"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/rate-movie", methods=["POST"])
def rate_movie():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        user_id = session['user_id']
        movie_id = request.json.get("movie_id")
        rating = request.json.get("rating")
        movie_title = request.json.get("movie_title")

        if not movie_id or rating is None or not movie_title:
            return jsonify({"error": "Missing movie_id, rating, or movie_title"}), 400

        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"ratings": {"movie_id": ObjectId(movie_id), "title": movie_title, "rating": rating}}}
        )
        if result.modified_count == 0:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": f"Rating for '{movie_title}' saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
