# -*- coding: utf-8 -*-


# flask imports
from flask import Blueprint, jsonify

# project imports

__author__ = 'Hamid FzM'

__all__ = ['web', 'api1']

web = Blueprint('main.web', __name__, url_prefix='')
api1 = Blueprint('main.api1', __name__, url_prefix='/api/v1')


@web.route('/')
def index():
    return "REST in Flask Index Page"


@api1.route('')
def status():
    """
    @apiVersion 1.0.0
    @apiGroup Main
    @apiName Status
    @apiDescription Show API V1 status information
    @api {get} /v1 API V1 Status
    @apiHeader {String} Content-Type =application/json JSON (application/json)

    @apiSuccess {Number} version API version
    @apiSuccess {String} status API status
    """

    # OK or Deprecate api
    return jsonify(version=1, status="OK"), 200

