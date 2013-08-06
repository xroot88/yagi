#!/usr/bin/env python
# Acts as a sink for HTTP requests. Accepts GET, POST, PUT, and DELETE
# methods. Accepts request, and prints to stdout.
#
# This script is usefull for testing Yagi handlers that make HTTP
# calls to external systems.

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser

class RequestHandler(BaseHTTPRequestHandler):
    HTTP_RESPONSE = 201

    def do_GET(self):
        request_path = self.path
        print("\n----- Request Start ----->\n")
        print(request_path)
        print(self.headers)
        print("<----- Request End -----\n")
        self.send_response(self.HTTP_RESPONSE)
        self.send_header("Set-Cookie", "foo=bar")

    def do_POST(self):
        request_path = self.path
        print("\n----- Request Start ----->\n")
        print(request_path)
        request_headers = self.headers
        content_length = request_headers.getheaders('content-length')
        length = int(content_length[0]) if content_length else 0
        print(request_headers)
        print(self.rfile.read(length))
        print("<----- Request End -----\n")

        self.send_response(self.HTTP_RESPONSE)

    do_PUT = do_POST
    do_DELETE = do_GET

def main(options):
    addr = options.address if options.address else "*"
    print('Listening on %s:%s' % (addr, options.port))
    #bleh
    RequestHandler.HTTP_RESPONSE = options.response

    server = HTTPServer((options.address, options.port), RequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-a', '--address', dest="address", default='',
                      help="IP Address to listen on.")
    parser.add_option('-p', '--port', dest="port", default=8080, type=int,
                      help="Port number to listen on.")
    parser.add_option('-r', '--response-code', dest="response", default=201, type=int,
                      help="HTTP response code to return on posts")
    parser.usage = ("Creates an http-server that will echo out any GET or POST parameters\n"
                    "Run:\n\n"
                    "   reflect")
    (options, args) = parser.parse_args()

    main(options)
