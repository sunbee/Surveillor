from picamera import PiCamera, array
import numpy as np
from io import BytesIO
from PIL import Image, ImageFilter, ImageMorph, ImageEnhance
import matplotlib.pyplot as plt
import time
import os

class MotionDetector:
    def __init__(self, width, height, delta, imthreshold, regionsize, showme=False):
        self.width = width
        self.height = height
        self.delta = delta
        self.threshold = imthreshold
        self.size = regionsize
        self.regions = {}
        self.candidates = {}
        self.showme = showme

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
        intervalsec = self.delta
        im_one = self.take_motion_snap()
        tic = time.time()
        toc = tic
        while (toc - tic) < intervalsec:
            toc = time.time()
        im_two = self.take_motion_snap()
        return (im_one, im_two, np.subtract(im_two, im_one))

    def _threshold_difference(self, imdiff):
        imthreshold = self.threshold
        return np.uint8(np.where(imdiff > imthreshold, 255, 0))

    def _erode_dilate(self, snap):
        snap_eroded = snap.filter(ImageFilter.MinFilter(7))
        snap_dilated = snap_eroded.filter(ImageFilter.MaxFilter(3))
        snap_bnw = snap_dilated.convert('1')
        return np.array(snap_bnw)

    def find_connected_components(self, imbnw):
        mask = np.zeros(imbnw.shape, dtype = np.int32)  # Mask 
        count_foreground = 0
        first_pass_counter = 0
        synonyms = {}

        for idx, x in np.ndenumerate(imbnw):
            aboveme = False     # B&W background
            leftofme = False    # B&W background
            A = 0           # Label none
            B = 0           # Label none
            if x: # Not background
                """
                Is there a pixel above or to the left that is not background?
                Check and if found, obtain the numeric labels 
                marking connected components in 1st pass.
                """
                count_foreground += 1
                if (idx[0] > 0): # Yes, above
                    aboveme = imbnw[idx[0]-1, idx[1]]
                    A = mask[idx[0]-1, idx[1]] # Get label
                if (idx[1] > 0): # Yes, on left
                    leftofme = imbnw[idx[0], idx[1]-1]
                    B = mask[idx[0], idx[1]-1] # Get label
                """
                If both left and above have foreground,
                stick the lesser number as the label on our pixel.
                Note the conflict for 2nd pass correction.
                Note that if the lower value has already been marked
                for correction, follow the chain to the lowest value
                in the dictionary of synonymous labels.
                If only one of left or above have foreground,
                stick that label on our pixel.
                Otherwise, mint a new label and stick it on.
                """
                if (aboveme and leftofme): # Contest if not A = B          
                    mask[idx] = min(A, B) # Resolve
                    if (A != B): # Note for update in second pass
                        if synonyms.get(min(A, B)):
                            synonyms[max(A, B)] = synonyms.get(min(A, B))
                        else:
                            synonyms[max(A, B)] = min(A, B)
                elif aboveme:
                    mask[idx] = A
                elif leftofme:
                    mask[idx] = B        
                else:
                    first_pass_counter += 1 # New label
                    mask[idx] = first_pass_counter

        connected_components = {}
        
        for idx,x in np.ndenumerate(mask):
            """
            Execute 2nd raster scan and update labels
            using the synonyms dictionary. 
            """
            if x > 0: # Labeled
                label = synonyms.get(x, 0) 
                if label > 0: # Synonym found for label
                    mask[idx] = label 
                    connected_components[label] = connected_components.get(label, 0) + 1
                else:
                    connected_components[x] = connected_components.get(x, 0) + 1
        
        self.candidates = connected_components
        return mask
        
    def analyze_connect_components(self):
        regions = self.candidates
        size = self.size 
        result = {label: regions[label] \
            for label in sorted(regions, key=regions.get, reverse=True) \
            if regions[label] > size}
        self.regions = regions
        return result

    def sense(self):
        imone, imtwo, imdiff = self._take_two_motion()
        imlevel = self._threshold_difference(imdiff=imdiff)
        imbnw = self._erode_dilate(snap=Image.fromarray(imlevel))
        mask = self.find_connected_components(imbnw=imbnw)

        if self.showme:
            outline = (3, 2)
            labels = np.array(["RAW FOOTAGE #1", "RAW FOOTAGE #2", "DIFFERENCE", "LEVEL", "B&W MASK", "REGIONS"])
            labels = labels.reshape(outline)
            labels

            font = {'family': 'serif', 'color': 'red', 'size': 18}

            _, axarray = plt.subplots(outline[0], outline[1], figsize=(12, 12))
            for idx, x in np.ndenumerate(labels):
                axarray[idx].set_xticks([])
                axarray[idx].set_yticks([])
                axarray[idx].set_title(labels[idx], fontdict=font)

            axarray[0, 0].imshow(imone)
            axarray[0, 1].imshow(imtwo)
            axarray[1, 0].imshow(imdiff)
            axarray[1, 1].imshow(imlevel)
            axarray[2, 0].imshow(imbnw)
            axarray[2, 1].imshow(mask)
            plt.show()

        return (imone, imtwo, imdiff, imlevel, imbnw, mask)


    

    