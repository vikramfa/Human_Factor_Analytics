import tornado.ioloop
import tornado.web
import tornado.websocket
import pika
from threading import Thread
import logging
import base64
import uuid
import json
import urllib
from nameko.standalone.rpc import ClusterRpcProxy
from services.PersistService import MongoDao

logging.basicConfig(level=logging.INFO)
CONFIG = {'AMQP_URI': "amqp://guest:guest@localhost"}

# web socket clients connected.
ear_clients =[]

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)


connection = pika.BlockingConnection(parameters)
logging.info('Connected:localhost')
channel = connection.channel()

def threaded_rmq():
    channel.queue_declare(queue="response_queue")
    logging.info('consumer ready, on response_queue')
    channel.basic_consume(consumer_callback, queue="response_queue", no_ack=True)
    channel.start_consuming()

def disconnect_to_rabbitmq():
    channel.stop_consuming()
    connection.close()
    logging.info('Disconnected from Rabbitmq')



def consumer_callback(ch, method, properties, body):
    logging.info("[x] Received %r" % (body,))
    for itm in ear_clients:
        print(itm.id)
        itm.write_message(body)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

    def check_origin(self, origin):
        return True

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def post(self):
        try:
            print("inside here")
            print(dict(json.loads(self.request.body)))
            user_dict = dict(json.loads(self.request.body))
            user_dict["clientId"] = uuid.uuid4()
            MongoDao.write_to_mongo(user_dict, "user_collection")
            self.write({"clientId":str(user_dict["clientId"])})
        except Exception as ex:
            print(ex)
            self.write({"error":"an error occured during processing"})

class EARSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self,origin):
        return True
    def open(self):
        logging.info('WebSocket opened')
        print(self.get_arguments("userid")[0])
        self.id = uuid.uuid4()
        ear_clients.append(self)


    def on_close(self):
        logging.info('WebSocket closed')
        ear_clients.remove(self)

    def on_message(self, message):
        print("client id ::",self.id)
        with ClusterRpcProxy(CONFIG) as rpc:
            rpc.ear_service.process_ear_data(message,str(self.id))

application = tornado.web.Application([
    (r'/ws/ear',EARSocketHandler),
    (r"/signup", MainHandler)
])


def startTornado():
    application.listen(7777)
    logging.info('Started on port 7777')
    tornado.ioloop.IOLoop.instance().start()


def stopTornado():
    tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":

    logging.info('Starting thread Tornado')

    threadTornado = Thread(target=startTornado)
    threadTornado.start()

    logging.info('Starting thread RabbitMQ')
    threadRMQ = Thread(target=threaded_rmq)
    threadRMQ.start()





