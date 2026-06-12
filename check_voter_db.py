"""
Inspect the DigitalOcean voter_db schema — collections, sample docs, indexes.
"""
from pymongo import MongoClient

VOTER_URL = "mongodb+srv://doadmin:K1jb38520POU7pv4@db-mdb-blr1-62418-1d213a0a.mongo.ondigitalocean.com/voter_db?authSource=admin&tls=true"
VOTER_DB  = "voter_db"

print("Connecting to DigitalOcean voter_db ...")
client = MongoClient(VOTER_URL, serverSelectionTimeoutMS=20000)
db = client[VOTER_DB]

# List collections
cols = db.list_collection_names()
print(f"\nCollections ({len(cols)}): {cols}")

for col_name in cols[:5]:   # inspect first 5 collections
    col = db[col_name]
    try:
        count = col.estimated_document_count()
    except Exception:
        count = '?'
    print(f"\n{'='*60}")
    print(f"Collection: {col_name}  |  estimated docs: {count}")

    # Sample document
    doc = col.find_one()
    if doc:
        doc.pop('_id', None)
        print("Keys:", list(doc.keys()))
        print("Sample values:")
        for k, v in list(doc.items())[:20]:
            print(f"   {k}: {repr(v)[:80]}")
    else:
        print("  (empty)")

    # Indexes
    try:
        indexes = list(col.list_indexes())
        print(f"Indexes ({len(indexes)}):")
        for idx in indexes:
            print(f"  {idx.get('name')}: {dict(idx.get('key', {}))}")
    except Exception as e:
        print(f"  Indexes error: {e}")

client.close()
print("\nDone.")
