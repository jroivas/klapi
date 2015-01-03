import zmq
import sys
import threading
import utils
import time

class ActionClient(threading.Thread):
    def __init__(self, sets):
        self.id = utils.generateID()
        self.port = 5555
        self.host = 'localhost'
        if 'backend_port' in sets:
            self.port = sets['backend_port']
        if 'backend_host' in sets:
            self.host = sets['backend_host']
        self.running = False
        self.queue = []
        self.callbacks = {}
        self.queue_mutex = threading.Lock()
        threading.Thread.__init__ (self)

    def createConnection(self):
        context = zmq.Context()

        socket = context.socket(zmq.DEALER)

        identity = u'client-%s' % self.id
        socket.identity = identity.encode('ascii')
        socket.connect('tcp://%s:%s' % (self.host, self.port))

        return (context, socket)

    def getResults(self, poll, socket):
        sockets = dict(poll.poll(1000))
        if socket in sockets:
            res = socket.recv_json()
            if 'id' in res:
                if res['id'] in self.callbacks:
                    with self.queue_mutex:
                        self.callbacks[res['id']](res)
                        del self.callbacks[res['id']]

    def handle(self, poll, socket):
        self.running = True
        while self.running:
            if not self.queue:
                self.getResults(poll, socket)
                time.sleep(0.01)
                continue

            with self.queue_mutex:
                (data, callback) = self.queue.pop(0)

                data['id'] = utils.generateID()
                self.callbacks[data['id']] = callback

            socket.send_json(data)

            self.getResults(poll, socket)

    def run(self):
        (context, socket) = self.createConnection()

        poll = zmq.Poller()
        poll.register(socket, zmq.POLLIN)

        self.handle(poll, socket)

        socket.close()
        context.term()

    def disconnect(self):
        self.running = False

    def sendAction(self, action, callback):
        with self.queue_mutex:
            self.queue.append((action, callback))
