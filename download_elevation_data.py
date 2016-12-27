from sys import argv
from math import ceil
import wget
import urllib
import zipfile
import os

def download_elevation_data(lat, lng):
    download_one_third_second_data(lat, lng)
    # TODO: check country, download appropriate data

def download_one_third_second_data(lat, lng):

    ziphandle = ("n" + str(ceil(abs(lat))).zfill(2)
        + "w" + str(ceil(abs(lng))).zfill(3))

    url = ("https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/"
        + "ArcGrid/" + ziphandle + ".zip")

    try:
        wget.download(url)
    except (urllib.error.HTTPError):
        print("Data not available")


    archive = zipfile.ZipFile(ziphandle + ".zip")

    for file in archive.namelist():
        if file.startswith("grd" + ziphandle + "_13/"):
            archive.extract(file, "elevationdata")

    os.remove(ziphandle + ".zip")
    # with zipfile.ZipFile(tDir + mainapk[0]) as z:
    #     with open(os.path.join(tDir, os.path.basename(icon[1])), 'wb') as f:
    #         f.write(z.read(icon[1]))

if __name__ == "__main__":
    download_elevation_data(float(argv[1]), float(argv[2]))