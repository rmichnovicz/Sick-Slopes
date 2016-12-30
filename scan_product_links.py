import pickle
import csv
import sys
import re

def urls(file):
    urls = dict()
    regex = re.compile(r'[ns]\d\d[ew]\d\d\d') # ex n32w090
    with open(file, newline='') as csvfile:
        next(csvfile) # skip first line of headers
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            results = regex.findall(row[11]) if len(row) >= 11 else []
            if len(results) > 0:
                coords = results[0]
                ns = 1 if coords[0] == 'n' else -1
                ew = 1 if coords[3] == 'e' else -1
                urls[ns * (int(coords[1:3]), ew * int(coords[4:]))] = row[7]
                print(ns * (int(coords[1:3]), ew * int(coords[4:])), ": ", row[7])
    return urls
# if __name__ == "__main__":
#     with open("us_urls.pickle", "wb") as file:
#         pickle.dump(urls("elevationproductslinks/13secondplots.csv"), file, protocol=4)
#     with open("mx_ca_urls.pickle", "wb") as file:
#         pickle.dump(urls("elevationproductslinks/1secondplots.csv"), file, protocol=4)