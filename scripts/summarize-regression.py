import argparse,csv,statistics
from collections import defaultdict
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();groups=defaultdict(list)
for path in a.directory.glob('*-results.csv'):
    for row in csv.DictReader(path.open(encoding='utf-8-sig')):groups[(row['label'],row['map'],row['scenario'])].append(row)
for key,rows in sorted(groups.items()):
    good=[float(r['seconds']) for r in rows if r['result']=='pass']
    print(*key,'runs='+str(len(rows)),'failures='+str(len(rows)-len(good)),'median_seconds='+str(round(statistics.median(good),3) if good else 'NA'),sep=' | ')
for path in a.directory.glob('*-memory.csv'):
    rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
    for name in sorted({r['name'] for r in rows}):
        values=[int(r['private_bytes']) for r in rows if r['name']==name]
        print(path.name,name,'peak_private_MiB='+str(round(max(values)/1048576,2)))
