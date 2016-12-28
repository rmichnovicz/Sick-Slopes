**Sick Slopes!**
============
Sick Slopes is a web app for finding routes to reach high velocities in unpowered vehicles such as longboards or bikes. Currently, this app supports the continental United States.

Quick Start for Locally Hosting
-------------------------------
Instructions are written for Ubuntu Linux, but I imagine they should work on other Debian-compatible distros and should be similar for other OSs. Hit me up if you can write instructions for other OSs! For Windows, I think GDAL comes with OSGeo4W.

**Download Dependencies**

    sudo add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update
    sudo apt-get install gdal-bin
    sudo apt install python3-pip
    pip3 install --upgrade pip
    pip3 install osmapi wget numpy scipy matplotlib ipython jupyter pandas sympy nose

I don't know if you need the stuff after numpy, it was just on their website.

**Download Map Data**

The command is followed by the latitude and longitude of the coordinate area you
need to download. It downloads a 1 degree by 1 degree block of coordinate data
at the resolution of 1/3 by 1/3 arc-seconds. The block is named by the northwest
corner of the coordinates. The default area selected upon opening index.htm is
contained in the N 34 W 85 block. The following commands are equivilent.

    python3 download_elevation_data.py 34 85
    python3 download_elevation_data.py 34 -085
    python3 download_elevation_data.py 33.4543423 84.32465878

How It works
------------

We're still working on that.

Version History
---------------
2016-11-4 - Project began at UGA Hacks II

