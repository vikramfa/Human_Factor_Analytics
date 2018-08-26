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
hr_clients = []


credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)


connection = pika.BlockingConnection(parameters)
logging.info('Connected:localhost')
channel = connection.channel()

def threaded_hr_rmq():
    channel.queue_declare(queue="hr_response_queue")
    channel.queue_declare(queue="gen_response_queue")
    logging.info('consumer ready, on hr response_queue')
    channel.basic_consume(hr_callback, queue="hr_response_queue", no_ack=True)
    channel.start_consuming()


def disconnect_to_rabbitmq():
    channel.stop_consuming()
    connection.close()
    logging.info('Disconnected from Rabbitmq')

def hr_callback(ch, method, properties, body):
    logging.info("[x] Received %r" % (body,))
    # The messagge is brodcast to the connected clients
    if(json.loads(body)["serviceType"] == "HR"):
        for client in hr_clients:
            client.write_message(body)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class SocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self,origin):
        return True

    def open(self):
        logging.info('WebSocket opened')
        self.id = uuid.uuid4()
        hr_clients.append(self)
        #clients.append(self)


    def on_close(self):
        logging.info('WebSocket closed')
        hr_clients.remove(self)

    def on_message(self, message):
        print("client id hr::",str(self.id))
        #print(message)
        with ClusterRpcProxy(CONFIG) as rpc:
            #rpc.heart_rate_service.process_hr_execution(message, str(self.id))
            rpc.image_publish_service_2.pushToHRQueue(message, str(self.id))

application = tornado.web.Application([
    (r'/ws/hr', SocketHandler),
    (r"/", MainHandler)
])


def startTornado():
    application.listen(7778)
    logging.info('Started on port 7778')
    tornado.ioloop.IOLoop.instance().start()


def stopTornado():
    tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":

    logging.info('Starting thread Tornado')

    threadTornado = Thread(target=startTornado)
    threadTornado.start()

    logging.info('Starting thread RabbitMQ')

    threadHRQ = Thread(target = threaded_hr_rmq())
    threadHRQ.start()





