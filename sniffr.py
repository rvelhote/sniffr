# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# # In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org>
import requests
import string
import base64
import cgi

# XSRF
from flask.ext import xsrf

# Recaptcha
from extensions.recaptcha import GoogleRecaptchaHandler
from sniffrexception import SniffrException

# Exceptions
from sniffrexception import RequestFailedException

# Requests
from requests.structures import CaseInsensitiveDict

from urlparse import urlparse

# Flask
from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from flask import session
from flask import Response

# Asset Management
from flask.ext.assets import Environment, Bundle

import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Register all assets that will be minified
# TODO Find a way to include the bundle in a different (separate) file
assets = Environment(app)
assets.debug = False

js_libs = Bundle(
    'assets/angular/angular.js',
    'assets/angular-cookies/angular-cookies.js',
    'assets/angular-sanitize/angular-sanitize.js',
    'assets/angular-lz-string/angular-lz-string.js',
    'assets/nprogress/nprogress.js',
    'assets/angular-recaptcha/release/angular-recaptcha.js',
    filters='rjsmin',
    output='gen/libraries.js')
assets.register("libraries", js_libs)

js_app = Bundle(
    'application/js/application.js',
    'application/js/controllers/sniffr-controller.js',
    'application/js/directives/sniffr-title.js',
    'application/js/directives/sniffr-keyvalue-table.js',
    'application/js/filters/human-readable.js',
    filters='rjsmin',
    output='gen/application.js')
assets.register("application", js_app)

# Setup application logging
# TODO Setup SMTP logging for critical errors
file_handler = RotatingFileHandler('/var/log/sniffr.log', 'a', 1 * 1024 * 1024, 10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

# Load default configuration
app.config.from_pyfile("sniffr.settings.py")
app.secret_key = app.config.get("SECRET_KEY")


@app.before_request
def before_request():
    if 'user_id' not in session:
        session['user_id'] = base64.urlsafe_b64encode(str(request.remote_addr) + str(request.user_agent))


def get_user_id():
    return session.get('user_id')

# XSRF Token Handler
# TODO Get some salt to add to the hash
xsrfh = xsrf.XSRFTokenHandler(user_func=get_user_id, secret=app.config.get("XSRF_KEY"), timeout=3600)

# Google Recaptcha Handler
# TODO Get some salt to add to the hash
recaptcha_handler = GoogleRecaptchaHandler(secret=app.config.get("RECAPTCHA_PRIVATE_KEY"), timeout=1800)


@app.errorhandler(SniffrException)
@xsrfh.send_token()
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/", methods=['GET'])
@xsrfh.send_token()
def index():
    """
    Display the main page of the application
    :return: string
    """
    user = {
        'ip': request.remote_addr,
        'agent': request.user_agent
    }

    recaptcha = {
        'show': recaptcha_handler.is_token_invalid(),
        'public_key': app.config.get("RECAPTCHA_PUBLIC_KEY")
    }

    configuration = {
        'analytics_key': app.config.get("ANALYTICS_KEY")
    }

    return Response(render_template('index.html', user=user, recaptcha=recaptcha, configuration=configuration))


@app.route('/q', methods=['POST'])
@xsrfh.handle_token()
@xsrfh.send_token()
@recaptcha_handler.verify()
def sniffit():
    """
    Perform an HTTP/HTTPS request to the address that the user specifid
    :return:

    TODO Make the Google Verification a separate module with annotion
    """
    parsed_url = urlparse(request.json["url"])
    app.logger.info(request.remote_addr + " " + parsed_url.netloc)

    # Processing the headers to be sent to the URL that the user defined in the interface.
    # What we are doing here is making sure the the user can't override some headers that we want to force such as
    # X-Forwarded-For.
    request_headers = CaseInsensitiveDict({header["key"]: header["value"] for header in request.json["headers"]})

    request_headers["X-Forwarded-For"] = request.remote_addr
    request_headers["X-Anti-Abuse"] = app.config.get("ABUSE_CONTACT")

    request_headers = {string.capwords(k, "-"): v for (k, v) in request_headers.items()}

    # Request Parameters
    if type(request.json["parameters"]) is list:
        request_parameters = "&".join([cgi.escape(header["key"])+"="+cgi.escape(header["value"]) for header in request.json["parameters"]])
    else:
        request_parameters = request.json["parameters"]

    # Base Response JSON
    response_json = {'success': False, 'sniffed': None, 'messages': []}

    try:
        if string.lower(request.json["method"]) in ["get", "head", "options"]:
            response = requests.request(request.json["method"], request.json["url"], verify=False,
                                        params=request_parameters, headers=request_headers)
        else:
            response = requests.request(request.json["method"], request.json["url"],
                                        verify=False, data=request_parameters, headers=request_headers)

        # I prefer to have the capitalized headers in the frontend
        # This will convert the headers from 'content-type' to 'Content-Type'
        response_headers = {string.capwords(k, "-"): v for (k, v) in response.headers.items()}

        # This is for the adrministrators only so there is no need for the end-user to see this
        request_headers.pop("X-Anti-Abuse")
        request_headers.pop("X-Forwarded-For")

        # Create a history of redirects to inform the user
        redirections = [{"url": redirect.url} for redirect in response.history]

        response_json["success"] = True
        response_json["showRecaptcha"] = recaptcha_handler.is_token_invalid()
        response_json["sniffed"] = {
            'headers': {
                'response': response_headers,
                'request': request_headers
            },
            'ssl': None,
            'redirect': redirections,
            'body': base64.b64encode(cgi.escape(response.text.encode("UTF-8"))),
            'size': response.headers.get("content-length", False),
            'ssize': len(response.text.encode("UTF-8")),
            'elapsed': response.elapsed.total_seconds(),
            'status': str(response.status_code) + " " + response.reason,
        }
    except Exception as e:
        raise RequestFailedException(repr(e))

    return jsonify(response_json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
