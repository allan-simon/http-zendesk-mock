# Disabled because pylint does not like upper case do_GET
# but we have to do so, otherwise it's not mapped to HTTP
# verb GET etc.
#
# pylint: disable=invalid-name
from typing import Union
from typing import Dict
from typing import List

from copy import deepcopy
import base64
import json as json_module
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler

from .search import handle_search

TICKETS_STORE: Dict[int, Dict] = {}
USERS_STORE: Dict[int, Dict] = {}
COMMENTS_STORE: Dict[int, List] = {}
MAX_COMMENT_ID = 0

DATA_STORE: Dict = {}

USERNAME = os.environ["MOCK_ZENDESK_USERNAME"]
API_KEY = os.environ["MOCK_ZENDESK_API_KEY"]


class MockHandler(BaseHTTPRequestHandler):
    """ Handle all requests as if it was an infogreffe.fr instance
    """

    def _send_json_response(self, json: Union[Dict, List], status_code=200):
        self._send_raw_json_response(
            json_body=json_module.dumps(json).encode("utf-8"), status_code=status_code
        )

    def _send_raw_json_response(self, json_body: bytes, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json_body)

    def _send_blank_response(self, status_code):
        self.send_response(status_code)
        self.end_headers()

    def _verify_auth(self) -> bool:
        # The method is on purpose very verbose and step by step
        # as this server is meant for development purpose, we want to be as precise
        # as possible on why we failed, so that our fellow developers can easily
        # find what's wrong with their code

        # for the moment we only support
        # https://developer.zendesk.com/rest_api/docs/support/introduction#api-token
        authorization_header = self.headers.get("Authorization")
        if authorization_header is None:
            print("auth failed because no Authorization header")
            return False

        if not authorization_header.startswith("Basic"):
            print("auth failed because no Basic method used in Authorization header")
            return False

        username_with_token_and_api_key = base64.decodebytes(
            authorization_header[len("Basic ") :].encode()
        ).decode()
        username_with_token, api_key = username_with_token_and_api_key.split(":")

        if username_with_token != f"{USERNAME}/token":
            print(
                f"auth failed because the username should be {USERNAME}/token "
                f"but got {username_with_token}"
            )
            return False

        if api_key != API_KEY:
            print(
                f"auth failed because the api key should be {API_KEY}"
                f"but got {api_key}"
            )
            return False

        return True

    def do_GET(self):
        """Answer to GET methods
        """
        if self._verify_auth() is False:
            self._send_json_response({}, status_code=401)

        if self.path.startswith("/api/v2/search.json"):
            # we take only the query part (i.e after the ?
            # and we extract the 'query' parameters
            search_query = urllib.parse.parse_qs(self.path.split("?")[1])["query"][0]

            # transform the zendesk search query which is "name:value othername:othervalue"
            # into a dict
            zendesk_query_params = dict(
                map(lambda query_item: query_item.split(":"), search_query.split(" "))
            )

            self._send_json_response(
                handle_search(TICKETS_STORE, zendesk_query_params), status_code=200
            )
            return

        if "/comments.json" in self.path:
            ticket_id = int(self.path.split("/")[4])
            if ticket_id not in TICKETS_STORE:
                self._send_json_response({}, status_code=404)
                return

            comments = COMMENTS_STORE.get(ticket_id, [])
            self._send_json_response({"comments": comments}, status_code=200)
            return

        if self.path.startswith("/api/v2/tickets/"):
            ticket_part = self.path.split("/")[4]
            if not ticket_part.endswith(".json"):
                self._send_json_response({}, status_code=404)
                return

            ticket_id = int(ticket_part.split(".")[0])
            ticket = TICKETS_STORE.get(ticket_id)
            if ticket is None:
                self._send_json_response({}, status_code=404)
                return

            self._send_json_response({"ticket": ticket}, status_code=200)
            return

        if self.path not in DATA_STORE:
            self._send_json_response({}, status_code=404)
            return

        self._send_raw_json_response(
            json_body=DATA_STORE[self.path]["body"],
            status_code=DATA_STORE[self.path]["status_code"],
        )

    def do_PUT(self):
        """Handle POST requests
        """

        if self._verify_auth() is False:
            self._send_json_response({}, status_code=401)

        body_size = int(self.headers["Content-Length"])
        body_string = self.rfile.read(body_size)

        body_dict = json_module.loads(body_string)
        print(body_dict)

        if self.path.startswith("/api/v2/tickets/"):
            ticket_part = self.path.split("/")[4]
            if not ticket_part.endswith(".json"):
                self._send_json_response({}, status_code=404)
                return

            ticket_id = int(ticket_part.split(".")[0])
            ticket = TICKETS_STORE.get(ticket_id)
            if ticket is None:
                self._send_json_response({}, status_code=404)
                return

            if ticket.get("status") == "closed":
                self._send_json_response(
                    {
                        "error": "RecordInvalid",
                        "description": "Record validation errors",
                        "details": {
                            "status": [
                                {"description": "Status: closed can't be updated"}
                            ]
                        },
                    },
                    status_code=422,
                )
                return

            comment_part = body_dict["ticket"].get("comment")
            if comment_part is not None:
                new_comment = deepcopy(comment_part)

                global MAX_COMMENT_ID
                MAX_COMMENT_ID += 1

                new_comment["id"] = MAX_COMMENT_ID

                comments = COMMENTS_STORE.get(ticket_id, [])
                comments.append(new_comment)
                COMMENTS_STORE[ticket_id] = comments

            self._send_json_response({"ticket": ticket}, status_code=200)
            return

        self._send_json_response({}, status_code=204)

    def do_POST(self):
        """Handle POST requests
        """
        if self._verify_auth() is False:
            self._send_json_response({}, status_code=401)

        if self.path.startswith("/api/v2/tickets.json"):
            body_size = int(self.headers["Content-Length"])
            body_string = self.rfile.read(body_size)

            body_dict = json_module.loads(body_string)
            print(body_dict)

            ticket_id = len(TICKETS_STORE) + 1
            # in case we've deleted some tickets
            # to avoid collision
            while ticket_id in TICKETS_STORE:
                ticket_id = len(TICKETS_STORE) + 1

            ticket = body_dict["ticket"]
            ticket["id"] = ticket_id
            TICKETS_STORE[ticket_id] = ticket

            if "requester" in ticket:
                next_user_id = len(USERS_STORE) + 1
                # in case we've deleted some users
                # to avoid collision
                while next_user_id in USERS_STORE:
                    next_user_id = len(USERS_STORE) + 1

                requester = ticket["requester"]
                requester["id"] = next_user_id
                USERS_STORE[next_user_id] = requester
                del ticket["requester"]
                ticket["requester_id"] = next_user_id

            if "comment" in ticket:

                global MAX_COMMENT_ID
                MAX_COMMENT_ID += 1

                comment = ticket["comment"]
                comment["id"] = MAX_COMMENT_ID
                COMMENTS_STORE[ticket_id] = [comment]

            self._send_json_response(body_dict, status_code=201)
            return

        self._send_json_response({}, status_code=204)

    def do_MOCK_INJECT(self):
        """ Handle non-standard HTTP verb 'MOCK_INJECT', to inject in cache

        The reason of using a non-standard verb is that we're sure
        not to overlap with existing API mapping

        It's used to prepopulate the given URL with the given data, so that
        the next GET requests on the very same URL (including get parameter)
        will get the given data in body
        """
        body_size = int(self.headers["Content-Length"])
        body_string = self.rfile.read(body_size)

        # allow the client to precise what will the status code
        # of its injected response
        # NOTE: if needed the same logic can be extended to other headers
        # as well
        status_code = int(self.headers.get("X-Mock-Status-Code", "200"))

        DATA_STORE[self.path] = {"status_code": status_code, "body": body_string}

        self.send_response(204)
        self.end_headers()

    def do_MOCK_FLUSH(self):
        """ Handle non-standard HTTP verb 'MOCK_FLUSH', to empty internal cache

        The reason of using a non-standard verb is that we're sure
        not to overlap with existing API mapping

        the URL given with this method is currently not used
        """

        DATA_STORE.clear()

        self.send_response(204)
        self.end_headers()

    def do_MOCK_DEBUG(self):
        """ Handle non-standard HTTP verb 'MOCK_DEBUG', to output DATASTORE

        the URL given with this method is currently not used
        """

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        self.wfile.write(json_module.dumps(DATA_STORE))
        self.wfile.close()
