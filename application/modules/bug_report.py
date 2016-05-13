# -*- coding: utf-8 -*-

"""
    This doc will show you how to configure bug report in Trello:

    get application key:
        1) Go to https://trello.com/app-key
        2) API_KEY = copy key from step 1

    get new token:
        1) import trello
        2) t = trello.TrelloApi(API_KEY)
        3) url = t.get_token_url('ChiChiKoo', expires='never')
        4) go to "url", login and allow and get id
        5) API_TOKEN = step 4 result id!

    get list id:
        1) https://trello.com/b/7SrW44NZ/chi-chi-koo
        2) BOARD_ID = 7SrW44NZ
        2) t = trello.Boards(API_KEY, API_TOKEN)
        3) LIST_ID = t.get_list(BOARD_ID)

    more information available at:
        http://pythonhosted.org/trello/trello.html
        https://trello.com/docs/api/
"""

# python imports
import trello
# flask imports
from flask import request

__author__ = 'Hamid FzM'


class BugReport:
    def __init__(self, app=None):
        self.key = None
        self.token = None
        self.list = None
        self.debug = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):

        config = app.config.get('BUG_REPORT')

        if not config:
            config = {
                'key': '',
                'token': '',
                'secret': '',
                'list': ''
            }

        self.key = config['key']
        self.token = config['token']
        self.list = config['list']
        self.debug = app.config['DEBUG']

    def report(self, error):
        # if self.debug:
        #     return

        try:
            code = error.code
        except Exception as e:
            code = 500

        title = "%s - %s" % (code, error.message) if error.message else "%s - %s" % (code, "Undefined")

        body = """
**Endpoint**: `%s`
**URL**: `%s`
**Referrer**: `%s`
**Headers**:

```
%s
```

**Args**: `%s`
**Request data**: `%s - %s`
**Response**: `%s`
        """ % \
               (request.endpoint,
                request.url,
                request.referrer,
                request.headers,
                request.values,
                request.method,
                request.module,
                error.args
                )

        t = trello.Cards(self.key, self.token)

        if self.unique_title(title) == 0:
            data = t.new(title, self.list, desc=body)
            t.new_label(data['id'], 'red')
            t.new_label(data['id'], 'blue')
        else:
            t.new_action_comment(self.unique_title(title), body)

    def unique_title(self, title):
        lists = trello.Lists(self.key, self.token)
        for item in lists.get_card(self.list):
            if item['name'] == title:
                return item['id']
        return 0
