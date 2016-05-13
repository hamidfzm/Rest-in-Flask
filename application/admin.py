# python imports
from os import path
from wtforms import PasswordField
# flask imports
from flask import request, url_for, redirect, current_app, Markup
from flask.ext.admin.contrib.sqla import ModelView
from flask_admin import form

download_mu = Markup(
    """<a class="icon" target="_blank" title="View" href="%s""><span class="fa fa-eye glyphicon glyphicon-download-alt"></span></a>""")


class AdminModelView(ModelView):
    can_view_details = True
    can_export = True
    details_modal = True

    def is_accessible(self):
        return True

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))
