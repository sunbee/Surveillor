from io import BytesIO
from PIL import Image
from picamera import PiCamera
import numpy as np
import matplotlib.pyplot as plt
import base64

class Classifyable:
    def __init__(self, rotation=180, exposure='auto', awb_mode='auto', resolution=(512, 512), format='jpeg'):
        self.rotation = rotation
        self.exposure = exposure
        self.resolution = resolution
        self.format = format
        self.snap = None

    def _take_snap(self):
        with PiCamera() as Eye:
            Eye.rotation = self.rotation
            Eye.resolution = self.resolution
            with BytesIO() as Stream:
                Eye.capture(Stream, self.format)
                Stream.seek(0)
                snap = Image.open(Stream).convert('RGB')
                return snap
    
    def set_snap(self):
        self.snap = self._take_snap()

    def show_snap(self, title='', label=''):
        font = {'family': 'serif', 'color': 'red', 'size': 12}
        plt.imshow(self.snap)
        plt.xticks([])
        plt.yticks([])
        plt.title(title, fontdict=font)
        if not label:
            plt.xlabel(" x ".join("{}".format(i) for i in np.array(self.snap).shape), fontdict=font)
        plt.show()

    def resize(self, resolution):
        return self.snap.resize(resolution) # (width, height)

    def tobase64enc(self, resolution=(224, 224)):
        buffered_bytes = BytesIO()
        self.snap.resize(resolution).save(buffered_bytes, 'jpeg')
        return base64.b64encode(buffered_bytes.getvalue())

    def toarray(self):
        return np.array(self.snap) 