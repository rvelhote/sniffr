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
import time

from flask import request
from flask import session
from functools import wraps
from sniffrexception import SniffrException


class GoogleReCaptchaInvalidException(SniffrException):
    """

    """
    status_code = 403


class GoogleRecaptchaHandler:
    """

    """
    KEY = "RECAPTCHA_SUCCESS"
    TIMESTAMP_KEY = "RECAPTCHA_TIMESTAMP"
    VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

    def __init__(self, secret, timeout=3600):
        self.secret = secret
        self.timeout = timeout

    def is_token_valid(self):
        return session.get(self.KEY, False) != False and not self.is_token_timed_out()

    def is_token_invalid(self):
        return not self.is_token_valid()

    def is_token_timed_out(self):
        """
        Determine if the current token is expired or not. This is just a simple comparison of the current server time
        with the time of the sucessful verification plus the configured timeout.
        :return: True if the token is timed-out of False is the token can still be used
        """
        return time.time() > (self.get_success_timestamp() + self.timeout)

    def get_success_timestamp(self):
        """
        Obtain an Unix Timestamp that marks the time that the user verified with the Google Recaptcha API.
        :return: The Unix Timestamp of when the verification happened
        """
        return int(session.get(self.TIMESTAMP_KEY, time.time()))

    def authorize(self):
        session[self.KEY] = True
        session[self.TIMESTAMP_KEY] = int(time.time())

    def unauthorize(self):
        session.pop(self.KEY, None)
        session.pop(self.TIMESTAMP_KEY, None)

    def verify(self):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not self.is_token_valid():
                    # Payload to be sent to the ReCaptcha verification service
                    payload = {
                        "secret": self.secret,
                        "response": request.json["gcaptcha"] if "gcaptcha" in request.json else "",
                        "remoteip": request.remote_addr
                    }

                    google_request = requests.post(self.VERIFY_URL, data=payload)
                    google_response = google_request.json()

                    if not google_response["success"]:
                        raise GoogleReCaptchaInvalidException("Google ReCaptcha verification failed!", payload={"showRecaptcha": True})

                    self.authorize()
                return f(*args, **kwargs)
            return decorated_function
        return decorator
