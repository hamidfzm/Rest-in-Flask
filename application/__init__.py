# python imports
import os
# flask imports
from flask import Flask, jsonify
# project imports
from config import DefaultConfig


def configure_app(app, configuration):
    app.config.from_object(DefaultConfig)

    if configuration is not None:
        app.config.from_object(configuration)

    app.config.from_pyfile('environ.py', silent=True)


def configure_folders(app):
    for key, value in app.config.items():
        if key.endswith('DIR'):
            if not os.path.exists(value):
                os.makedirs(value)
                app.logger.info("{} created at {}".format(key, value))


def configure_controllers(app):
    controllers = app.config['CONTROLLERS']
    for controller in controllers:
        bp = __import__('application.controllers.%s' % controller, fromlist=[controller])

        for route in bp.__all__:
            route_obj = getattr(bp, route)
            app.register_blueprint(route_obj)


def configure_errorhandlers(app):
    # python imports
    # flask imports
    from flask.ext.jsonschema import ValidationError as JsonValidationError

    # from application.extensions import bug_report

    def not_found(error):
        """
        @apiDefine NotFound
        @apiError (Error 404) NotFound The server has not found anything matching the Request-URI. No indication is given of whether the condition is
        temporary or permanent. The 410 (Gone) status code SHOULD be used if the server knows, through some internally configurable mechanism, that
        an old resource is permanently unavailable and has no forwarding address. This status code is commonly used when the server does not wish to
        reveal exactly why the request has been refused, or when no other response is applicable.
        """
        return (jsonify(error=error.message), 404) if app.config['DEBUG'] else (jsonify(), 404)

    app.register_error_handler(404, not_found)

    def bad_request(error):
        """
        @apiDefine BadRequest
        @apiError (Error 400) BadRequest The request could not be understood by the server due to malformed syntax. The client SHOULD NOT repeat the
        request without modifications.
        """
        return (jsonify(error=error.message), 400) if app.config['DEBUG'] else (jsonify(), 400)

    app.register_error_handler(JsonValidationError, bad_request)

    @app.errorhandler(403)
    def forbidden(error):
        """
        @apiDefine Forbidden
        @apiError (Error 400) Forbidden The server understood the request, but is refusing to fulfill it. Authorization will not help and the request
        SHOULD NOT be repeated. If the request method was not HEAD and the server wishes to make public why the request has not been fulfilled, it
        SHOULD describe the reason for the refusal in the entity. If the server does not wish to make this information available to the client, the
        status code 404 (Not Found) can be used instead.
        """
        return (jsonify(error=error.message), 403) if app.config['DEBUG'] else (jsonify(), 403)

    @app.errorhandler(401)
    def unauthorized(error):
        """
        @apiDefine Unauthorized
        @apiError (Error 401) Unauthorized The request requires user authentication. The response MUST include a WWW-Authenticate header field (
        section 14.47) containing a challenge applicable to the requested resource. The client MAY repeat the request with a suitable Authorization
        header field(section 14.8). If the request already included Authorization credentials, then the 401 response indicates that authorization has
        been refused for those credentials. If the 401 response contains the same challenge as the prior response, and the user agent has already
        attempted authentication at least once, then the user SHOULD be presented the entity that was given in the response, since that entity
        might include relevant diagnostic information. HTTP access authentication is explained in "HTTP Authentication: Basic and Digest Access
        Authentication"
        """
        return (jsonify(error=error.message), 401) if app.config['DEBUG'] else (jsonify(), 401)

    @app.errorhandler(485)
    def national_code_not_validate(error):
        """
        @apiDefine NationalCodeNotValidate
        @apiError (Error 485) This error occurs when users national code is not validate.
        """
        return (jsonify(error=error.message), 485) if app.config['DEBUG'] else (jsonify(), 485)

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(error)
        return "", 500

    @app.errorhandler(418)
    def full_capacity(error):
        """
        @apiDefine FullCapacity
        @apiError (Error 418) This error occurs when capacity of a model in database is full according to the game logic
        and user is not allowed to add new object
        """
        return (jsonify(error=error.message), 418) if app.config['DEBUG'] else (jsonify(), 418)

    @app.errorhandler(419)
    def datatime(error):
        """
        @apiDefine LeagueHasBeenStarted
        @apiError (Error 419) This error occurs when league bas been started.
        """
        return (jsonify(error=error.message), 419) if app.config['DEBUG'] else (jsonify(), 419)

    @app.errorhandler(420)
    def datatime(error):
        """
        @apiDefine LeagueHasStarted
        @apiError (Error 420) This error occurs when league has not been started.
        """
        return (jsonify(error=error.message), 420) if app.config['DEBUG'] else (jsonify(), 420)

    @app.errorhandler(425)
    def notenoughmoney(error):
        """
        @apiDefine NotEnoughMoney
        @apiError (Error 425) This error occurs when team credit get lower than player price.
        """
        return (jsonify(error=error.message), 425) if app.config['DEBUG'] else (jsonify(), 425)

    @app.errorhandler(426)
    def playerpost(error):
        """
        @apiDefine InvalidPost
        @apiError (Error 426) This error occurs when player post is invalid .
        """
        return (jsonify(error=error.message), 426) if app.config['DEBUG'] else (jsonify(), 426)

    @app.errorhandler(427)
    def formationerror(error):
        """
        @apiDefine InvalidFormation
        @apiError (Error 427) This error occurs when team formation is invalid or out players get more than 4.
        """
        return (jsonify(error=error.message), 427) if app.config['DEBUG'] else (jsonify(), 427)


def configure_extensions(app):
    import application.extensions as ex
    from application.extensions import redis
    from application.extensions import migrate, db

    for extension in app.config['EXTENSIONS']:
        try:
            getattr(ex, extension).init_app(app)
        except (AttributeError, TypeError):
            pass
    redis.init_app(app, strict=True)
    migrate.init_app(app, db)


def configure_media(app):
    from flask import send_from_directory

    @app.route('/media/<path:filename>')
    def media(filename):
        return send_from_directory(app.config['MEDIA_DIR'], filename)


def configure_admin(app):
    from application.admin import (AdminModelView)

    from application.extensions import admin, db

    pass


def configure_event_listeners(app):
    pass


def create_app(configuration):
    app = Flask(__name__)

    configure_app(app, configuration)
    configure_folders(app)
    configure_media(app)
    configure_errorhandlers(app)
    configure_admin(app)
    configure_extensions(app)
    configure_controllers(app)
    configure_event_listeners(app)

    return app
