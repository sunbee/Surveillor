from tflite_runtime.interpreter import Interpreter
from PIL import Image
import numpy as np
import time
import os
from picamera import PiCamera
from io import BytesIO
import matplotlib.pyplot as plt

class ObjectDetector:
    def __init__(self, path2labels, path2model) -> None:
        self.path2labels = path2labels
        self.path2model = path2model
        self._intepreter = None
        self._labels = None
        self._input_details = None
        self._output_details = None

    def _set_labels(self):
        with open(self.path2labels) as text_labels:
            labels = text_labels.readlines()
        labels = [label.rstrip() for label in labels]
        self._labels = labels

    def _set_interpreter(self):
        self._interpreter = Interpreter(self.path2model)
        self._interpreter.allocate_tensors()

    def _set_input_details(self):
        self._input_details = self._interpreter.get_input_details()

    def _set_output_details(self):
        self._output_details = self._interpreter.get_output_details()

    def complete_initialization(self):
        """
        * MUST CALL BEFORE USE OF OBJECT FOR IMAGE CLASSIFICATION *

        USAGE MANUAL:
        1. Set up classifier (* THIS STEP *)
        2. Give image as input for prediction
        3. Perform prediction
        4. Report results of prediction 

        STEPS MUST BE PERFORMED IN THE ORDER SPECIFIED.
        """
        self._set_labels()
        self._set_interpreter()
        self._set_input_details()
        self._set_output_details()

    def take_snap(self, width, height):
        with PiCamera() as Eye:
            Eye.rotation = 180
            Eye.resolution = (512, 512)
            with BytesIO() as Stream:
                Eye.capture(Stream, 'jpeg')
                Stream.seek(0)
                snap = Image.open(Stream).convert('RGB').resize((height, width))
                return snap

    def showsnap(self, snap, title='', label=''):
        # Show in notebook
        font = {'family': 'serif', 'color': 'red', 'size': 18}
        plt.imshow(snap)
        plt.xticks([])
        plt.yticks([])
        plt.title(title, fontdict=font)
        if not label:
            plt.xlabel(" x ".join("{}".format(i) for i in np.array(snap).shape), fontdict=font)
        plt.show()

    def _set_input_image(self, show=False):
        """
        * USAGE MANUAL: STEP 2 *

        Feed the image from picamera to the convolutional neural network.
        Args:
        - show (boolean) will render the snapshot FOR USE IN DEBUGGING ONLY
        Returns None
        """
        height = self._input_details[0]["shape"][1]
        width  = self._input_details[0]["shape"][2]

        print("Got size of input image as {} x {} in {}-D.".format(height, width, len(self._input_details[0]["shape"])))

        snap = self.take_snap(width, height)
        self.showsnap(snap) if show else None

        im2classify = np.expand_dims(snap, axis=0)
        self._interpreter.set_tensor(self._input_details[0]["index"], im2classify)

    def _predict(self):
        """

        * USAGE MANUAL: STEP 3 *

        Inovke the interpreter and detect objecs in imae.
        Args: None
        Returns None
        """
        self._interpreter.invoke()

    def _get_output_labels(self, topk):
        """
        
        * USAGE MANUAL: STEP 4 *

        Report the objects detected in the image with probability of success.
        Args
        - topk is an integer specifying the desired rank of the match
        Returns a list of tuples with the match label and success probability
        of the top k matches.
        """
        output = np.squeeze(self._interpreter.get_tensor(self._output_details[0]["index"]))
        scale, zero_point = self._output_details[0]["quantization"]
        output = scale * (output - zero_point)

        ordered = np.argpartition(-output, topk)
        return [(self._labels[i], output[i]) for i in ordered[:topk]]

    def classify_snap(self, topk=12):
        """

        Combines steps 2 through 4 in USAGE MANUAL.

        Takes a snap and returns the detected objects.
        Args
        - topk is an integer specifying the desired rank of the match
        Returns a list of tuples with the match label and success probability
        of the top k matches.
        """
        self._complete_initialization() if not self._interpreter else None
        self._set_input_image()
        self._predict()
        result = self._get_output_labels(topk)

        return result





