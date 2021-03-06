import socket
import time
import select

from mGesf.exceptions import LeapPortTimeoutError


class LeapInterface:
    listensocket = socket.socket()  # Creates an instance of socket
    Port = 8000
    maxConnections = 999
    IP = socket.gethostname()
    clientsocket = socket
    running = False

    def __init__(self):
        pass

    def connect_sensor(self):
        # connect to the sensor
        self._set_up_local_network_port()

    def start_sensor(self):
        # tell the sensor to start sending frames
        self._send_start_command()

    def process_frame(self):
        # return a frame of the sensor
        # this function should return NONE WITHOUT blocking if a frame is not complete
        # return random.random()
        frame = self._get_frame_from_network_port()
        print(frame)
        frame = [float(x) for x in frame.split(' ')]
        return frame, None  # TODO add the leap camera image

    def stop_sensor(self):
        self._send_stop_command()

    def _set_up_local_network_port(self):
        self.listensocket.bind(('', self.Port))
        self.listensocket.listen(self.maxConnections)
        print("Server started at " + self.IP + " on port " + str(self.Port))
        self.clientsocket = self.listensocket.accept()

        # need to get above working properly
        print("New connnection made")

    def _send_start_command(self):
        self.running = True

    def _get_frame_from_network_port(self):
        # if self.running:
        #     return self.clientsocket[0].recv(1024).decode()  # Gets the incoming message
        if self.running:
            timeout = 0.001
            self.clientsocket[0].setblocking(False)
            ready = select.select([self.clientsocket[0]], [], [], timeout)
            if ready[0]:
                return self.clientsocket[0].recv(1024).decode()  # Gets the incoming message
            else:
                return '0.0 0.0 0.0 0.0 0.0'

    def _send_stop_command(self):
        self.running = False


def run_test():
    while 1:
        frame = leap_interface.process_frame()
        print(frame)
        time.sleep(1e-3)


if __name__ == "__main__":
    leap_interface = LeapInterface()
    leap_interface.connect_sensor()
    leap_interface.start_sensor()
    run_test()
