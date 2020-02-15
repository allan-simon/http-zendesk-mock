"""
Launch a fake zendesk.com
"""

import os
from http.server import HTTPServer

from .handler import MockHandler


def launch_server(hostname, port_number):
    """
    Start a mock instance of zendesk.com listening
    on given hostname and port
    """
    httpd = HTTPServer((hostname, port_number), MockHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == "__main__":
    PORT = int(os.getenv("MOCK_ZENDESK_PORT", "8084"))
    print("starting service on ", PORT)
    launch_server("0.0.0.0", PORT)
