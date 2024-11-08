import urllib.request
import json
import csv
from datetime import datetime

filename = "air_quality.json"
csv_file = "air_quality.csv"
main_data = json.load(open(filename, "r", encoding="utf-8"))
ind = 0
count = 0
def main():
    global ind, count
    req = urllib.request.Request(
        url="http://api.openweathermap.org/data/2.5/air_pollution/history?lat=9.6970387&lon=-75.61609832592933&start=946684800&end=1730419200&appid=a1888882ca11f1450c414922db737dfe",
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"  # noqa
        },
    )
    with urllib.request.urlopen(req) as f:
        content = str(f.read().decode())

        data = json.loads(content)

        for pm2_5 in main_data:
            for dt in data['list']:
                if datetime.fromtimestamp(dt["dt"]).strftime('%d/%m/%Y')==pm2_5['datetime']:
                    count += float(dt['components'].get("pm2_5","0"))
                    ind += 1
                    break
            if(ind!=0):
                pm2_5['pm2.5'] = float(count/ind)
                count = 0
                ind = 0
            else:
                pm2_5['pm2.5'] = 0
            
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f,fieldnames=["datetime","T","TM","Tm","H","PP","VV","V","VM","pm2.5"])
        writer.writeheader()
        for row in main_data:
            writer.writerow(row)

    
main()