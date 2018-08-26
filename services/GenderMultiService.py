from nameko.events import EventDispatcher, event_handler,BROADCAST

from nameko.rpc import RpcProxy
import cv2
import dlib
import numpy as np
import base64
import numpy as np
import cv2
from services.PersistService import MongoDao
from nameko.rpc import rpc
from algorithms.wide_resnet import WideResNet
import datetime

class GenderMultiService:
    name = "gender_multi_service"
    dispatch = EventDispatcher()
    emotionPublishDataService = RpcProxy("emotion_data_publish_service")
    weight_file = "/models/weights.18-4.06.hdf5"

    # for face detection
    detector = dlib.get_frontal_face_detector()

    # load model and weights
    img_size = 64
    model = WideResNet(img_size, depth=16, k=8)()
    model.load_weights(weight_file)

    @rpc
    def detect_gender(self,image_data):
        img = base64.b64decode(image_data[22:])
        imgNpArr = np.fromstring(img, np.ubyte)
        img_np = cv2.imdecode(imgNpArr, 1)
        input_img = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        img_h, img_w, _ = np.shape(input_img)

        # detect faces using dlib detector
        detected = self.detector(input_img, 1)
        faces = np.empty((len(detected), self.img_size, self.img_size, 3))

        for i, d in enumerate(detected):
            x1, y1, x2, y2, w, h = d.left(), d.top(), d.right() + 1, d.bottom() + 1, d.width(), d.height()
            xw1 = max(int(x1 - 0.4 * w), 0)
            yw1 = max(int(y1 - 0.4 * h), 0)
            xw2 = min(int(x2 + 0.4 * w), img_w - 1)
            yw2 = min(int(y2 + 0.4 * h), img_h - 1)
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            # cv2.rectangle(img, (xw1, yw1), (xw2, yw2), (255, 0, 0), 2)
            faces[i, :, :, :] = cv2.resize(img[yw1:yw2 + 1, xw1:xw2 + 1, :], (self.img_size, self.img_size))

        if len(detected) > 0:
            # predict ages and genders of the detected faces
            results = self.model.predict(faces)
            predicted_genders = results[0]
            ages = np.arange(0, 101).reshape(101, 1)
            predicted_ages = results[1].dot(ages).flatten()
            print(predicted_genders)
            print(predicted_ages)
            date = datetime.datetime.now().isoformat()
            return predicted_genders
