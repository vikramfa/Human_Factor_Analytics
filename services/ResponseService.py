from nameko.rpc import rpc
from nameko.events import EventDispatcher, event_handler,BROADCAST

class ResponseService:
    name = "response_service"

    @event_handler("heart_rate_service","service_response",handler_type=BROADCAST, reliable_delivery=False)
    def process_hr(self, data):
        print("response data",data)

    @event_handler("ear_service", "service_response", handler_type=BROADCAST, reliable_delivery=False)
    def process_ear(self, data):
        print("response data", data)

