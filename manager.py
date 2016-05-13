#!/usr/bin/env python
# -*- coding: utf-8 -*-
# find . -name "*.pyc" -exec rm -rf {} \;

# python imports
import re
from scrapy import cmdline
from sys import argv
# flask imports
from flask.ext.script import Manager
from flask.ext.migrate import MigrateCommand

# project imports
from application import create_app
from application.config import DevelopmentConfig
from database import manager as database_manager

app = create_app(DevelopmentConfig)
manager = Manager(app)

manager.add_command('database', database_manager)
manager.add_command('migration', MigrateCommand)


@manager.command
def run():
    """
    Run server on port 5000 and domain name rishe.me.local
    """
    app.run(host='0.0.0.0', port=8080, debug=True)


@manager.command
def routes():
    """
    Get all application http routes
    """
    import urllib

    output = [urllib.unquote("\033[1m{:50s} {:20s} {}\033[0;0m".format('Endpoint', 'Methods', 'Rule'))]
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, rule))
        output.append(line)

    for line in sorted(output):
        print(line)


@manager.command
def jsons():
    """
    Generate json files from Json classes
    """

    # python imports
    from json import dump
    import os

    # project imports
    from application import jsons

    location = os.path.join(app.root_path, 'jsonschema')

    if not os.path.exists(location):
        os.makedirs(location)

    uncamelize = lambda camel: re.sub('(.)([A-Z]{1})', r'\1_\2', camel).lower()

    for json in jsons.__all__:
        with open(os.path.join(location, '%s.json' % uncamelize(json)), 'w') as f:
            dump(getattr(jsons, json).get_schema(ordered=True), f)


@manager.command
def doc():
    """
    Generate documentation files
    """
    import subprocess
    subprocess.call("apidoc -i . -o ../doc/", shell=True)

