
from nameko.rpc import rpc
import numpy as np
import cv2
import base64
from nameko.events import EventDispatcher
import json

class ImagePublishService2:
    name = "image_publish_service_2"
    dispatch = EventDispatcher()
    @rpc
    def pushToHRQueue(self, fileinfo1,clientID):
        try:
            fileinfo = base64.b64decode(fileinfo1[22:])
            imgNpArr = np.fromstring(fileinfo, np.ubyte)

            #print(imgNpArr.shape)
            img_np = cv2.imdecode(imgNpArr, 1)
            #print(img_np)
            height, width, numberFrames = img_np.shape
            imageSize = img_np.size
            dataObject = {'clientID':clientID,'imageName': 'xyz.png', 'imgSize': str(imageSize),
                       'imgHeight': str(height), 'imgWidth': str(width),
                       'imgNoOfPlanes': str(numberFrames),'image':fileinfo1}

            self.dispatch("process_hr", dataObject)

        except Exception as exp:
            print('Exception occured during Image Capture due to ' + str(exp))
            raise exp

