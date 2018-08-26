
from nameko.events import EventDispatcher, event_handler,BROADCAST
from nameko.rpc import rpc,RpcProxy
import datetime
import numpy as np
import algorithms.ear as ea
import base64
import time
import cv2
from cachetools import LRUCache
from services.PersistService import MongoDao

class EARService:
    name = "ear_service"
    dispatch = EventDispatcher()
    algorithm = ea.EarAlogirthm()
    algorithm.loadShapePredictor('models/shape_predictor_68_face_landmarks.dat')
    average_cache = LRUCache(maxsize=10)

    publishDataService = RpcProxy("data_publish_service")


    """def __init__(self):
        self.algorithm = ea.EarAlogirthm()
        self.algorithm.loadShapePredictor('models/shape_predictor_68_face_landmarks.dat')"""

    @rpc
    def process_ear_data(self,image_data,clientId):
        fileinfo = base64.b64decode(image_data[22:])
        imgNpArr = np.fromstring(fileinfo, np.ubyte)
        img_np = cv2.imdecode(imgNpArr, 1)
        height, width, numberFrames = img_np.shape
        imageSize = img_np.size

        img_np.resize(imageSize)

        nparr = img_np.reshape(height, width, numberFrames)

        blinksTotal, earRatio = self.algorithm.shapeFilterAlgorithm(nparr)
        date = datetime.datetime.now().isoformat()
        #print(blinksTotal, earRatio, date)
        earResponse = dict()
        avg_ear = 0
        earResponse['serviceType'] = "EAR"
        if clientId in self.average_cache:
            prev_data = self.average_cache[clientId]
            if prev_data["count"] > 50:
                avg_ear = sum(prev_data["ear_data"]) / len(prev_data["ear_data"])
            else:
                print("count is::", prev_data["count"])
                prev_data["count"] = prev_data["count"] + 1
                prev_data["ear_data"].append(earRatio)
                self.average_cache[clientId] = prev_data
        else:
            ear_data = []
            ear_data.append(earRatio)
            count = 1
            datatoCache = {"ear_data": ear_data, "count": count}
            self.average_cache[clientId] = datatoCache
        if avg_ear > 0:
            earResponse["averageEar"] = abs((avg_ear-earRatio))/avg_ear
        else:
            earResponse["averageEar"] = avg_ear
        earResponse['earRatio'] = earRatio
        earResponse['blinks'] = blinksTotal
        earResponse['time'] = int(time.time())
        earResponse["date"] = str(date)
        earResponse["userId"] = clientId
        print(earResponse)
        self.publishDataService.pushToQueue(earResponse)
        MongoDao.write_to_mongo(earResponse, "ear_collection")

    @event_handler("image_publish_service", "process_ear")
    def process_ear(self, properties):
        print("processing ear")
        date = datetime.datetime.now().isoformat()
        # str_imag = properties.headers.get("imageName")
        img_size = int(properties.get("imgSize"))
        img_Height = int(properties.get("imgHeight"))
        img_Width = int(properties.get("imgWidth"))
        img_noPlanes = int(properties.get("imgNoOfPlanes"))
        clientId = str(properties.get("clientId"))
        #print(properties.get("image")[22:])
        nparr = np.fromstring(base64.b64decode(properties.get("image")[22:]), np.ubyte)
        nparr = cv2.imdecode(nparr, 1)
        #print("nparr::", nparr, img_Height, img_noPlanes, img_size, img_Width)
        nparr.resize(img_size)

        nparr = nparr.reshape(img_Height, img_Width, img_noPlanes)
        blinksTotal, earRatio = self.algorithm.shapeFilterAlgorithm(nparr)

        print(blinksTotal, earRatio, date)
        earResponse = dict()
        avg_ear = 0
        earResponse['serviceType'] = "EAR"
        if clientId in self.average_cache:
            prev_data = self.average_cache[clientId]
            print("counter is ::",prev_data["count"])
            if prev_data["count"] > 50:
                print("counter reached")
                avg_ear = sum(prev_data["ear_data"]) / len(prev_data["ear_data"])
            else:
                #print("count is::", prev_data["count"])
                prev_data["count"] = prev_data["count"] + 1
                prev_data["ear_data"].append(earRatio)
                self.average_cache[clientId] = prev_data
        else:
            ear_data = []
            ear_data.append(earRatio)
            count = 1
            datatoCache = {"ear_data": ear_data, "count": count}
            self.average_cache[clientId] = datatoCache
        earResponse['earRatio'] = earRatio
        earResponse["averageEar"] = avg_ear
        earResponse['blinks'] = blinksTotal
        earResponse['time'] = int(time.time())
        earResponse["date"] = str(date)
        earResponse["userId"] = clientId
        self.publishDataService.pushToQueue(earResponse)
        MongoDao.write_to_mongo(earResponse,"ear_collection")
        #self.dispatch("service_response", earResponse)
