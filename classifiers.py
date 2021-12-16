from types import new_class
from tflite_runtime.interpreter import Interpreter
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import time
import os
from picamera import PiCamera
from io import BytesIO
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from classifyable import *

class BaseCNN:
    def __init__(self, path2labels, path2model, classifyable_image) -> None:
        self.path2labels = path2labels
        self.path2model = path2model
        self._interpreter = None
        self._labels = None
        self._input_details = None
        self._output_details = None
        self._classifyable = classifyable_image

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

    def _set_input_image(self, new=False):
        """
        
        USAGE MANUAL: STEP 2 Feed the image from picamera to the convolutional neural network.
        
        Args:
        - new (boolean) is the flag to request a fresh snap from classifyable
        Returns None

        """

        height = self._input_details[0]["shape"][1]
        width  = self._input_details[0]["shape"][2]
        snap = self._classifyable.resize((width, height))
        im2classify = np.expand_dims(snap, axis=0)
        self._interpreter.set_tensor(self._input_details[0]["index"], im2classify)

    def _predict(self):
        """

        USAGE MANUAL: STEP 3 Inovke the interpreter and detect objecs in image.

        Args: None
        Returns None

        """
        self._interpreter.invoke()

    @abstractmethod
    def _get_output_labels(self):
        """
        
        USAGE MANUAL: STEPS 4 Report the outcome depending on the cnn model used.

        """
        pass

    @abstractmethod
    def classify_snap(self):
        """

        USAGE MANUAL: STEPS 1-4 Take a snap and return the detected objects.

        """
        pass

class MobileNet(BaseCNN):
    def __init__(self, path2labels, path2model, classifyable_image) -> None:
        super().__init__(path2labels, path2model, classifyable_image)

    def _get_output_labels(self, topk):
        """

        Args
        - topk (int) is the number of top-ranking matches desired.
        Returns a list of tuples, each with the class label and success probability,
        for the top k matches.

        """
        output = np.squeeze(self._interpreter.get_tensor(self._output_details[0]["index"]))
        scale, zero_point = self._output_details[0]["quantization"]
        output = scale * (output - zero_point)

        ordered = np.argpartition(-output, topk)
        return [(self._labels[i], output[i]) for i in ordered[:topk]]

    def classify_snap(self, new=False, topk=5):
        """

        Args
        - topk (int) is the desired number of top-ranking matches.
        Returns a list of tuples, each containing the class label and success probability,
        for the top-ranking matches.
        
        """
        self.complete_initialization() if not self._interpreter else None
        self._set_input_image(new=new)
        self._predict()
        result = self._get_output_labels(topk=topk)

        return result

class Coco(BaseCNN):
    def __init__(self, path2labels, path2model, classifyable_image) -> None:
        super().__init__(path2labels, path2model, classifyable_image)
        _snap = None

    def _set_labels(self):
        super()._set_labels()
        if self._labels[0] == '???':
            del(self._labels[0])

    def _get_output_labels(self, threshold=0.45):
        boxes = self._interpreter.get_tensor(self._output_details[0]['index'])[0] # Bounding box coordinates of detected objects
        classes = self._interpreter.get_tensor(self._output_details[1]['index'])[0] # Class index of detected objects
        scores = self._interpreter.get_tensor(self._output_details[2]['index'])[0] # Success probabilities of detected objects

        results = [(self._labels[int(classes[i])], "{}%".format(int(scores[i]*100))) for i in range(len(scores)) if scores[i] > threshold]
        print("Found {}".format(results if (len(results)>0) else "NONE!"))

        height = self._input_details[0]["shape"][1]
        width  = self._input_details[0]["shape"][2]
        snap_in = self._classifyable.resize((width, height))
        snap_out = snap_in.copy()
        snapbb = ImageDraw.Draw(snap_out)

        for i in range(len(scores)):
            if ((scores[i] > threshold) and (scores[i] <= 1.0)):

                # Get the bounding box for ith object and draw it
                # Calculate the coordinates in pixel, clipping boxes to image perimeter where required.
                ymin = int(max(1, boxes[i][0] * height)) # Clip to 1 px from edge when required
                xmin = int(max(1, boxes[i][1] * width))
                ymax = int(min(width-1, boxes[i][2] * height))
                xmax = int(min(height-1, boxes[i][3] * width))
                bbox = [(xmin, ymin), (xmax, ymax)]
                print("TL: {:.2f}, {:.2f} BR: {:.2f}, {:.2f}.".format(xmin, ymin, xmax, ymax))
                snapbb.rectangle(bbox, outline="yellow")

                # Make and add labels
                font = ImageFont.truetype(r'./Assets/arial.ttf', 12)
                tloc = (xmin, ymin)
                title = "{}: {}%".format(self._labels[int(classes[i])], int(scores[i]*100))
                snapbb.text(tloc, title, fill="red", font=font, align="left")

        return snap_in, snap_out, results

    def classify_snap(self, new=False, threshold=0.45):
        """

        Args
        - threshold (float) is the cut-off probability of successful detection.
        Returns a list of tuples, each containing the class label and success probability,
        for the top-ranking matches.
        
        """
        self.complete_initialization() if not self._interpreter else None
        self._set_input_image(new=new)
        self._predict()
        return self._get_output_labels(threshold=threshold)
