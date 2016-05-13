# -*- coding: utf-8 -*-

# python imports
# flask imports
from flask.ext.script import Manager, prompt_bool

# project imports
from application.extensions import db, redis, es

manager = Manager(usage="Perform database operations")


@manager.command
def drop():
    """Drops database tables"""
    if prompt_bool("Are you sure you want to lose all your data"):
        db.drop_all()
        redis.flushdb()


@manager.command
def create():
    """Creates database tables from sqlalchemy models"""
    db.create_all()


@manager.command
def recreate():
    """
    Recreates database tables (same as issuing 'drop' and then 'create')
    """
    drop()
    create()


@manager.command
def update():
    es.indices.delete(index='example', ignore=[400, 404])

    body = {
        "settings": {
            "index": {"max_result_window": 500000},
            "analysis": {
                "char_filter": {
                    "zero_width_spaces": {
                        "type": "mapping",
                        "mappings": ["\\u200C=> "]
                    }
                },
                "filter": {
                    "nGram_filter": {
                        "type": "nGram",
                        "min_gram": 2,
                        "max_gram": 50,
                        "token_chars": [
                            "letter",
                            "digit",
                            "punctuation",
                            "symbol"]
                    },
                    "persian_stop": {
                        "type": "stop",
                        "stopwords": "_persian_"
                    }

                },
                "analyzer": {
                    "nGram_analyzer": {
                        "type": "custom",
                        "tokenizer": "whitespace",
                        "filter": [
                            "lowercase",
                            "asciifolding",
                            "arabic_normalization",
                            "persian_normalization",
                            "persian_stop",
                            "nGram_filter"
                        ]
                    },
                    "whitespace_analyzer": {
                        "type": "custom",
                        "tokenizer": "whitespace",
                        "filter": [
                            "lowercase",
                            "asciifolding",
                            "arabic_normalization",
                            "persian_normalization",
                            "persian_stop"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "player": {
                "_all": {
                    "analyzer": "nGram_analyzer",
                    "search_analyzer": "whitespace_analyzer"
                },
                "properties": {
                    "id": {
                        "type": "integer",
                        "index": "no",
                        "include_in_all": False
                    },
                    "name_fa": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "name_en": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "post": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "price": {
                        "type": "double",
                        "include_in_all": False
                    },
                    "team": {
                        "type": "string",
                        "index": "not_analyzed",
                    }
                }
            }
        }
    }

    es.indices.create(index='example', body=body)


@manager.command
def fake():
    """
    Generate fake data for database
    """
    pass


@manager.command
def developer():
    """
    Generate fake user for development use
    """
    pass


@manager.command
def populate():
    pass


@manager.command
def test():
    """Use it for test purpose"""
    pass
