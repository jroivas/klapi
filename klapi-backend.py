#!flask/bin/python
import zmq
import sys
import threading
import json
import settings

class KlapiServer(threading.Thread):
    def __init__(self, sets):
        threading.Thread.__init__ (self)

        self.port = 5555
        self.backend_name = 'klapi_backend'
        self.worker_count = 5

        if 'backend_port' in sets:
            self.port = sets['backend_port']
        if 'backend_name' in sets:
            self.backend_name = sets['backend_name']
        if 'backend_workers' in sets:
            self.worker_count = sets['backend_workers']

        self.running = False

    def _init_connection(self):
        context = zmq.Context()
        server = context.socket(zmq.ROUTER)
        server.bind('tcp://*:%s' % (self.port))

        backend = context.socket(zmq.DEALER)
        backend.bind('inproc://%s' % (self.backend_name))

        return (context, server, backend)

    def _deinit_connection(self, context, server, backend):
        server.close()
        backend.close()
        context.term()

    def launch_workers(self, context):
        workers = []
        for _ in range(self.worker_count):
            worker = KlapiWorker(context, self.backend_name)
            worker.start()
            workers.append(worker)

        return workers

    def init_poller(self, server, backend):
        poll = zmq.Poller()
        poll.register(server, zmq.POLLIN)
        poll.register(backend, zmq.POLLIN)

        return poll

    def serve(self, server, backend):
        self.running = True
        poll = self.init_poller(server, backend)

        print ('Klapi-backend on port %s (%s workers), worker IPC on "%s"' % (
            self.port, self.worker_count, self.backend_name))

        while self.running:
            sockets = dict(poll.poll())

            # Work as a simple proxy
            if server in sockets:
                data = server.recv_multipart
                backend.send_multipart(data)
            if backend in sockets:
                data = backend.recv_multipart
                server.send_multipart(data)

    def run(self):
        (context, server, backend) = self._init_connection()
        workers = self.launch_workers(context)

        self.serve(server, backend)

        self._deinit_connection(context, server, backend)

class KlapiWorker(threading.Thread):
    def __init__(self, context, backend_name):
        threading.Thread.__init__ (self)
        self.context = context
        self.backend_name = backend_name
        self.running = False

    def run(self):
        worker = self.context.socket(zmq.DEALER)
        worker.connect('inproc://%s' % (self.backend_name))
        self.running = True

        while self.running:
            ident, msg  = worker.recv_multipart()
            msg_json = json.loads(msg)

            result = self.handle(msg_json)
            if 'terminate' in result:
                self.running = False

            new_msg = json.dumps(result)
            worker.send_multipart([ident, new_msg])

        worker.close()

    def handle(self, msg):
        # TODO: Handle dict message, send back as dict
        return msg

if __name__ == '__main__':
    server = KlapiServer(settings.settings())
    server.start()
    server.join()
