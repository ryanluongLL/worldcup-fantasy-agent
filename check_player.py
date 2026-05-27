from database.schema import get_database
db = get_database()
p = db.players.find_one({"name": {"$regex": "Mbapp", "$options": "i"}}, {"name": 1, "firstname": 1, "lastname": 1, "position": 1, "nationality": 1, "_id": 0})
print(p)
