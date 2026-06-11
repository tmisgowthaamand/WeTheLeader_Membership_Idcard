with open(r"c:\Users\Admin\OneDrive\Desktop\New folder (2)\Idgenerator\data\assembly_test\ass_16_Egmore.sql", 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'INSERT INTO' in line.upper():
            print(f"Line {i+1} starts with: {repr(line[:50])}")
            if i > 70: break
