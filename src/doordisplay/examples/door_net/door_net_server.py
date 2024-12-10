# This script is a basic headless HTTP data server.
# When it starts, it will generate an RSA key to authenticate POST data.
import traceback
# Posts must be an encoded JSON list
#  * element 0 must be the string "Door"
#  * element 1 is the data to be hosted


from http.server import HTTPServer, BaseHTTPRequestHandler
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import json
import base64
import time
PORT = 1336

server_data = b"[]"

# Generate RSA key pair
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Export public key for distribution
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):
        global server_data
        self.send_response(200)
        self.end_headers()
        self.wfile.write(server_data)
        self.wfile.flush()

    def do_POST(self):
        global server_data
        try:
            data_len = int(self.headers.get("Content-Length"))
            data = json.loads(self.rfile.read(data_len))
            a = base64.b64decode(data["a"].encode("utf-8"))
            b = base64.b64decode(data["b"].encode("utf-8"))
            if (time.time()-float(a) < 0.1) and a == private_key.decrypt(
                b,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )):
                server_data = data["c"].encode("utf-8")
                self.send_response(200)
                self.end_headers()
            else:
                print(a)
                print(private_key.decrypt(
                b,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )))
                self.send_response(401)
                self.end_headers()
        except:
            print(traceback.format_exc())
            self.send_response(400)
            self.end_headers()

if __name__ == "__main__":
    # Print the public key for distribution
    print(public_pem.decode())

    # Define the server address and port
    server_address = ("", PORT)  # "" means all available interfaces, port 8000
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
        httpd.server_close()