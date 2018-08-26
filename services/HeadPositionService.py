from nameko.events import EventDispatcher, event_handler,BROADCAST
import algorithms.headposition as hpos
from nameko.rpc import rpc,RpcProxy
import base64
import time
import cv2
import datetime
import numpy as np
from services.PersistService import MongoDao

class HeadPositionService:
    name = "head_position_service"
    dispatch = EventDispatcher()
    algorithm = hpos.HeadPosition()
    algorithm.loadShapePredictor('models/shape_predictor_68_face_landmarks.dat')

    publishDataService = RpcProxy("data_publish_service")

    @rpc
    def process_head_positon(self,image_data,clientId):
        date = datetime.datetime.now().isoformat()
        fileinfo = base64.b64decode(image_data[22:])
        imgNpArr = np.fromstring(fileinfo, np.ubyte)
        img_np = cv2.imdecode(imgNpArr, 1)
        height, width, numberFrames = img_np.shape
        imageSize = img_np.size

        img_np.resize(imageSize)

        nparr = img_np.reshape(height, width, numberFrames)

        angle, p1, p2 = self.algorithm.getHeadPosition(nparr)

        hposResponse = dict()
        hposResponse['serviceType'] = "HeadPosition"
        hposResponse['headPos'] = angle
        hposResponse["date"] = str(date)
        hposResponse["userId"] = clientId

        print(hposResponse)
        self.publishDataService.pushToQueue(hposResponse)
        MongoDao.write_to_mongo(hposResponse, "hpos_collection")

        return

    @event_handler("image_publish_service", "process_hpos")
    def process_hpos(self, properties):
        date = datetime.datetime.now().isoformat()
        # str_imag = properties.headers.get("imageName")
        img_size = int(properties.get("imgSize"))
        img_Height = int(properties.get("imgHeight"))
        img_Width = int(properties.get("imgWidth"))
        img_noPlanes = int(properties.get("imgNoOfPlanes"))
        clientId = properties.get("clientId")
        # print(properties.get("image")[22:])
        nparr = np.fromstring(base64.b64decode(properties.get("image")[22:]), np.ubyte)
        nparr = cv2.imdecode(nparr, 1)
        # print("nparr::", nparr, img_Height, img_noPlanes, img_size, img_Width)
        nparr.resize(img_size)

        nparr = nparr.reshape(img_Height, img_Width, img_noPlanes)

        angle,p1,p2 = self.algorithm.getHeadPosition(nparr)

        hposResponse = dict()
        hposResponse['serviceType'] = "HeadPosition"
        hposResponse['headPos'] = angle
        hposResponse["date"] = str(date)
        hposResponse["userId"] = clientId

        print(hposResponse)
        self.publishDataService.pushToQueue(hposResponse)
        MongoDao.write_to_mongo(hposResponse, "hpos_collection")