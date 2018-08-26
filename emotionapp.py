import tornado.ioloop
import tornado.web
import tornado.websocket
import pika
from threading import Thread
import logging
import base64
import uuid
import json
from nameko.standalone.rpc import ClusterRpcProxy

logging.basicConfig(level=logging.INFO)
CONFIG = {'AMQP_URI': "amqp://guest:guest@localhost"}

# web socket clients connected.
gen_clients=[]

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)


connection = pika.BlockingConnection(parameters)
logging.info('Connected:localhost')
channel = connection.channel()


def threaded_gen_rmq():
    channel.queue_declare(queue="gen_response_queue")
    logging.info('consumer ready, on gen response_queue')
    channel.basic_consume(gen_callback, queue="gen_response_queue", no_ack=True)
    channel.start_consuming()


def disconnect_to_rabbitmq():
    channel.stop_consuming()
    connection.close()
    logging.info('Disconnected from Rabbitmq')

def gen_callback(ch, method, properties, body):
    logging.info("[x] Received %r" % (body,))
    for itm in gen_clients:
        itm.write_message(body)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class EmotionSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self,origin):
        return True
    def open(self):
        logging.info('WebSocket opened')
        self.id = uuid.uuid4()
        gen_clients.append(self)


    def on_close(self):
        logging.info('WebSocket closed')
        gen_clients.remove(self)

    def on_message(self, message):
        print("client id ::",self.id)
        with ClusterRpcProxy(CONFIG) as rpc:
            rpc.emotion_service.process_emotion_detection(message,str(self.id))
            rpc.gender_service.process_gender_detection(message,str(self.id))


application = tornado.web.Application([
    (r'/ws/emotion',EmotionSocketHandler),
    (r"/", MainHandler)
])


def startTornado():
    application.listen(7779)
    logging.info('Started on port 7779')
    tornado.ioloop.IOLoop.instance().start()


def stopTornado():
    tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":

    logging.info('Starting thread Tornado')

    threadTornado = Thread(target=startTornado)
    threadTornado.start()

    logging.info('Starting thread RabbitMQ')
    threadHRQ = Thread(target = threaded_gen_rmq())
    threadHRQ.start()





