# -*- coding: utf-8 -*-

# python imports
from datetime import datetime
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from os import path, remove

# flask imports
from flask import Blueprint, request, jsonify, abort, g, current_app
from flask.ext.jsonschema import validate

# project imports
from application.extensions import db
from application.models.user import User
from application.forms.user import UploadAvatar

api1 = Blueprint('user.api1', __name__, url_prefix='/api/v1/user')


@api1.route('/authenticate', methods=['POST'])
@validate('authenticate')
def authenticate():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName Authenticate
    @apiDescription Authenticate an existing user or register a user using phone number.
    An activation code will be send to phone.
    @api {post} /v1/user/authenticate Authenticate an existing user or register a phone number
    @apiHeader {String} Content-Type =application/json JSON (application/json)

    @apiParam {String} phone Phone of the existing user.

    @apiSuccessExample Success-Response:
        HTTP/1.1 200 OK

    @apiSuccessExample Success-Response:
        HTTP/1.1 201 Created

    @apiUse BadRequest

    @apiSampleRequest http://example.com/api/v1/user/authenticate
    """
    phone = request.json['phone']

    try:
        user_obj = User.query.filter_by(phone=phone).one()
        user_obj.send_activation_code()

        return jsonify(), 200

    except NoResultFound:
        user_obj = User(phone=phone)
        db.session.add(user_obj)
        db.session.commit()
        user_obj.send_activation_code()

        return jsonify(), 201


@api1.route('/web_authenticate', methods=['POST'])
@validate('web_authenticate')
def web_authenticate():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName WebAuthenticate
    @apiDescription Authenticate user using password from web site
    @api {post} /v1/user/web_authenticate Authenticate using password
    @apiHeader {String} Content-Type =application/json JSON (application/json)

    @apiParam {String} phone Phone of the existing user.
    @apiParam {String} password Password that user set or the one which is sent by sms

    @apiSuccess {String} refresh Refresh token
    @apiSuccess {String} access Access token

    @apiUse BadRequest
    @apiUse Unauthorized
    @apiUse NotFound
    @apiError (Error 406) PasswordProblem User didn't set a password

    @apiSampleRequest http://example.com/api/v1/user/web_authenticate
    """
    json = request.json
    try:
        user_obj = User.query.filter_by(phone=json['phone']).one()

        # Warning!!! 1370 activation code is for developing purpose
        # TODO think about a solution to stop brute force and DDOS attacks using activation codes
        if not user_obj.has_password:
            return abort(406)

        # TODO save password using bycrypt not plain text in DB
        if user_obj.password == json['password']:
            access_token = user_obj.generate_access_token()

            token_obj = Token(user=user_obj, access=access_token, refresh=str(uuid4()))
            db.session.add(token_obj)
            db.session.commit()

            return jsonify(access=access_token, refresh=token_obj.refresh), 200

        return abort(401)
    except NoResultFound:
        return abort(404)


@api1.route('/activate', methods=['POST'])
@validate('activate')
def activate():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName Activate
    @apiDescription Generate access and refresh tokens using phone and code sent to phone number
    @api {post} /v1/user/activate Generate tokens
    @apiHeader {String} Content-Type =application/json JSON (application/json)

    @apiParam {String} phone Phone of the user.
    @apiParam {String} code Code sent to the user phone.

    @apiSuccess {String} refresh Refresh token
    @apiSuccess {String} access Access token

    @apiSuccessExample Success-Response:
        HTTP/1.1 200 OK

    @apiSuccessExample Success-Response:
        HTTP/1.1 201 Created

    @apiUse Unauthorized
    @apiUse NotFound
    @apiUse BadRequest

    @apiSampleRequest http://example.com/api/v1/user/activate
    """
    try:
        json = request.json
        user_obj = User.query.filter_by(phone=json['phone']).one()

        # Warning!!! 1370 activation code is for developing purpose
        # TODO think about a solution to stop brute force and DDOS attacks using activation codes
        if user_obj.consume_activation_code(json['code']) or json['code'] == '13740':
            access_token = user_obj.generate_access_token()

            token_obj = Token(user=user_obj, access=access_token, refresh=str(uuid4()))
            db.session.add(token_obj)
            db.session.commit()

            if user_obj.user_name is None or user_obj.user_name == "":
                return jsonify(access=access_token, refresh=token_obj.refresh), 201
            return jsonify(access=access_token, refresh=token_obj.refresh), 200

        return abort(401)
    except NoResultFound:
        return abort(404)


@api1.route('/refresh', methods=['POST'])
@validate('refresh')
def refresh():
    # TODO we can take last used access token in header and its better i think
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName Refresh
    @apiDescription Refresh access token using refresh token and last used access token
    @api {post} /v1/user/refresh Refresh access token
    @apiHeader {String} Content-Type =application/json JSON (application/json)

    @apiParam {String} refresh User refresh token
    @apiParam {String} access Last used access token

    @apiSuccess {String} access New access token

    @apiUse Unauthorized
    @apiUse NotFound
    @apiUse BadRequest

    @apiSampleRequest http://example.com/api/v1/user/refresh
    """

    json = request.json
    token_obj = Token.query.get(json['refresh'])
    if not token_obj:
        return abort(404)

    if token_obj.consume_access_code(json['access']):
        token_obj.last_refresh = datetime.utcnow()
        access_token = token_obj.user.generate_access_token()
        token_obj.access = access_token
        db.session.commit()

        return jsonify(access=access_token), 200

    return abort(401)


