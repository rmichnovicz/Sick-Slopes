**Sick Slopes!**
============
Sick Slopes is a web app for finding the routes in an area to achieve the highest possible velocity without powered acceleration, such as in longboarding, skateboarding, or biking. This app was designed in mind the goal of with finding the sickest slopes for longboarding. Currently, this app supports the continental United States.

Quick Start for Locally Hosting
-------------------------------
Instructions are written for Ubuntu Linux, but I imagine they should work on other Debian-compatible distros and should be similar for other OSs. Hit me up if you can write instructions for other OSs! For Windows, I think GDAL comes with OSGeo4W.

**Download Dependencies**

    sudo add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update
    sudo apt-get install gdal-bin
    sudo apt install python3-pip
    pip3 install --upgrade pip
    pip3 install osmapi numpy scipy matplotlib ipython jupyter pandas sympy nose

I don't know if you need the stuff after numpy, it was just on their website.

**Download Map Data**

Change the numbers in the file name to the ceiling of the coordinates you need (eg. N 33.7 W 84.4 -> n34w085)

    wget https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/ArcGrid/n34w085.zip
    unzip n34w085.zip
    rm n34w085.zip

How It works
------------

We're still working on that.

Version History
---------------
2016-11-4 - Project began at UGA Hacks II

