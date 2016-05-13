#!/usr/bin/env python
# -*- coding: utf-8 -*-
# find . -name "*.pyc" -exec rm -rf {} \;

# python imports
import unittest
import json

# project imports
from application import create_app
from application.config import TestingConfig
from application.extensions import db, redis
from application.models import User


def authenticate(self, phone):
    return self.client.post('/api/v1/user/authenticate', headers=self.headers, data=json.dumps({'phone': phone}))


def activate(self, phone, code):
    return self.client.post('/api/v1/user/activate', headers=self.headers,
                            data=json.dumps({'phone': phone, 'code': code}))


def web_authenticate(self, phone, password):
    return self.client.post('/api/v1/user/web_authenticate', headers=self.headers,
                            data=json.dumps({'phone': phone, 'password': password}))


def refresh(self, access_token, refresh_token):
    return self.client.post('/api/v1/user/refresh', headers=self.headers,
                            data=json.dumps({'access': access_token, 'refresh': refresh_token}))


def access(self, phone):
    response = activate(self, phone, '13740')
    access_token = json.loads(response.data)['access']
    self.headers['Access-Token'] = access_token
    return access_token


def create_password(self, password):
    return self.client.post('/api/v1/user/password', headers=self.headers,
                            data=json.dumps({'new_password': password}))