@api1.route('', methods=['GET'])
@User.authenticate()
def profile():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName CurrentUserProfile
    @apiDescription Get current user profile information
    @api {get} /v1/user Get private user profile
    @apiHeader {String} Content-Type =application/json JSON (application/json)
    @apiHeader {String} Access-Token User access token

    @apiSuccess {String} user_name User nick name
    @apiSuccess {String} real_name User real name
    @apiSuccess {String} phone User phone number
    @apiSuccess {String} coupon_count User coupon count
    @apiSuccess {String} national_code User personal id
    @apiSuccess {String} registered_at User register date time in yyyy-MM-dd HH:mm:ss format

    @apiUse Unauthorized
    @apiUse NotFound
    @apiUse BadRequest

    @apiSampleRequest http://example.com/api/v1/user
    """
    return jsonify(g.user.to_json()), 200


@api1.route('/<int:user_id>', methods=['GET'])
@User.authenticate()
def profile_other(user_id):
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName PublicUserProfile
    @apiDescription Get a user public profile information
    @api {get} /v1/user/:id Get public user profile
    @apiHeader {String} Content-Type =application/json JSON (application/json)
    @apiHeader {String} Access-Token User access token

    @apiParam {Integer} id Other user id

    @apiSuccess {String} user_name User user name

    @apiUse Unauthorized
    @apiUse NotFound
    @apiUse BadRequest

    @apiSampleRequest http://example.com/api/v1/user/:id
    """

    user_obj = User.query.get(user_id)
    if not user_obj:
        return abort(404)
    return jsonify(user_name=user_obj.user_name), 200


@api1.route('', methods=['PUT'])
@User.authenticate()
@validate('edit_info')
def edit_info():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName EditInfo
    @apiDescription Edit current user information
    @api {put} /v1/user Edit current user info
    @apiHeader {String} Content-Type =application/json JSON (application/json)
    @apiHeader {String} Access-Token User access token

    @apiParam {String} user_name User user name
    @apiParam {String} real_name User real name
    @apiParam {String} national_code User personal id

    @apiError (Error 409) IntegrityError name field is not unique
    @apiUse Unauthorized
    @apiUse BadRequest
    @apiUse NationalCodeNotValidate

    @apiSampleRequest http://example.com/api/v1/user
    """

    def national_code_validate(national_code):
        national_code_recursive = national_code[::-1]
        s = 0
        for idx, val in enumerate(national_code_recursive[1:]):
            s += int(val) * (idx + 2)
        r = s % 11
        if r >= 2:
            r = 11 - r
        if r == int(national_code[9]):
            return True
        return False

    try:
        if 'national_code' in request.json:
            if not national_code_validate(request.json['national_code']):
                return "national code not valid", 485
        g.user.populate(request.json)
        db.session.commit()
        return jsonify(), 200
    except IntegrityError, err:
        if "user_name" in str(err.orig):
            return "user_name already exists", 409

        elif "national_code" in str(err.orig):
            return "national_code already exists", 409
        else:
            return abort(409)


@api1.route('/password', methods=['POST'])
@User.authenticate()
@validate('create_password')
def create_password():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName CreatePassword
    @apiDescription Set password for user if it is not set
    @api {get} /v1/user Create password
    @apiHeader {String} Content-Type=application/json JSON (application/json)
    @apiHeader {String} Access-Token User access token

    @apiParam {String} new_password User new password

    @apiSuccessExample Success-Response:
        HTTP/1.1 201 Created

    @apiError (Error 406) PasswordProblem User already have a password
    @apiUse Unauthorized
    @apiUse BadRequest

    @apiSampleRequest http://example.com/api/v1/user/password
    """
    json = request.json
    if g.user.has_password():
        return abort(406)

    g.user.password = json['new_password']
    db.session.commit()

    return jsonify(), 201


