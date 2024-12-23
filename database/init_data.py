from pymongo import MongoClient

# اتصال به MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["TestDatabase"]

# کلکشن‌ها
movies_collection = db["movies"]
users_collection = db["users"]
reviews_collection = db["reviews"]

# داده‌های اولیه
movies = [
    {"title": "Inception", "genre": "Sci-Fi", "year": 2010},
    {"title": "The Dark Knight", "genre": "Action", "year": 2008},
    {"title": "Interstellar", "genre": "Sci-Fi", "year": 2014},
]

# درج اطلاعات اولیه در MongoDB
for movie in movies:
    movies_collection.insert_one(movie)

print("Data inserted successfully!")
