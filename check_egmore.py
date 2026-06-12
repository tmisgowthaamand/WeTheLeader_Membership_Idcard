from pymongo import MongoClient
import config

client = MongoClient(config.MONGO_URI)
db = client[config.MONGO_DB]

count_16 = db.voters.count_documents({"ASSEMBLY_NO": "16"})
total = db.voters.count_documents({})

print(f"Voters with ASSEMBLY_NO=16 (Egmore): {count_16}")
print(f"Total voters in collection: {total}")

if count_16 > 0:
    sample = db.voters.find_one({"ASSEMBLY_NO": "16"})
    print("\nSample record:")
    for k, v in sample.items():
        if k != "_id":
            print(f"  {k}: {v}")
