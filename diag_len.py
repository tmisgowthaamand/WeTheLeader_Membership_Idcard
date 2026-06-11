with open(r"c:\Users\Admin\OneDrive\Desktop\New folder (2)\Idgenerator\data\assembly_test\ass_16_Egmore.sql", 'r', encoding='utf-8', errors='ignore') as f:
    i = 0
    for line in f:
        i += 1
        if 'INSERT INTO' in line.upper():
            print(f"Line {i} length: {len(line)}")
        if i > 1000: break