class UserTestCase(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestingConfig)
        with cls.app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.drop_all()
            db.session.remove()
        cls.app.extensions['redis'].flushdb()

    def setUp(self):
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        self.client = self.app.test_client(use_cookies=False)

    def tearDown(self):
        pass

    def test_authenticate(self):
        with self.app.app_context():
            response = authenticate(self, "093081849422")
            self.assertEquals(response.status_code, 400)

            response = authenticate(self, 93081849422)
            self.assertEquals(response.status_code, 400)

            response = authenticate(self, "09308184942")
            self.assertEquals(response.status_code, 201)

            response = authenticate(self, "09308184942")
            self.assertEquals(response.status_code, 200)

    def test_activate(self):
        with self.app.app_context():
            phone = "09375876887"
            authenticate(self, phone)
            user_obj = User.query.filter_by(phone=phone).one()
            key = 'uac:%d'

            response = activate(self, "093014778811", "13740")
            self.assertEquals(response.status_code, 400)

            response = activate(self, phone, "1374")
            self.assertEquals(response.status_code, 400)

            response = activate(self, phone, "13741")
            self.assertEquals(response.status_code, 401)

            self.assertIsNone(redis.get(key % user_obj.id))

            authenticate(self, phone)
            response = activate(self, phone, redis.get(key % user_obj.id))
            self.assertEquals(response.status_code, 201)

            response = activate(self, phone, '13740')
            self.assertEquals(response.status_code, 201)
            response = activate(self, "09301477885", "13740")
            self.assertEquals(response.status_code, 404)

    def test_web_authenticate(self):
        with self.app.app_context():
            phone = "09375876888"
            password = "123456"
            authenticate(self, phone)
            access(self, phone)

            response = web_authenticate(self, "093014778811", password)
            self.assertEquals(response.status_code, 400)

            response = web_authenticate(self, phone, "12345")
            self.assertEquals(response.status_code, 400)

            response = web_authenticate(self, phone, "1234567")
            self.assertEquals(response.status_code, 401)

            create_password(self, password)
            response = web_authenticate(self, phone, password)
            self.assertEquals(response.status_code, 200)

            response = web_authenticate(self, "09123421382", password)
            self.assertEquals(response.status_code, 404)

    def test_refresh(self):
        with self.app.app_context():
            phone = "09375876889"
            authenticate(self, phone)
            active = activate(self, phone, '13740')
            access_token = active.data.split("\"")[3]
            refresh_token = active.data.split("\"")[7]

            response = refresh(self, access_token, None)
            self.assertEqual(response.status_code, 400)

            response = refresh(self, None, refresh_token)
            self.assertEqual(response.status_code, 400)

            response = refresh(self, access_token, '"' + refresh_token + '"')
            self.assertEqual(response.status_code, 404)
            # TODO there is a bug if access_token or refresh_token send with "" two different error raises it means json validate have bug

            response = refresh(self, access_token, "82e53034-3552-4b68-8ded-3be2da7753d7")
            self.assertEqual(response.status_code, 404)

            response = refresh(self, "663a9829-c950-43f5-bfaf-7484d1b62163", refresh_token)
            self.assertEqual(response.status_code, 401)

            active = activate(self, phone, '13740')
            access_token = active.data.split("\"")[3]
            refresh_token = active.data.split("\"")[7]

            response = refresh(self, access_token, refresh_token)
            self.assertEqual(response.status_code, 200)

    def test_info(self):
        def info():
            return self.client.get('/api/v1/user', headers=self.headers)

        with self.app.app_context():
            response = info()
            self.assertEqual(response.status_code, 401)

            phone = "09375876889"
            authenticate(self, phone)
            access(self, phone)

            response = info()
            self.assertEqual(response.status_code, 200)

    def test_info_other(self):
        def info_other(user_id):
            return self.client.get('/api/v1/user/%d' % user_id, headers=self.headers)

        with self.app.app_context():
            phone = "09375876879"
            authenticate(self, phone)
            authenticate(self, "09166682828")
            access(self, phone)

            response = info_other(2)
            self.assertEqual(response.status_code, 200)

            response = info_other(85)
            self.assertEqual(response.status_code, 404)

    def test_edit_info(self):
        def edit_info(user_name, real_name, national_code):
            data = {'user_name': user_name, 'real_name': real_name, 'national_code': national_code}
            if user_name is None:
                data.pop('user_name')
            if real_name is None:
                data.pop('real_name')
            if national_code is None:
                data.pop('national_code')

            return self.client.put('/api/v1/user', headers=self.headers, data=json.dumps(data))

        with self.app.app_context():
            response = edit_info('salar', "sali", None)
            self.assertEqual(response.status_code, 401)
            phone = "09375876789"
            authenticate(self, phone)
            access(self, phone)

            response = edit_info('salar', "sali", "849849849")
            self.assertEqual(response.status_code, 400)

            response = edit_info('salar', "sali", 4360455098)
            self.assertEqual(response.status_code, 400)

            response = edit_info('salar', None, "4360400071")
            self.assertEqual(response.status_code, 200)

            response = edit_info('salar', None, None)
            self.assertEqual(response.status_code, 200)

            response = edit_info(None, None, None)
            self.assertEqual(response.status_code, 200)

            response = edit_info('salar', "sali", None)
            self.assertEqual(response.status_code, 200)

            response = edit_info('salar', "sali", "4560168202")
            self.assertEqual(response.status_code, 200)

            authenticate(self, "09123421380")
            access(self, "09123421380")

            response = edit_info('sala', "sali", "0510027288")
            self.assertEqual(response.status_code, 200)

            response = edit_info('salar', "sali", "4516415364")
            self.assertEqual(response.status_code, 409)

            # response = edit_info('salefsad', "sali", "4560515191") # TODO there is problem after 409 error
            # self.assertEqual(response.status_code, 409)

    def test_create_password(self):
        with self.app.app_context():
            response = create_password(self, "321321")
            self.assertEqual(response.status_code, 401)
            phone = "09375876885"
            authenticate(self, phone)
            access(self, phone)

            response = create_password(self, "32111")
            self.assertEqual(response.status_code, 400)

            response = create_password(self, 321111)
            self.assertEqual(response.status_code, 400)

            response = create_password(self, "32111")
            self.assertEqual(response.status_code, 400)

            response = create_password(self, None)
            self.assertEqual(response.status_code, 400)

            response = create_password(self, "32141541")
            self.assertEqual(response.status_code, 201)

            response = create_password(self, "654884")
            self.assertEqual(response.status_code, 406)

    def test_edit_password(self):
        def edit_password(self, old_password, new_password):
            return self.client.put('/api/v1/user/password', headers=self.headers,
                                   data=json.dumps({'new_password': new_password, 'old_password': old_password}))

        with self.app.app_context():
            phone = "09375876884"
            authenticate(self, phone)
            access(self, phone)

            create_password(self, "123123")
            response = edit_password(self, "123124", "654654654")
            self.assertEqual(response.status_code, 406)

            response = edit_password(self, "123123", "654")
            self.assertEqual(response.status_code, 400)

            response = edit_password(self, "123", "654654654")
            self.assertEqual(response.status_code, 400)

            response = edit_password(self, 123123, "654654654")
            self.assertEqual(response.status_code, 400)

            response = edit_password(self, "123123", "654654654")
            self.assertEqual(response.status_code, 200)

            response = edit_password(self, "123123", "6546545646854")
            self.assertEqual(response.status_code, 406)

            response = edit_password(self, "654654654", "846865486")
            self.assertEqual(response.status_code, 200)

    def test_delete_password(self):
        def delete_password(self, old_password):
            return self.client.delete('/api/v1/user/password', headers=self.headers,
                                      data=json.dumps({'old_password': old_password}))

        with self.app.app_context():
            phone = "09375876883"
            authenticate(self, phone)
            access(self, phone)

            response = delete_password(self, "123123")
            self.assertEqual(response.status_code, 406)

            create_password(self, "123123")
            response = delete_password(self, "3215")
            self.assertEqual(response.status_code, 400)

            response = delete_password(self, "123123")
            self.assertEqual(response.status_code, 200)

            response = delete_password(self, "123123")
            self.assertEqual(response.status_code, 406)

    def test_revoke(self):
        def revoke():
            return self.client.delete('/api/v1/user/revoke', headers=self.headers)

        with self.app.app_context():
            phone = "09372643535"
            authenticate(self, phone)
            access(self, phone)

            response = revoke()
            self.assertEqual(response.status_code, 200)

            response = revoke()
            self.assertEqual(response.status_code, 401)

    def test_revoke_all(self):
        pass


if __name__ == '__main__':
    unittest.main()
