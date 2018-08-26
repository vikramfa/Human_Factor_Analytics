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
hp_clients =[]

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)


connection = pika.BlockingConnection(parameters)
logging.info('Connected:localhost')
channel = connection.channel()

def threaded_rmq():
    channel.queue_declare(queue="hp_response_queue")
    logging.info('consumer ready, on hp_response_queue')
    channel.basic_consume(consumer_callback, queue="hp_response_queue", no_ack=True)
    channel.start_consuming()

def disconnect_to_rabbitmq():
    channel.stop_consuming()
    connection.close()
    logging.info('Disconnected from Rabbitmq')



def consumer_callback(ch, method, properties, body):
    logging.info("[x] Received %r" % (body,))
    for itm in hp_clients:
        print(itm.id)
        itm.write_message(body)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


class HPSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self,origin):
        return True
    def open(self):
        logging.info('WebSocket opened')
        self.id = uuid.uuid4()
        hp_clients.append(self)


    def on_close(self):
        logging.info('WebSocket closed')
        hp_clients.remove(self)

    def on_message(self, message):
        print("client id ::",self.id)
        with ClusterRpcProxy(CONFIG) as rpc:
            rpc.head_position_service.process_head_positon(message,str(self.id))

application = tornado.web.Application([
    (r'/ws/hpos',HPSocketHandler),
    (r"/", MainHandler)
])


def startTornado():
    application.listen(7776)
    logging.info('Started on port 7776')
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





