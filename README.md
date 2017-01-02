**Sick Slopes!**
============
Sick Slopes is a web app for finding routes to reach high velocities in unpowered vehicles such as longboards or bikes. Currently, this app supports the continental United States.

Quick Start for Locally Hosting
-------------------------------
Instructions are written for Ubuntu Linux, but I imagine they should work on other Debian-compatible distros and should be similar for other OSs. Hit me up if you can write instructions for other OSs! For Windows, I think GDAL comes with OSGeo4W.

**Download Dependencies**

    sudo add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update
    sudo apt-get install gdal-bin
    sudo apt-get install python3-gdal
    sudo apt-get install python3-pip
    pip3 install --upgrade pip
    sudo pip3 install osmapi wget numpy scipy matplotlib ipython jupyter pandas sympy nose

I don't know if you need the stuff after numpy, it was just on their website.


How It works
------------

We're still working on that.

Version History
---------------
2016-11-4 - Project began at UGA Hacks II

