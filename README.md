##vivo-static

This repository contains code for a presentation at the [2016 VIVO conference](http://www.vivoconference.org/).

Deploying VIVO as A Static Site

Presenters: Ted Lawless, Alexandre Rademaker and Fabricio Chalub


### Install & Configure

A running VIVO instance is required and access to the VIVO SPARQL API.

The static app requires Python 2.7 (make work with 3.x but not tested) and the Python packaging tool pip.

####Install the web app

* `git clone https://github.com/lawlesst/vivo-static.git`

* `cd vivo-static/web`

* `pip install -r requirements.txt`

* `cp .sample-env .env`

* Adjust values in .env to match your VIVO instance. This means setting the VIVO URL, username, password, and data namespace. This file is used to set environment variables that allows vivo-static to connect to VIVO.

* `source .env`

* `python app.py`

* visit [http://localhost:5000](http://localhost:5000) in your browser

* at this point you should be seeing the working vivo-static application

#### Generating the static site

vivo-static uses a tools called Frozen-Flask to genrate the HTML and CSS necessary for hosting the app as a static site. 

To generate the static site, from within the "web" directory run `python freeze.py`. This will create a `build` directory of the static assets for the site. Depending on the amount of data you have loaded into VIVO, this could take a while. 

To test your sample site, `cd build` and run `python -m SimpleHTTPServer 8000` to simulate hosting a static site. 


### Application details