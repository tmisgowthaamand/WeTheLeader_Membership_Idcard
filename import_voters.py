import os
import sys
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "wetheleaders")

if not MONGO_URI:
    print("Error: MONGO_URI not found in .env")
    sys.exit(1)

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db.voters

def parse_row(line):
    """
    Parses a single row line like: (1, '16', 'Egmore', ..., '600007'),
    Returns a list of values.
    """
    line = line.strip()
    if not line.startswith("("):
        return None
    
    # Remove leading ( and trailing ), or );
    if line.endswith("),") or line.endswith(");"):
        line = line[1:-2]
    elif line.endswith(")"):
        line = line[1:-1]
    else:
        # Might be a partial line or something else
        return None
    
    fields = []
    buffer = ""
    in_string = False
    escaped = False
    
    for c in line:
        if c == "'" and not escaped:
            in_string = not in_string
        elif c == "\\" and in_string:
            escaped = not escaped
            continue
        elif c == "," and not in_string:
            val = buffer.strip()
            if val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            elif val.upper() == "NULL":
                val = None
            fields.append(val)
            buffer = ""
        else:
            buffer += c
        escaped = False
    
    # Last field
    val = buffer.strip()
    if val.startswith("'") and val.endswith("'"):
        val = val[1:-1]
    elif val.upper() == "NULL":
        val = None
    fields.append(val)
    
    return fields

def import_sql_file(filepath):
    print(f"Starting import: {filepath}")
    count = 0
    batch = []
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            r = parse_row(line)
            if not r or len(r) < 20: 
                continue
            
            # Column mapping (verified from head of file):
            # 1:ASSEMBLY_NO, 2:ASSEMBLY_NAME, 3:PART_NO, 4:SECTION_NO, 5:SERIAL_NO, 6:HOUSE_NO, 
            # 7:VOTER_NAME, 8:RELATION_TYPE, 9:RELATION_NAME, 10:EPIC_NO, 11:MOBILE_NUMBER, 12:AGE, 13:GENDER, 27:DISTRICT, 28:PIN_CODE
            
            epic_no = r[10]
            if not epic_no: continue
            
            doc = {
                "EPIC_NO": epic_no,
                "VOTER_NAME": r[7],
                "ASSEMBLY_NO": r[1],
                "AC_NO": r[1],
                "ASSEMBLY_NAME": r[2],
                "PART_NO": r[3],
                "SECTION_NO": r[4],
                "SLNOINPART": r[5],
                "HOUSE_NO": r[6],
                "C_HOUSE_NO": r[6],
                "RLN_TYPE": r[8],
                "RLN_FM_NM_EN": r[9],
                "RELATION_NAME": r[9],
                "MOBILE_NO": r[11],
                "AGE": r[12],
                "GENDER": r[13],
                "DISTRICT_NAME": r[27],
                "DISTRICT": r[27],
                "PIN_CODE": r[28]
            }
            
            # Using update_one with upsert to avoid blocking on duplicates
            batch.append(UpdateOne(
                {"EPIC_NO": epic_no},
                {"$set": doc},
                upsert=True
            ))
            
            if len(batch) >= 1000:
                try:
                    collection.bulk_write(batch, ordered=False)
                    count += len(batch)
                    if count % 5000 == 0:
                        print(f"Imported {count} records...")
                except Exception as e:
                    print(f"Error in bulk write: {e}")
                batch = []
        
        if batch:
            collection.bulk_write(batch, ordered=False)
            count += len(batch)
    
    print(f"Finished {filepath}. Total records: {count}")

if __name__ == "__main__":
    files = [
        r"c:\Users\Admin\OneDrive\Desktop\New folder (2)\Idgenerator\data\assembly_test\ass_16_Egmore.sql",
        r"c:\Users\Admin\OneDrive\Desktop\New folder (2)\Idgenerator\data\assembly_test\ass_17_Royapuram.sql"
    ]
    
    for f in files:
        if os.path.exists(f):
            import_sql_file(f)
        else:
            print(f"File not found: {f}")
    
    # Create index for EPIC_NO if not exists
    print("Ensuring indexes...")
    collection.create_index("EPIC_NO", unique=True)
    collection.create_index("ASSEMBLY_NAME")
    
    print("Migration complete!")
