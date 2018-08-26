
from nameko.rpc import rpc
import numpy as np
import cv2
import base64
from nameko.events import EventDispatcher
import json

class ImagePublishService:
    name = "image_publish_service"
    dispatch = EventDispatcher()
    @rpc
    def pushToQueue(self, fileinfo1,clientId):
        try:
            fileinfo = base64.b64decode(fileinfo1[22:])
            imgNpArr = np.fromstring(fileinfo, np.ubyte)
            #print(imgNpArr.shape)
            img_np = cv2.imdecode(imgNpArr, 1)
            height, width, numberFrames = img_np.shape
            imageSize = img_np.size
            dataObject = {'clientId':clientId,'imageName': 'xyz.png', 'imgSize': str(imageSize),
                       'imgHeight': str(height), 'imgWidth': str(width),
                       'imgNoOfPlanes': str(numberFrames),'image':fileinfo1}

            #self.dispatch("process_hr", dataObject)
            self.dispatch("process_ear", dataObject)
            self.dispatch("process_gender",dataObject)
            self.dispatch("process_emotion", dataObject)
            #self.dispatch("process_hpos", dataObject)

        except Exception as exp:
            print('Exception occured during Image Capture due to ' + str(exp))
            raise exp

