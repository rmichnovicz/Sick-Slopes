# We need to import request to access the details of the POST request
# and render_template, to render our templates (form and response)
# we'll use url_for to get some URLs for the app on the templates
from flask import Flask, render_template, request, url_for, jsonify, send_file
from multiprocessing import Process
from make_map import make_map
import countries
# TODO Remove the following in production
from scan_product_links import urls
import os
from math import ceil
import wget
import urllib
import zipfile

app = Flask(__name__)
country_checker = countries.CountryChecker("TM_WORLD_BORDERS-0.3.shx")
# TODO Remove the following in production
us_urls = urls("elevationproductslinks/13secondplots.csv")
mx_ca_urls = urls("elevationproductslinks/1secondplots.csv")


# Define a route for the default URL, which loads the form
# TODO Remove the following route in production
@app.route('/', methods=['GET'])
def show_home():
    return render_template('index.htm')

@app.route('/send_square/', methods=['POST'])
def respond():
    data = request.get_json(force=True)
    # TODO check if request is gucci
    country = str(country_checker.getCountry(countries.Point(
        (data['north'] + data['south']) / 2 ,
        (data['east'] + data['west']) / 2
        )))
    print (data['east'], data['west'])

    # TODO Remove the following block of code in production
    # if country == 'United States':
    #     path_suffix = '_13'
    #     useful_urls = us_urls
    # else:
    #     path_suffix = '_1'
    #     useful_urls = mx_ca_urls
    # for lat in range(
    #     ceil(float(data['south'])), ceil(float(data['north'])) + 1
    #     # Eg N 87.7 to N 86.
    #     ):
    #     for lng in range(
    #         ceil(float(data['west'])), ceil(float(data['east'])) + 1
    #         ):
    #         fname = ('grd' + ('n' if lat>0 else 's')
    #             + str(math.ceil(abs(lat))).zfill(2)
    #             + ('e' if lng>0 else 'w')
    #             + str(math.ceil(abs(lng))).zfill(3))
    #         database_path = ('elevationdata/'
    #             + fname
    #             + path_suffix + '/w001001.adf'
    #             )
    #         if not os.path.exists(database_path):
    #             try:
    #                 wget.download(useful_urls[(lat, lng)])




    success, stoplights, local_maxima, graph, node_heights, node_latlons, \
        edge_heights = make_map((
            data['west'],
            data['south'],
            data['east'],
            data['north']
            ), country)
    if (success):
        return jsonify({
            "stoplights": stoplights,
            "local_maxima": local_maxima,
            "graph": graph,
            "node_heights": node_heights,
            "node_latlons": node_latlons,
            "edge_heights": edge_heights
            })
    return jsonify(False)

# @app.route("/get_json/")
# def get_json():
#     success, stoplights, local_maxima, graph, node_heights, node_latlons, \
#         edge_heights = make_map()
#     if (success):
#         return jsonify({
#             "stoplights": stoplights,
#             "local_maxima": local_maxima,
#             "graph": graph,
#             "node_heights": node_heights,
#             "node_latlons": node_latlons,
#             "edge_heights": edge_heights
#             })
#     return jsonify(False)

# TODO Remove the following 3 routes in production
@app.route("/favicon.ico")
def get_favicon():
    return send_file('favicon.ico')

@app.route("/findhills.js")
def get_js():
    return send_file('findhills.js')

@app.route("/style.css")
def get_css():
    return send_file('style.css')

# Run the app :)
if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int("80")
    )

