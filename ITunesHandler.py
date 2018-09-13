from http.server import BaseHTTPRequestHandler, HTTPServer
import struct
import urllib

class PairingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if (self.path.startswith('/pair?')):
            # any incoming requests are just pairing code related
            # return our guid regardless of input

            print (self.path[6:])
            
            parms = urllib.parse.parse_qs(self.path[6:])
            self.pairingcode = parms['pairingcode']
            self.servicename = parms['servicename']
            print('pairingcode=%s servicename=%s' % (self.pairingcode, self.servicename))
            values = {
                'cmpg': '\x00\x00\x00\x00\x00\x00\x00\x02',
                'cmnm': 'Android remote',
                'cmty': 'ipod',
            }

            encoded = ''
            bEncoded = bytearray()
            for key, value in values.items():
                bEncoded.extend(key.encode('ascii'))
                bEncoded.extend(struct.pack('>i', len(value)))
                bEncoded.extend(value.encode('ascii'))
            
            bHeader = bytearray()
            bHeader.extend('cmpa'.encode('ascii'))
            bHeader.extend(struct.pack('>i', len(bEncoded)))
            bHeader.extend(bEncoded)

            #print('bHeader=%s' % (bHeader))
            self.send_response(200)
            self.send_header('Content-Length', len(bHeader))
            self.end_headers()
            self.wfile.write(bHeader)

try:
    port = 1024
    server = HTTPServer(('', port), PairingHandler)
    print ('started server on port %s' % (port))
    server.serve_forever()

except KeyboardInterrupt:
    server.socket.close()
