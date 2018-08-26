import pika
from nameko.rpc import rpc
import json

class EmotionDataPublishService:

    name = "emotion_data_publish_service"

    def __init__(self):
        self.rabbitHostAddr = "localhost"
        self.rabbitQueueName = "gen_response_queue"
        self.createProducer()

    def createProducer(self):
        credentials = pika.PlainCredentials('guest', 'guest')
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(self.rabbitHostAddr, 5672, '/', credentials))
        self.channel = self.connection.channel()

    def closeConnection(self):
        print(" [x] Connection Close")
        self.connection.close()

    @rpc
    def pushEmotionResponseToQueue(self, responseData):
        try:
            self.channel.basic_publish(exchange='',
                                       routing_key=self.rabbitQueueName,
                                       # body=imageName,
                                       body=json.dumps(responseData),
                                       properties=pika.BasicProperties(
                                           delivery_mode=2
                                       ))
            print(" [x] Sent file" )
        except Exception as exp:
            print('Exception occured during Image Capture due to ' + str(exp))
            self.closeConnection()
            raise exp
        finally:
            self.closeConnection()