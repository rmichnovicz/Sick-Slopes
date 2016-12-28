# We need to import request to access the details of the POST request
# and render_template, to render our templates (form and response)
# we'll use url_for to get some URLs for the app on the templates
from flask import Flask, render_template, request, url_for, jsonify, send_file
from multiprocessing import Process
from make_map import make_map

app = Flask(__name__)
# from hill_finder import find_hills
# dummy method: TODO remove
def find_hills(west, south, east, north):
    return True

# Define a route for the default URL, which loads the form
@app.route('/', methods=['GET'])
def show_home():
    return render_template('index.htm')

@app.route('/send_square/', methods=['POST'])
def respond():
    data = request.get_json(force=True)
    success, stoplights, local_maxima, graph, node_heights, node_latlons, \
        edge_heights = make_map((
            data['west'],
            data['south'],
            data['east'],
            data['north']
            ))
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

    # hill_finder = Process(target=find_hills, args=(
    #     data['west'], data['south'], data['east'], data['north']
    # ))
    # hill_finder.daemon = True
    # hill_finder.start()
    # return str(request.is_json)

@app.route("/get_json/")
def get_json():
    success, stoplights, local_maxima, graph, node_heights, node_latlons, \
        edge_heights = make_map()
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

# TODO Remove when implementing nginx
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


