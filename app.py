from flask import Flask, render_template, request, jsonify, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

# اتصال به MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["TestDatabase"]
movies_collection = db["movies"]
reviews_collection = db["reviews"]
users_collection = db["users"]


@app.route("/")
def index():
    return render_template("auth.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/create_account", methods=["POST"])
def create_account():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if users_collection.find_one({"email": email}):
        return jsonify({"success": False, "message": "Account already exists!"})

    users_collection.insert_one({
        "name": name,
        "email": email,
        "password": password
    })

    return jsonify({"success": True, "message": "Account created successfully!"})


if __name__ == "__main__":
    app.run(debug=True)
