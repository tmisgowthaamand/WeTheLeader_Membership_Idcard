import os
import re
import csv
import io
from pymongo import MongoClient
from dotenv import load_dotenv
import config

load_dotenv()

def extract_docs_from_block(block):
    # block is the string containing (...) , (...) ;
    # We find all (...)
    # Regex that respects quotes is better.
    # But let's try a simple scanner.
    
    records = []
    
    # We strip the "INSERT INTO ... VALUES" prefix if it exists in the block
    if 'VALUES' in block.upper():
        block = block[block.upper().find('VALUES') + 6:]
    
    # Clean ending semicolon
    block = block.strip().rstrip(';')
    
    # Find all balanced parentheses
    # Since it's a standard SQL dump, we can look for "),(" as a separator 
    # Or just find all ( ... )
    # Let's use a regex for (values, values)
    
    # We use a trick: find all patterns that look like (val1, val2, ...)
    # But values can contain commas.
    # However, phpMyAdmin usually formats them quite cleanly.
    
    raw_records = re.findall(r'\((.*?)\)(?:,|$|\n)', block, re.DOTALL)
    
    for r in raw_records:
        r = r.strip()
        if not r: continue
        
        # Use csv reader to handle quotes and escaping
        f = io.StringIO(r)
        reader = csv.reader(f, quotechar="'", skipinitialspace=True, escapechar='\\')
        try:
            for row in reader:
                if len(row) < 29: continue
                
                def clean(v):
                    if v is None: return ""
                    v = str(v).strip()
                    if v.upper() == "NULL": return ""
                    return v

                doc = {
                    "EPIC_NO":        clean(row[10]),
                    "VOTER_NAME":     clean(row[7]),
                    "FM_NAME_EN":     clean(row[7]), 
                    "RELATION_TYPE":  clean(row[8]),
                    "RELATION_NAME":  clean(row[9]),
                    "RLN_FM_NM_EN":   clean(row[9]),
                    "ASSEMBLY_NAME":  clean(row[2]),
                    "ASSEMBLY_NO":    clean(row[1]),
                    "DISTRICT_NAME":  clean(row[27]),
                    "MOBILE_NO":      clean(row[11]),
                    "PART_NO":        clean(row[3]),
                    "SECTION_NO":     clean(row[4]),
                    "SLNOINPART":     clean(row[5]),
                    "HOUSE_NO":       clean(row[6]),
                    "AGE":            clean(row[12]),
                    "GENDER":         clean(row[13]),
                    "PIN_CODE":       clean(row[28])
                }
                if doc["EPIC_NO"]:
                    records.append(doc)
        except:
            continue
    return records

def import_sql(file_path):
    client = MongoClient(config.MONGO_URI)
    db = client[config.MONGO_DB]
    collection = db.voters
    
    print(f"Opening {file_path}...")
    count = 0
    batch = []
    
    current_block = []
    in_insert = False
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            l_strip = line.strip()
            if not l_strip: continue
            
            if l_strip.upper().startswith('INSERT INTO'):
                # Process previous block if any
                if current_block:
                    recs = extract_docs_from_block(" ".join(current_block))
                    for r in recs:
                        batch.append(r)
                        count += 1
                        if len(batch) >= 1000:
                            collection.insert_many(batch, ordered=False)
                            batch = []
                            print(f"Imported {count} records...")
                
                current_block = [l_strip]
                in_insert = True
            elif in_insert:
                current_block.append(l_strip)
                if l_strip.endswith(';'):
                    recs = extract_docs_from_block(" ".join(current_block))
                    for r in recs:
                        batch.append(r)
                        count += 1
                        if len(batch) >= 1000:
                            try:
                                collection.insert_many(batch, ordered=False)
                            except:
                                for b in batch:
                                    b.pop('_id', None)
                                    collection.update_one({"EPIC_NO": b["EPIC_NO"]}, {"$set": b}, upsert=True)
                            batch = []
                            print(f"Imported {count} records...")
                    current_block = []
                    in_insert = False

    if batch:
        try:
            collection.insert_many(batch, ordered=False)
        except:
            for b in batch:
                b.pop('_id', None)
                collection.update_one({"EPIC_NO": b["EPIC_NO"]}, {"$set": b}, upsert=True)
    
    print(f"Done! Total imported: {count}")

if __name__ == "__main__":
    sql_path = r"c:\Users\Admin\OneDrive\Desktop\New folder (2)\Idgenerator\data\assembly_test\ass_16_Egmore.sql"
    if os.path.exists(sql_path):
        import_sql(sql_path)
