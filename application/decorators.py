# python imports
from functools import wraps
from cStringIO import StringIO as IO
import gzip

# flask imports
from flask import request, current_app, abort, after_this_request, url_for, jsonify, g
from flask.ext.sqlalchemy import BaseQuery


def gzipped(f):
    @wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                        response.status_code >= 300 or
                        'Content-Encoding' in response.headers):
                return response
            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb',
                                      fileobj=gzip_buffer)
            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func


def paginate(key, max_per_page):
    """
    @apiDefine Paginate
    @apiSuccess {Object} meta Pagination meta data.
    @apiSuccess {Url} meta.first Url for first page of results
    @apiSuccess {Url} meta.last Url for last page of results
    @apiSuccess {Url} meta.next Url for next page of results
    @apiSuccess {Url} meta.prev Url for previous page of results
    @apiSuccess {int} meta.page number of the current page
    @apiSuccess {int} meta.pages all pages count
    @apiSuccess {int} meta.per_page item per each page
    @apiSuccess {int} meta.total count of all items
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            query = f(*args, **kwargs)
            page = request.args.get('page', 1, type=int)

            per_page = min(request.args.get('per_page', current_app.config['PAGE_SIZE'], type=int),
                           max_per_page)

            if not isinstance(query, BaseQuery):
                return f(*args, **kwargs)

            pagination_obj = query.paginate(page, per_page)
            meta = {'page': pagination_obj.page, 'per_page': pagination_obj.per_page,
                    'total': pagination_obj.total, 'pages': pagination_obj.pages}

            if pagination_obj.has_prev:
                meta['prev'] = url_for(request.endpoint, page=pagination_obj.prev_num,
                                       per_page=per_page,
                                       _external=True, **kwargs)
            else:
                meta['prev'] = None

            if pagination_obj.has_next:
                meta['next'] = url_for(request.endpoint, page=pagination_obj.next_num,
                                       per_page=per_page,
                                       _external=True, **kwargs)
            else:
                meta['next'] = None

            meta['first'] = url_for(request.endpoint, page=1,
                                    per_page=per_page, _external=True,
                                    **kwargs)
            meta['last'] = url_for(request.endpoint, page=pagination_obj.pages,
                                   per_page=per_page, _external=True,
                                   **kwargs)

            return jsonify({
                str(key): [item.to_json() for item in pagination_obj.items],
                'meta': meta
            })

        return wrapped

    return decorator
