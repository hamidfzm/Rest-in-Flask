# python imports
from jsl import Document, StringField


class Authenticate(Document):
    phone = StringField(required=True, pattern='^09[0-9]{9}$')


class WebAuthenticate(Document):
    phone = StringField(required=True, pattern='^09[0-9]{9}$')
    password = StringField(required=True, pattern='.{6,}')


class Activate(Document):
    phone = StringField(required=True, pattern='^09[0-9]{9}$')
    code = StringField(required=True, pattern='^[0-9]{5}$')


class Refresh(Document):
    access = StringField(required=True)
    refresh = StringField(required=True)


class EditInfo(Document):
    real_name = StringField()
    user_name = StringField()
    national_code = StringField()


class CreatePassword(Document):
    new_password = StringField(min_length=6, required=True)


class EditPassword(Document):
    old_password = StringField(min_length=6, required=True)
    new_password = StringField(min_length=6, required=True)


class DeletePassword(Document):
    old_password = StringField(min_length=6, required=True)
