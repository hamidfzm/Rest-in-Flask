# -*- coding: utf-8 -*-

# python imports
import os


class DefaultConfig(object):
    DEBUG = True
    DEPLOYMENT = False

    SECRET_KEY = 'developers@rishe.me'
    SITE_NAME = 'http://example.com'

    WTF_CSRF_ENABLED = False
    CSRF_ENABLED = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'

    # Blueprint need to be installed entered here
    CONTROLLERS = (
        'main',
        'user',
        'player',
        'league',
        'team',
        'fantasy_league',
        'fantasy_team'
    )

    API_VERSION = 1

    PAGE_SIZE = 10

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

    MEDIA_DIR = os.environ.get('MEDIA_DIR', '/tmp/media/')
    AVATAR_DIR = os.path.join(MEDIA_DIR, 'avatar')

    CACHE_NO_NULL_WARNING = True
    CACHE_TYPE = 'null'
    CACHE_DEFAULT_TIMEOUT = 3600
    CACHE_DIR = os.environ.get('CACHE_DIR', '/tmp/cache/')

    REDIS_URL = "redis://localhost:6379/0"
    ELASTICSEARCH_HOST = "localhost:9200"

    ACTIVATION_CODE_TIMEOUT = 60 * 10  # 10 minutes
    ACCESS_TOKEN_TIMEOUT = 60 * 60  # 60 minutes

    # TODO not a good option because it allow CORS attack so use credentials in future
    CORS_RESOURCES = {r"/api/*": {"origins": "*"}}
    EXTENSIONS = ['db', 'cache', 'json', 'es', 'sms', 'cors', 'admin', 'es']


class DeploymentConfig(DefaultConfig):
    DEBUG = False
    TESTING = False
    DEPLOYMENT = True
    CACHE_TYPE = 'filesystem'
    FANTASY_LEAGUE_START = True


class DevelopmentConfig(DefaultConfig):
    DEBUG = True


class TestingConfig(DefaultConfig):
    DEBUG = False
    TESTING = True
    DEPLOYMENT = True
    CACHE_TYPE = 'null'
