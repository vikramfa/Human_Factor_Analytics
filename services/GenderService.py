
from nameko.events import EventDispatcher, event_handler,BROADCAST
from algorithms.classifier import ImageClassifier
from nameko.rpc import RpcProxy
import base64
import numpy as np
import tensorflow as tf
import cv2
from services.PersistService import MongoDao
from nameko.rpc import rpc

class GenderService:
    name = "gender_service"
    dispatch = EventDispatcher()
    emotionPublishDataService = RpcProxy("emotion_data_publish_service")
    classifier = ImageClassifier("models/faces_graph.pb","models/faces_graphLabels.txt")

    @rpc
    def process_gender_detection(self,img_data,clientId):
        fileinfo = base64.b64decode(img_data[22:])
        imgNpArr = np.fromstring(fileinfo, np.ubyte)
        img_np = cv2.imdecode(imgNpArr, 1)
        height, width, numberFrames = img_np.shape
        imageSize = img_np.size

        img_np.resize(imageSize)

        nparr = img_np.reshape(height, width, numberFrames)

        answer, score = self.classifier.classifyImage(nparr, 1)

        genderResponse = dict()
        genderResponse['serviceType'] = "Gender"
        genderResponse['gender'] = answer
        genderResponse['confidence'] = score
        genderResponse["userId"] = clientId
        print(genderResponse)
        self.emotionPublishDataService.pushEmotionResponseToQueue(genderResponse)
        MongoDao.write_to_mongo(genderResponse, "gender_collection")




    @event_handler("image_publish_service", "process_gender")
    def process_gender(self, properties):
        img_size = int(properties.get("imgSize")),
        img_Height = int(properties.get("imgHeight"))
        img_Width = int(properties.get("imgWidth"))
        img_noPlanes = int(properties.get("imgNoOfPlanes"))
        clientId = properties.get("clientId")
        nparr = np.fromstring(base64.b64decode(properties.get("image")[22:]), np.ubyte)

        nparr = cv2.imdecode(nparr, 1)

        nparr.resize(img_size)

        nparr = nparr.reshape(img_Height, img_Width, img_noPlanes)

        answer,score = self.classifier.classifyImage(nparr,1)
        genderResponse = dict()
        genderResponse['serviceType'] = "Gender"
        genderResponse['gender'] = answer
        genderResponse['confidence'] = score
        genderResponse["userId"] = clientId
        print(genderResponse)
        self.emotionPublishDataService.pushEmotionResponseToQueue(genderResponse)
        MongoDao.write_to_mongo(genderResponse, "gender_collection")