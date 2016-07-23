import json
import string

import werkzeug
import flask
from flask import Flask, request
from flask import render_template
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
Bootstrap(app)

#AZ = string.lowercase
#AZ_GROUPS = [AZ[i:i+3] for i in xrange(0, 26, 3)]

import backend

@app.route("/")
def index():
    people = backend.get_people()
    return render_template(
        'index.html',
        people=people,
        #groups=AZ_GROUPS
    )

@app.route("/person/<pid>.html")
def person(pid):
    return render_template(
        'person.html',
        details=backend.get_person(pid),
        publications=backend.get_pubs(pid)
    )


if __name__ == "__main__":
    app.run(debug=True)
