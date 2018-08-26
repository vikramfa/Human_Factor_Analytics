#!/usr/bin/env python

import cv2
import numpy as np
from numpy import dot
from numpy.linalg import norm
from imutils import face_utils
import dlib
import imutils
import math

class HeadPosition:
    def loadShapePredictor(self, shapePreditctorAlgorithmPath):
        print("[INFO] loading facial landmark predictor...")
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(shapePreditctorAlgorithmPath)
        (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
        self.nose1,self.nose2 = face_utils.FACIAL_LANDMARKS_IDXS["nose"]
        self.leftMouth,self.rightMouth= face_utils.FACIAL_LANDMARKS_IDXS["mouth"]
        self.jaw1,self.jaw2 = face_utils.FACIAL_LANDMARKS_IDXS["jaw"]

        print("[INFO] starting video stream thread...")

    def getFacialLandmarks(self, imageFrame):

        info = (0, 0)
        try:
            frame = imutils.resize(imageFrame, width=imageFrame.shape[1])
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            rects = self.detector(gray, 0)
            for rect in rects:

                shape = self.predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)
                #print(shape)
                leftEye = shape[self.lStart:self.lEnd][-3]
                rightEye = shape[self.rStart:self.rEnd][0]
                nose = shape[self.nose1:self.nose2][3]
                mouth = shape[self.leftMouth:self.rightMouth]
                jaw = shape[self.jaw1:self.jaw2]
                jaw = jaw[int(len(jaw)/2)]
                lMouth = mouth[0]
                rMouth = mouth[-4]
                return np.array([nose,jaw,leftEye,rightEye,lMouth,rMouth], dtype="double")

        except Exception as exp:
            print('failure in running the ear alogirthm due to:' + str(exp))
            raise exp
        return info

    def getHeadPosition(self,imageFrame):
        # 3D model points.
        model_points = np.array([
            (0.0, 0.0, 0.0),  # Nose tip
            (0.0, -330.0, -65.0),  # Chin
            (-225.0, 170.0, -135.0),  # Left eye left corner
            (225.0, 170.0, -135.0),  # Right eye right corne
            (-150.0, -150.0, -125.0),  # Left Mouth corner
            (150.0, -150.0, -125.0)  # Right mouth corner

        ])

        # Camera internals
        size = imageFrame.shape
        focal_length = size[1]
        center = (size[1] / 2, size[0] / 2)
        camera_matrix = np.array(
            [[focal_length, 0, center[0]],
             [0, focal_length, center[1]],
             [0, 0, 1]], dtype="double"
        )

        #get image landmarks

        image_points = self.getFacialLandmarks(imageFrame)

        dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion
        (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix,
                                                                      dist_coeffs,
                                                                      flags=cv2.SOLVEPNP_ITERATIVE)

        rot_mat = np.zeros((3, 3), np.float32)
        rot_mat, jacob = cv2.Rodrigues(rotation_vector.T, rot_mat)

        euler = self.rotationMatrixToEulerAngles(rot_mat)
        euler_angles = []
        for x in euler:
            euler_angles.append(x * 180 / math.pi)

        (nose_end_point2D, jacobian) = cv2.projectPoints(np.array([(0.0, 0.0, 1000.0)]), rotation_vector,
                                                         translation_vector,
                                                         camera_matrix, dist_coeffs)

        for p in image_points:
            cv2.circle(imageFrame, (int(p[0]), int(p[1])), 3, (0, 0, 255), -1)

        p1 = (int(image_points[0][0]), int(image_points[0][1]))
        p2 = (int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))

        return euler_angles,p1,p2

    # Checks if a matrix is a valid rotation matrix.
    def isRotationMatrix(self,R):
        Rt = np.transpose(R)
        shouldBeIdentity = np.dot(Rt, R)
        I = np.identity(3, dtype=R.dtype)
        n = np.linalg.norm(I - shouldBeIdentity)
        return n < 1e-6

    # Calculates rotation matrix to euler angles
    # The result is the same as MATLAB except the order
    # of the euler angles ( x and z are swapped ).
    def rotationMatrixToEulerAngles(self,R):
        assert (self.isRotationMatrix(R))

        sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

        singular = sy < 1e-6

        if not singular:
            x = math.atan2(R[2, 1], R[2, 2])
            y = math.atan2(-R[2, 0], sy)
            z = math.atan2(R[1, 0], R[0, 0])
        else:
            x = math.atan2(-R[1, 2], R[1, 1])
            y = math.atan2(-R[2, 0], sy)
            z = 0

        return np.array([x, y, z])


if __name__ == "__main__":

    headPos = HeadPosition()

    headPos.loadShapePredictor('../models/shape_predictor_68_face_landmarks.dat')

    angles,p1,p2 = headPos.getHeadPosition(cv2.imread("headPose.jpg"))

    print(angles)
    print(p1,p2)

