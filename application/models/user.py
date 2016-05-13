# python imports
from datetime import datetime
from uuid import uuid4
from random import randint
from functools import wraps
from sqlalchemy_utils import PasswordType

# flask imports
from flask import current_app, request, abort, g

# project imports
from application.extensions import db, redis, sms


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    real_name = db.Column(db.Unicode(254), nullable=True)
    user_name = db.Column(db.Unicode(254), nullable=True, unique=True)
    phone = db.Column(db.String(11), nullable=False, unique=True)
    national_code = db.Column(db.String(10), nullable=True, unique=True)
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512', 'md5_crypt'], deprecated=['md5_crypt']), nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    registered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    coupon_count = db.Column(db.Integer, nullable=False, default=0)

    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'), nullable=True)

    tokens = db.relationship('Token', backref='user', lazy='dynamic', cascade='all,delete')
    fantasy_teams = db.relationship('FantasyTeam', backref='user', lazy='dynamic', cascade='all,delete')

    def has_password(self):
        return self.password is not None

    @classmethod
    def authenticate(cls, populate=True):
        """
        If user authenticated correctly then g.user value will be filled with user sql alchemy
        other wise it will abort request with 401 unauthorised http response code
        :param populate: if False user is user_id and if True user is user_obj from database. use populate=False for perfomance


        @apiDefine AccessTokenHeader
        @apiHeader {String} Access-Token =33c002af-0939-4c3d-89f4-d3ab7676d978 Access token given after registering, activation and refreshing
        """

        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                try:
                    # NOTE:
                    #  In most cases user_id is None so it's better
                    #  instead of connecting to database and check None value
                    # check data in program

                    access_token_id = request.headers.get('Access-Token')
                    assert access_token_id

                    user_id = redis.get('uat:%s' % access_token_id)
                    assert user_id

                    g.user = cls.query.get(user_id) if populate else user_id
                    assert g.user

                    return f(*args, **kwargs)
                except AssertionError:
                    return abort(401)

            return wrapper

        return decorator

    def send_activation_code(self):
        code = str(randint(0, 99999)).zfill(5)
        redis.setex('uac:%d' % self.id, current_app.config['ACTIVATION_CODE_TIMEOUT'], code)
        current_app.logger.debug(sms.send_one('%s\nCode: %s' % (current_app.config['SITE_NAME'], code), self.phone)
                                 if sms.on else 'Code: %s' % code)

    def consume_activation_code(self, code):
        """
        :type code int
        """

        key = 'uac:%d' % self.id
        if redis.exists(key):
            r_code = redis.get(key)
            redis.delete(key)

            if r_code == code:
                return True
        return False

    def generate_access_token(self):
        code = str(uuid4())
        redis.setex('uat:%s' % code, current_app.config['ACCESS_TOKEN_TIMEOUT'], str(self.id))
        return code

    def populate(self, json):
        """
        Populate model from json dictionary
        :type json dict
        """

        if 'user_name' in json:
            self.user_name = json['user_name'] if len(json['user_name']) > 0 else None
        if 'real_name' in json:
            self.real_name = json['real_name'] if len(json['real_name']) > 0 else None
        if 'password' in json:
            self.password = json['password']
        if 'national_code' in json:
            self.national_code = json['national_code'] if len(json['national_code']) > 0 else None

    @classmethod
    def generate_fake(cls):
        """
        :rtype User
        """
        from faker import Factory
        from mixer.backend.flask import mixer

        mixer.faker.locale = 'fa'
        faker = Factory.create('fa_IR')

        fake = mixer.blend(cls)
        fake.real_name = faker.name()

        faker = Factory.create()
        while True:
            try:
                fake_username = faker.domain_word()
                fake.user_name = fake_username

                db.session.add(fake)
                db.session.commit()
                break
            except:
                db.session.rollback()

        return fake

    def to_json(self):
        return {'user_name': self.user_name,
                'real_name': self.real_name,
                'phone': self.phone,
                'registered_at': str(self.registered_at),
                'coupon_count': self.coupon_count,
                'national_code': self.national_code,
                'has_password': self.has_password()
                }
