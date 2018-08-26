
from nameko.rpc import rpc,RpcProxy
from nameko.events import EventDispatcher, event_handler,BROADCAST
from algorithms.classifier import ImageClassifier
import numpy as np
import cv2
import base64
from services.PersistService import MongoDao

class EmotionService:
    name = "emotion_service"
    dispatch = EventDispatcher()
    emotionPublishDataService = RpcProxy("emotion_data_publish_service")
    classifier = ImageClassifier("models/faceEmotion_graph.pb", "models/faceEmotion_graphLabels.txt")

    @rpc
    def process_emotion_detection(self, img_data, clientId):
        fileinfo = base64.b64decode(img_data[22:])
        imgNpArr = np.fromstring(fileinfo, np.ubyte)
        img_np = cv2.imdecode(imgNpArr, 1)
        answer, score = self.classifier.classifyImage(img_np, 1)
        height, width, numberFrames = img_np.shape
        imageSize = img_np.size

        img_np.resize(imageSize)

        nparr = img_np.reshape(height, width, numberFrames)

        answer, score = self.classifier.classifyImage(nparr, 1)
        emotionResponse = dict()
        emotionResponse['serviceType'] = "emotion_detection"
        emotionResponse['emotion'] = answer
        emotionResponse['confidence'] = score
        emotionResponse["userId"] = clientId
        print(emotionResponse)
        self.emotionPublishDataService.pushEmotionResponseToQueue(emotionResponse)
        MongoDao.write_to_mongo(emotionResponse, "emotion_collection")



    @event_handler("image_publish_service", "process_emotion")
    def process_emotion(self, properties):
        img_size = int(properties.get("imgSize"))
        img_Height = int(properties.get("imgHeight"))
        img_Width = int(properties.get("imgWidth"))
        img_noPlanes = int(properties.get("imgNoOfPlanes"))
        clientId = properties.get("clientId")
        nparr = np.fromstring(base64.b64decode(properties.get("image")[22:]), np.ubyte)

        nparr = cv2.imdecode(nparr, 1)

        nparr.resize(img_size)

        nparr = nparr.reshape(img_Height, img_Width, img_noPlanes)
        answer,score = self.classifier.classifyImage(nparr, 1)
        emotionResponse = dict()
        emotionResponse['serviceType'] = "emotion_detection"
        emotionResponse['emotion'] = answer
        emotionResponse['confidence'] = score
        emotionResponse["userId"] = clientId
        print(emotionResponse)
        self.emotionPublishDataService.pushEmotionResponseToQueue(emotionResponse)
        MongoDao.write_to_mongo(emotionResponse, "emotion_collection")