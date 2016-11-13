# We need to import request to access the details of the POST request
# and render_template, to render our templates (form and response)
# we'll use url_for to get some URLs for the app on the templates
from flask import Flask, render_template, request, url_for
import json
from multiprocessing import Process
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
    hill_finder = Process(target=find_hills, args=(
        data['west'], data['south'], data['east'], data['north']
    ))
    hill_finder.daemon = True
    hill_finder.start()
    return str(request.is_json)



# Run the app :)
if __name__ == '__main__':
  app.run(
        host="0.0.0.0",
        port=int("80")
  )


