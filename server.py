# We need to import request to access the details of the POST request
# and render_template, to render our templates (form and response)
# we'll use url_for to get some URLs for the app on the templates
from flask import Flask, render_template, request, url_for
app = Flask(__name__)

# Define a route for the default URL, which loads the form
@app.route('/', methods=['GET'])
def show_map():
    return render_template('index.htm')

# Define a route for the action of the form, for example '/hello/'
# We are also defining which type of requests this route is
# accepting: POST requests in this case
@app.route('/send_square/', methods=['POST'])
def respond():
    box = request.get_json()
    return str(request.is_json)

# Run the app :)
if __name__ == '__main__':
  app.run(
        host="0.0.0.0",
        port=int("80")
  )


