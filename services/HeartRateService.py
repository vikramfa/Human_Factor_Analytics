
import datetime
from nameko.events import EventDispatcher, event_handler,BROADCAST
from nameko.rpc import rpc,RpcProxy
import numpy as np
from algorithms.processors_noopenmdao import findFaceGetPulse
import base64
import time
import cv2
from cachetools import LRUCache
from services.PersistService import MongoDao


class HeartRateService:
    name = "heart_rate_service"
    factor = 1.2

    cache = LRUCache(maxsize=10)
    average_cache = LRUCache(maxsize=10)


    dispatch = EventDispatcher()
    publishDataService = RpcProxy("hr_data_publish_service")

    selected_cam = 0

    """@rpc
    def process_hr_execution(self,image_data,clientID):
        date = datetime.datetime.now().isoformat()

        if clientID in self.cache:
            print("foundClient::", clientID)
            algorithm = self.cache[clientID]
        else:
            print("creating new instance")
            algorithm = findFaceGetPulse(bpm_limits=[50, 160],
                                         data_spike_limit=2500.,
                                         face_detector_smoothness=10.)
            self.cache[clientID] = algorithm

        fileinfo = base64.b64decode(image_data[22:])
        imgNpArr = np.fromstring(fileinfo, np.ubyte)
        img_np = cv2.imdecode(imgNpArr, 1)
        height, width, numberFrames = img_np.shape
        imageSize = img_np.size

        img_np.resize(imageSize)

        nparr = img_np.reshape(height, width, numberFrames)

        algorithm.frame_in = nparr
        algorithm.run(self.selected_cam)
        avg_hr = 0
        hrResponse = dict()
        hrResponse['serviceType'] = "HR"
        if clientID in self.average_cache:
            prev_data = self.average_cache[clientID]
            if prev_data["count"] > 100:
                avg_hr = sum(prev_data["hr_data"]) / len(prev_data["hr_data"])
            else:
                print("count is::", prev_data["count"])
                prev_data["count"] = prev_data["count"] + 1
                prev_data["hr_data"].append(algorithm.bpm * 1.2)
                self.average_cache[clientID] = prev_data
        else:
            hr_data = []
            hr_data.append(algorithm.bpm * 1.2)
            count = 1
            datatoCache = {"hr_data": hr_data, "count": count}
            self.average_cache[clientID] = datatoCache

        hrResponse['heartRate'] = algorithm.bpm * 1.2
        hrResponse['time'] = int(time.time())
        hrResponse['averageHR'] = avg_hr
        hrResponse['date'] = str(date)
        hrResponse['userId'] = clientID
        print(hrResponse)
        self.publishDataService.pushHRResponseToQueue(hrResponse)
        MongoDao.write_to_mongo(hrResponse, "hr_collection")"""

    @event_handler("image_publish_service_2", "process_hr")
    def process_hr(self, properties):
        date = datetime.datetime.now().isoformat()
        clientID = properties.get("clientID")
        if clientID in self.cache:
            print("foundClient::",clientID)
            algorithm = self.cache[clientID]
        else:
            print("creating new instance")
            algorithm = findFaceGetPulse(bpm_limits=[50, 160],
                                         data_spike_limit=2500.,
                                         face_detector_smoothness=10.)
            self.cache[clientID] = algorithm


        img_size = int(properties.get("imgSize"))
        img_Height = int(properties.get("imgHeight"))
        img_Width = int(properties.get("imgWidth"))
        img_noPlanes = int(properties.get("imgNoOfPlanes"))


        nparr = np.fromstring(base64.b64decode(properties.get("image")[22:]), np.uint8)
        #print(nparr)

        nparr = cv2.imdecode(nparr, 1)

        #nparr.resize(img_size)
        print(img_size,img_Height,img_Width)

        nparr = nparr.reshape(img_Height, img_Width, img_noPlanes)

        #print(nparr)

        try:
            algorithm.frame_in = nparr
            algorithm.run(self.selected_cam)
        except Exception as exp:
            print(exp)
        avg_hr = 0
        hrResponse = dict()
        hrResponse['serviceType'] = "HR"
        if clientID in self.average_cache:
            prev_data = self.average_cache[clientID]
            if prev_data["count"] >50:
               avg_hr =  sum(prev_data["hr_data"])/len(prev_data["hr_data"])
            else:
                print("count is::",prev_data["count"])
                prev_data["count"] = prev_data["count"]+1
                prev_data["hr_data"].append(algorithm.bpm * self.factor)
                self.average_cache[clientID] = prev_data
        else:
            hr_data = []
            hr_data.append(algorithm.bpm * self.factor)
            count = 1
            datatoCache = {"hr_data":hr_data,"count":count}
            self.average_cache[clientID] =  datatoCache


        if avg_hr > 0:
            hrResponse['averageHR'] = abs(avg_hr - algorithm.bpm * self.factor)/avg_hr
        else:
            hrResponse["averageHR"] = avg_hr

        hrResponse['heartRate'] = algorithm.bpm * self.factor
        hrResponse['time'] = int(time.time())
        hrResponse['date'] = str(date)
        hrResponse['userId'] = clientID
        print(hrResponse)
        self.publishDataService.pushHRResponseToQueue(hrResponse)
        MongoDao.write_to_mongo(hrResponse,"hr_collection")
        #self.dispatch("service_response", hrResponse)