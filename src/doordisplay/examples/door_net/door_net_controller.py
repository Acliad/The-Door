# import requests
# import json
# from cryptography.hazmat.primitives.asymmetric import padding
# from cryptography.hazmat.primitives import serialization, hashes
# from PyQt6 import QtWidgets as qtw
#
#
# URL = "http://localhost:8000"
#
# # server_public_key_pem = input("paste public key: ").encode("utf-8")
# server_public_key_pem = b"""
# """
#
# public_key = serialization.load_pem_public_key(server_public_key_pem)
#
# # Encrypt data with the server's public key
# data = json.dumps(["Door", {"a":"thing"}]).encode("utf8")
# encrypted_data = public_key.encrypt(
#     data,
#     padding.OAEP(
#         mgf=padding.MGF1(algorithm=hashes.SHA256()),
#         algorithm=hashes.SHA256(),
#         label=None
#     )
# )
#
# # Send the encrypted data in a POST request
# response = requests.post("http://localhost:8000", data=encrypted_data)
#
# # Print the server's response
# print(f"Response status: {response.status_code}")