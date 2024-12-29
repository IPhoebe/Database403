from http.client import responses

from dns.message import make_response
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB connection
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["TestDatabase"]
movies_collection = db["movies"]
users_collection = db["users"]
reviews_collection = db["reviews"]


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users_collection.find_one({"email": email})

        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            return redirect(url_for('home'))
        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/home")
def home():
    try:
        top_movies = list(movies_collection.find().sort("rating", -1))
    except Exception:
        top_movies = []

    recommendations = []
    try:
        user_id = session.get('user_id')
        if user_id:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
            if user and 'ratings' in user:
                high_rated_movies = [
                    rating for rating in user["ratings"] if rating["rating"] > 7
                ]
                high_rated_genres = []

                for rating in high_rated_movies:
                    movie = movies_collection.find_one({"_id": ObjectId(rating['movie_id'])})
                    if movie:
                        high_rated_genres.append(movie['genre'])

                unique_genres = list(set(high_rated_genres))

                rated_movie_ids = [ObjectId(rating['movie_id']) for rating in user['ratings']]

                recommendations = list(
                    movies_collection.find({
                        "genre": {"$in": unique_genres},
                        "_id": {"$nin": rated_movie_ids}
                    })
                )
    except Exception:
        recommendations = []

    return render_template("home.html", movies=top_movies, recommendations=recommendations)

@app.route("/film/<movie_id>", methods=['GET'])
def film(movie_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    movie = movies_collection.find_one({"_id": ObjectId(movie_id)})
    if not movie:
        return "Movie not found", 404

    user_id = session['user_id']
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    username = user['name'] if user else "Guest"

    return render_template('film.html', movie=movie, username=username)

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    flash("You have successfully logged out", "success")
    return redirect(url_for('login'))

@app.route("/profile")
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        return "User not found", 404
    user_watchlist = user.get('watchlist', [])
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


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify([])
    movies = list(movies_collection.find({"title": {"$regex": query, "$options": "i"}}))
    result = [{"_id": str(movie["_id"]), "title": movie["title"], "image": movie.get("image", "default_image_url.jpg")}
              for movie in movies]

    return jsonify(result)

@app.route("/api/reviews", methods=["POST"])
def add_review():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        user_id = session['user_id']
        movie_id = request.json.get("movie_id")
        username = request.json.get("username")
        comment = request.json.get("comment")

        if not movie_id or not username or not comment:
            return jsonify({"error": "Missing movie_id, username, or comment"}), 400

        review = {
            "user_id": ObjectId(user_id),
            "movie_id": ObjectId(movie_id),
            "username": username,
            "comment": comment
        }

        reviews_collection.insert_one(review)
        return jsonify({"message": "Review added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reviews/<movie_id>", methods=["GET"])
def get_reviews(movie_id):
    reviews = list(reviews_collection.find({"movie_id": ObjectId(movie_id)}))
    return jsonify([{"username": r["username"], "comment": r["comment"]} for r in reviews])


if __name__ == "__main__":
    app.run(debug=True)