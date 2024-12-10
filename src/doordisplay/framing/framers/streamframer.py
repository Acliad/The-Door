import threading
import traceback

from framing.framers.framer import Framer
import time
import requests
import json
from base64 import b64decode
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from the password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000
    )
    return kdf.derive(password.encode())


class StreamFramerWorker():
    def __init__(self, target_url:str, password:str, callback):
        self.password = password
        self.target_url = target_url
        self.callback = callback
        self.alive = False

    def run(self):
        self.alive = True
        while self.alive:
            try:
                response = requests.get(self.target_url)
                print("response code", response.status_code)
                if response.status_code == 200:
                    lines = response.content.decode("utf-8").split("\n")
                    salt = b64decode(lines[0].strip())
                    nonce = b64decode(lines[1].strip())
                    ciphertext = b64decode(lines[2].strip())
                    key = derive_key(self.password, salt)
                    aesgcm = AESGCM(key)
                    decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
                    frames = json.loads(decrypted_data.decode("utf-8"))
                    self.callback(frames)
            except:
                print(traceback.format_exc())
            time.sleep(0.01)


class StreamFramer(Framer):
    def __init__(self, target_url: str, password:str):
        super().__init__()

        self.frames = []
        self.frame_idx = -1 # not playing
        self.frame_time = 0

        self.worker = StreamFramerWorker(target_url, password, self.new_data)
        self.thread = threading.Thread(target=self.worker.run)
        self.thread.start()

    def new_data(self, *frames):
        self.frame_idx = -1 # not playing
        self.frame_time = 0
        self.frames = frames

    def update(self):
        """
        Updates the current frame of the stream framer.

        Returns:
            tuple[ndarray, dt]: The current frame and the time to display it in seconds.
        """
        if time.time() > self.frame_time and self.frame_idx < len(self.frames):
            self.frame_idx += 1
            self.matrix = self.frames[self.frame_idx]["matrix"]
            self.frame_time = time.time()+self.frames[self.frame_idx]["duration_s"]

        return super().update()

    def kill(self):
        self.worker.alive = False
        self.thread.join()

    def reset(self):
        pass