"""
Flask app.

- defines routes
- calls backend to query VIVO store
- passes data to templates

"""

from flask import Flask
from flask import render_template, url_for
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.debug = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
Bootstrap(app)

# from flask.ext.profile import Profiler
# Profiler(app)

import backend

#http://flask.pocoo.org/snippets/40/
# This allows us to use urls that end with .html
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)
# end url config

@app.route("/")
def index():
    people = backend.get_people()
    return render_template(
        'index.html',
        people=people,
    )

@app.route("/person/<pid>.html")
def person(pid):
    person = backend.Profile(pid)
    print person.websites()
    return render_template(
        'person.html',
        person=person.profile(),
        websites=person.websites(),
        publications=person.publications(),
        positions=person.positions(),
        jsonld=person.schema_org(),
    )


if __name__ == "__main__":
    app.run()
