from picamera import PiCamera, array
import numpy as np
from io import BytesIO
from PIL import Image, ImageFilter, ImageMorph, ImageEnhance
import matplotlib.pyplot as plt
import time
import os

class MotionDetector:
    def __init__(self, width, height, detection_interval):
        self.width = width
        self.height = height

    def __str__(self) -> str:
        pass

    def _take_motion_snap(self):
        width = self.width
        height = self.height
        with PiCamera() as Eye:
            time.sleep(1)
            Eye.resolution = (width, height)
            Eye.rotation = 180
            with array.PiRGBArray(camera=Eye) as Stream:
                Eye.exposure_mode = 'auto'
                Eye.awb_mode = 'auto'
                Eye.capture(Stream, format='rgb')
                return Stream.array

    def _take_two_motion(self):
        intervalsec = self.detection_interval
        im_one = self.take_motion_snap()
        tic = time.time()
        toc = tic
        while (toc - tic) < intervalsec:
            toc = time.time()
        im_two = self.take_motion_snap()
        im_diff = np.subtract(im_two, im_one)
        return im_diff

    def _threshold_difference(self, imdiff, threshold=50):
        return np.uint8(np.where(imdiff > threshold, 255, 0))

    def _erode_dilate(self, snap, showme=False):
        snap_eroded = snap.filter(ImageFilter.MinFilter(7))
        if showme:
            snap_eroded.show()
            print("After erosion, got median, mean as {:.2f}, {:.2f}.".format(np.median(snap_eroded), np.mean(snap_eroded)))
        snap_dilated = snap_eroded.filter(ImageFilter.MaxFilter(3))
        if showme:
            snap_dilated.show()
            print("After dilation, got median, mean as {:.2f}, {:.2f}.".format(np.median(snap_dilated), np.mean(snap_dilated)))
        snap_bnw = snap_dilated.convert('1')
        bnw_array = np.array(snap_bnw)
        if showme:
            snap_bnw.show()
            print("B&W image for motion detection has dimensions {}".format(bnw_array.shape))
        return bnw_array

    

    

    