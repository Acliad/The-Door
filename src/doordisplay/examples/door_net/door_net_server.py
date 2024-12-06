# This script is a basic headless HTTP data server.
# When it starts, it will generate an RSA key to authenticate POST data.

# Posts must be an encoded JSON list
#  * element 0 must be the string "Door"
#  * element 1 is the data to be hosted


from http.server import HTTPServer, BaseHTTPRequestHandler
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import json

PORT = 1337

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
        print("Get Received")
        global server_data
        self.send_response(200)
        self.end_headers()
        self.wfile.write(server_data)

    def do_POST(self):
        print("Post Received")
        global server_data
        try:
            content_length = int(self.headers.get("Content-Length"))
            encrypted_data = self.rfile.read(content_length)

            # Decrypt the data using the server's private key
            decrypted_data = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            json_data = json.loads(decrypted_data.decode("utf-8"))
            assert json_data[0] == "Door"
            server_data = json_data[1].encode("utf-8")
            self.send_response(200)
            self.end_headers()
        except:
            self.send_response(400)
            self.end_headers()

if __name__ == "__main__":
    # Print the public key for distribution
    print(public_pem.decode())

    # Define the server address and port
    server_address = ("", PORT)  # "" means all available interfaces, port 8000
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    try:
        print("Server Start")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
        httpd.server_close()
