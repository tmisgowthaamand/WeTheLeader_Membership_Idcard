"""
Import ass_17_Royapuram.sql into MongoDB voters collection.
Uses upsert on EPIC_NO to avoid any duplicates.
Column order from SQL (same as Egmore):
  0:ID, 1:ASSEMBLY_NO, 2:ASSEMBLY_NAME, 3:PART_NO, 4:SECTION_NO,
  5:SERIAL_NO, 6:HOUSE_NO, 7:VOTER_NAME, 8:RELATION_TYPE, 9:RELATION_NAME,
  10:EPIC_NO, 11:MOBILE_NUMBER, 12:AGE, 13:GENDER, 14:PART_NAME,
  15:POLLING_STATION_NAME, 16:POLLING_STATION_ADDRESS, 17:MAIN_TOWN,
  18:WARD, 19:POST_OFFICE, 20:POLICE_STATION, 21:PANCHAYAT,
  22:BLOCK, 23:TEHSIL, 24:MANDAL, 25:REVENUE_DIVISION, 26:SUBDIVISION,
  27:DISTRICT, 28:PIN_CODE
"""

import csv
import io
import time
from pymongo import MongoClient, UpdateOne
import config

SQL_FILE = r"data/assembly_test/ass_17_Royapuram.sql"
BATCH_SIZE = 500

def clean(v):
    if v is None:
        return ""
    v = str(v).strip().strip("'\"")
    if v.upper() in ("NULL", "NONE"):
        return ""
    return v

def parse_row(row):
    if len(row) < 29:
        return None
    epic_no = clean(row[10])
    if not epic_no:
        return None
    return {
        "EPIC_NO":                   epic_no,
        "ASSEMBLY_NO":               clean(row[1]),
        "ASSEMBLY_NAME":             clean(row[2]),
        "PART_NO":                   clean(row[3]),
        "SECTION_NO":                clean(row[4]),
        "SLNOINPART":                clean(row[5]),
        "HOUSE_NO":                  clean(row[6]),
        "VOTER_NAME":                clean(row[7]),
        "FM_NAME_EN":                clean(row[7]),
        "RELATION_TYPE":             clean(row[8]),
        "RLN_TYPE":                  clean(row[8]),
        "RELATION_NAME":             clean(row[9]),
        "RLN_FM_NM_EN":              clean(row[9]),
        "MOBILE_NO":                 clean(row[11]),
        "AGE":                       clean(row[12]),
        "GENDER":                    clean(row[13]),
        "PART_NAME":                 clean(row[14]),
        "POLLING_STATION_NAME":      clean(row[15]),
        "POLLING_STATION_ADDRESS":   clean(row[16]),
        "MAIN_TOWN":                 clean(row[17]),
        "WARD":                      clean(row[18]),
        "POST_OFFICE":               clean(row[19]),
        "POLICE_STATION":            clean(row[20]),
        "PANCHAYAT":                 clean(row[21]),
        "BLOCK":                     clean(row[22]),
        "TEHSIL":                    clean(row[23]),
        "MANDAL":                    clean(row[24]),
        "REVENUE_DIVISION":          clean(row[25]),
        "SUBDIVISION":               clean(row[26]),
        "DISTRICT":                  clean(row[27]),
        "DISTRICT_NAME":             clean(row[27]),
        "PIN_CODE":                  clean(row[28]),
    }

def extract_rows_from_values(values_str):
    docs = []
    values_str = values_str.strip().rstrip(';').strip()
    i = 0
    n = len(values_str)
    while i < n:
        if values_str[i] == '(':
            depth = 0
            in_quote = False
            quote_char = None
            j = i
            while j < n:
                c = values_str[j]
                if in_quote:
                    if c == '\\':
                        j += 2
                        continue
                    if c == quote_char:
                        in_quote = False
                elif c in ("'", '"'):
                    in_quote = True
                    quote_char = c
                elif c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            inner = values_str[i+1:j]
            f = io.StringIO(inner)
            reader = csv.reader(f, quotechar="'", skipinitialspace=True, escapechar='\\')
            try:
                for row in reader:
                    doc = parse_row(row)
                    if doc:
                        docs.append(doc)
            except Exception:
                pass
            i = j + 1
        else:
            i += 1
    return docs

def run_import():
    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=30000)
    db = client[config.MONGO_DB]
    collection = db.voters

    before_count = collection.count_documents({"ASSEMBLY_NO": "17"})
    print(f"Before import — Royapuram (17) records in MongoDB: {before_count}")

    total_parsed   = 0
    total_upserted = 0
    total_matched  = 0
    ops_batch      = []

    start = time.time()
    current_insert = []
    in_insert = False

    print(f"Reading {SQL_FILE} ...")

    with open(SQL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            l = line.strip()
            if not l:
                continue

            upper = l.upper()

            if upper.startswith('INSERT INTO'):
                if current_insert:
                    block = ' '.join(current_insert)
                    vi = block.upper().find('VALUES')
                    if vi != -1:
                        docs = extract_rows_from_values(block[vi + 6:])
                        for doc in docs:
                            total_parsed += 1
                            ops_batch.append(
                                UpdateOne({"EPIC_NO": doc["EPIC_NO"]}, {"$set": doc}, upsert=True)
                            )
                    current_insert = []
                current_insert = [l]
                in_insert = True

            elif in_insert:
                current_insert.append(l)
                if l.endswith(';'):
                    block = ' '.join(current_insert)
                    vi = block.upper().find('VALUES')
                    if vi != -1:
                        docs = extract_rows_from_values(block[vi + 6:])
                        for doc in docs:
                            total_parsed += 1
                            ops_batch.append(
                                UpdateOne({"EPIC_NO": doc["EPIC_NO"]}, {"$set": doc}, upsert=True)
                            )
                    current_insert = []
                    in_insert = False

            if len(ops_batch) >= BATCH_SIZE:
                result = collection.bulk_write(ops_batch, ordered=False)
                total_upserted += result.upserted_count
                total_matched  += result.matched_count
                ops_batch = []
                elapsed = time.time() - start
                print(f"  Parsed: {total_parsed:,} | New: {total_upserted:,} | Updated: {total_matched:,} | {elapsed:.1f}s")

    # Flush remaining block
    if current_insert:
        block = ' '.join(current_insert)
        vi = block.upper().find('VALUES')
        if vi != -1:
            docs = extract_rows_from_values(block[vi + 6:])
            for doc in docs:
                total_parsed += 1
                ops_batch.append(
                    UpdateOne({"EPIC_NO": doc["EPIC_NO"]}, {"$set": doc}, upsert=True)
                )

    # Final batch flush
    if ops_batch:
        result = collection.bulk_write(ops_batch, ordered=False)
        total_upserted += result.upserted_count
        total_matched  += result.matched_count

    elapsed = time.time() - start
    after_count = collection.count_documents({"ASSEMBLY_NO": "17"})

    print()
    print("=" * 50)
    print(f"Import complete in {elapsed:.1f}s")
    print(f"Total rows parsed from SQL : {total_parsed:,}")
    print(f"New records inserted        : {total_upserted:,}")
    print(f"Existing records updated    : {total_matched:,}")
    print(f"Royapuram (17) in MongoDB  : {after_count:,}")
    print("=" * 50)

if __name__ == "__main__":
    run_import()
