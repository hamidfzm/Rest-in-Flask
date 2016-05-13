# python imports
from wtforms import FileField
from wtforms.validators import DataRequired

# flask imports
from flask.ext.wtf import Form


class UploadAvatar(Form):
    file = FileField(validators=[DataRequired()])
