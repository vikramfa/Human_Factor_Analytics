# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 12:52:04 2017

@author: vigsrinivasan
"""

# USAGE
# python detect_blinks.py --shape-predictor shape_predictor_68_face_landmarks.dat --video blink_detection_demo.mp4
# python detect_blinks.py --shape-predictor shape_predictor_68_face_landmarks.dat

# import the necessary packages
from scipy.spatial import distance as dist
#from imutils.video import FileVideoStream
#from imutils.video import VideoStream
#import mysql_insert as ms
from imutils import face_utils
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2


class EarAlogirthm:

    EYE_AR_THRESH = 0.3
    EYE_AR_CONSEC_FRAMES = 3
    COUNTER = 0
    TOTAL = 0 
 
    def loadShapePredictor(self, shapePreditctorAlgorithmPath):
            print("[INFO] loading facial landmark predictor...")
            self.detector = dlib.get_frontal_face_detector()
            self.predictor = dlib.shape_predictor(shapePreditctorAlgorithmPath)
            (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
            (self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
            print("[INFO] starting video stream thread...")
            
    def eye_aspect_ratio(self, eye):
        try:
            A = dist.euclidean(eye[1], eye[5])
            B = dist.euclidean(eye[2], eye[4])
            C = dist.euclidean(eye[0], eye[3])
            ear = (A + B) / (2.0 * C)
            return ear
        except Exception as exp:
            print('Exception occured during ear calculation:'+str(exp))
            raise exp

    def shapeFilterAlgorithm(self, imageFrame):
        info = (0,0)
        try:
            frame = imutils.resize(imageFrame, width=450)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #cv2.imshow("test window", gray)
            #cv2.waitKey(1000)
            #cv2.destroyAllWindows()
            rects = self.detector(gray, 0)
            for rect in rects:
                shape = self.predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)
                leftEye = shape[self.lStart:self.lEnd]
                rightEye = shape[self.rStart:self.rEnd]
                leftEAR = self.eye_aspect_ratio(leftEye)
                rightEAR = self.eye_aspect_ratio(rightEye)
                ear = (leftEAR + rightEAR) / 2.0
                leftEyeHull = cv2.convexHull(leftEye)
                rightEyeHull = cv2.convexHull(rightEye)
                cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
                if ear < self.EYE_AR_THRESH:
                    self.COUNTER += 1
                else:
                    if self.COUNTER >= self.EYE_AR_CONSEC_FRAMES:
                        self.TOTAL += 1
                    self.COUNTER = 0
                cv2.putText(frame, "Blinks: {}".format(self.TOTAL), (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                #cv2.imshow("Frame", frame)
                #cv2.waitKey(1)
                info = (self.TOTAL,ear)
        except Exception as exp:
            print('failure in running the ear alogirthm due to:'+str(exp))
            raise exp
        return info
           


        