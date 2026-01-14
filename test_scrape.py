import re

for fname in ['contrib.html', 'contrib2024.html']:
    try:
        html = open(fname, encoding='utf-8').read()
        print(f"\n=== {fname} ===")
        
        # Pattern: data-date="YYYY-MM-DD" ... data-level="N"
        pattern = r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"'
        matches = re.findall(pattern, html)
        levels = {}
        for date, lvl in matches:
            levels[int(lvl)] = levels.get(int(lvl), 0) + 1
        print('Level counts:', levels)
        
        # Show date range
        if matches:
            dates = [m[0] for m in matches]
            print(f"Date range: {min(dates)} to {max(dates)}")
            
            non_zero = [(d, l) for d, l in matches if int(l) > 0][:5]
            print('Sample non-zero:', non_zero)
    except Exception as e:
        print(f"{fname}: {e}")