@api1.route('/password', methods=['PUT'])
@User.authenticate()
@validate('edit_password')
def edit_password():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName EditPassword
    @apiDescription Edit user password if it is set
    @api {put} /v1/user/password Edit password
    @apiHeader {String} Content-Type =application/json JSON (application/json)
    @apiHeader {String} Access-Token User access token

    @apiParam {String} old_password User old password
    @apiParam {String} new_password User new password

    @apiSuccessExample Success-Response:
        HTTP/1.1 200 OK

    @apiError (Error 406) PasswordProblem Wrong old password or password is not set
    @apiUse Unauthorized
    @apiUse BadRequest

    @apiSampleRequest http://example.com/api/v1/user/password
    """
    json = request.json
    if g.user.password == json['old_password']:
        g.user.password = json['new_password']
        db.session.commit()
        return jsonify(), 200
    return abort(406)


@api1.route('/password', methods=['DELETE'])
@User.authenticate()
@validate('delete_password')
def delete_password():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName DeletePassword
    @apiDescription Delete user password if it is set
    @api {get} /v1/user Delete password
    @apiHeader {String} Content-Type =application/json JSON (application/json)
    @apiHeader {String} Access-Token User access token

    @apiParam {String} old_password User old password

    @apiSuccessExample Success-Response:
        HTTP/1.1 200 OK

    @apiError (Error 406) PasswordProblem Wrong old password
    @apiUse Unauthorized
    @apiUse BadRequest

    @apiSampleRequest http://example.com/api/v1/user/password
    """
    json = request.json
    if g.user.password == json['old_password']:
        g.user.password = None
        db.session.commit()
        return jsonify(), 200
    return abort(406)


@api1.route('/revoke', methods=['DELETE'])
@User.authenticate()
def revoke():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName Revoke
    @apiDescription Revoke current user access and refresh tokens
    @api {delete} /v1/user/revoke Revoke current authentication tokens
    @apiHeader {String} Content-Type =application/json JSON (application/json)
    @apiHeader {String} Access-Token User access token

    @apiSuccessExample Success-Response:
        HTTP/1.1 200 OK

    @apiUse Unauthorized

    @apiSampleRequest http://example.com/api/v1/user/revoke
    """
    Token.revoke(request.headers.get('Access-Token'))
    db.session.commit()
    return jsonify(), 200


@api1.route('/revoke_all', methods=['DELETE'])
@User.authenticate()
def revoke_all():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName RevokeAll
    @apiDescription Revoke all user tokens so all devices logged in with this device will be logged out
    @api {delete} /v1/user/revoke_all Revoke all authentication tokens
    @apiHeader {String} Content-Type =application/json JSON (application/json)
    @apiHeader {String} Access-Token User access token

    @apiSuccessExample Success-Response:
        HTTP/1.1 200 OK

    @apiUse Unauthorized

    @apiSampleRequest http://example.com/api/v1/user/revoke_all
    """
    Token.revoke_all(g.user)
    db.session.commit()
    return jsonify(), 200


@api1.route('/avatar', methods=['PUT'])
@User.authenticate()
def edit_avatar():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName EditAvatar
    @apiDescription Edit user profile information
    @api {put} /v1/user/avatar Edit user avatar
    @apiHeader {String} Content-Type =multipart/form-data form-data (multipart/form-data)
    @apiUse AccessTokenHeader

    @apiParam {File} file File content (only *.jpg supported for now)

    @apiSuccessExample Success-Response:
        HTTP/1.1 200 OK

    @apiUse Unauthorized
    @apiUse BadRequest
    """

    form = UploadAvatar()

    if form.validate():
        file_obj = form.file.data
        _, extension = path.splitext(file_obj.filename)
        filename = '%s%s' % (g.user.phone, extension)
        file_address = path.join(current_app.config['AVATAR_DIR'], filename)

        file_obj.save(file_address)

        return '', 200
    return jsonify(errors=form.errors), 400


@api1.route('/avatar', methods=['DELETE'])
@User.authenticate()
def delete_avatar():
    """
    @apiVersion 1.0.0
    @apiGroup User
    @apiName DeleteAvatar
    @apiDescription Delete user profile information
    @api {delete} /v1/user/avatar Delete user avatar
    @apiUse AccessTokenHeader

    @apiSuccessExample Success-Response:
        HTTP/1.1 200 OK

    @apiUse Unauthorized
    @apiUse NotFound
    """

    filename = '%s%s' % (g.user.phone, '.jpg')
    file_address = path.join(current_app.config['AVATAR_DIR'], filename)

    if path.isfile(file_address):
        remove(file_address)

        return '', 200
    return abort(404)
