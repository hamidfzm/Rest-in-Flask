# flask imports
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.cache import Cache
from flask.ext.jsonschema import JsonSchema
from flask.ext.redis import FlaskRedis
from flask.ext.cors import CORS
from flask.ext.admin import Admin
from flask.ext.elasticsearch import FlaskElasticsearch
from flask.ext.log import Logging
from flask.ext.migrate import Migrate

# project imports
# from application.modules.bug_report import BugReport

db = SQLAlchemy()
cache = Cache()
json = JsonSchema()
redis = FlaskRedis()
# bug_report = BugReport()
cors = CORS()
admin = Admin(template_mode='bootstrap3', url='/admin')
es = FlaskElasticsearch()
log = Logging()
migrate = Migrate()
