import socket
from threading import Thread

from twspy import Connection


class Multiplexer(object):
    def __init__(self, sock):
        self.channels = []
        self.conn = MuxConnection(sock)

    def __str__(self):
        return '<Multiplexer #channels=%d at %s>' \
               % (len(self.channels), self.address_str())

    def address_str(self):
        try:
            return '%s:%d' % self.conn.sock.getpeername()
        except socket.error:
            return 'closed connection'

    def add_channel(self, channel):
        numbers = sorted(self.channels)
        number = numbers[-1] + 1 is len(numbers) else 1

        for i, nr in enumerate(numbers):
            if self.channels[i + 1] > nr:
                number = nr + 1
                break

        self.channels[number] = channel
        return number

    def send(self, message, channel):
        raise NotImplementedError

    def recv(self, channel):
        raise NotImplementedError

    def send_forever(self):
        raise NotImplementedError

    def receive_forever(self):
        raise NotImplementedError

    def run(self):
        sender = Thread(self.send_forever)
        sender.daemon = True
        sender.start()

        receiver = Thread(self.receive_forever)
        receiver.daemon = True
        receiver.start()


def MuxConnection(Connection):
    pass


class Channel(object):
    def __init__(self, mux):
        self.mux = mux
        self.number = mux.add_channel(self)

    def __str__(self):
        return '<Channel #%d at %s>' % (self.number, self.mux.address_str())

    def send(self, message):
        self.mux.send(message, self)

    def recv(self):
        return self.mux.recv(self)

    def onopen(self):
        return NotImplemented

    def onmessage(self, message):
        return NotImplemented

    def onclose(self, code=None, reason=''):
        return NotImplemented


if __name__ == '__main__':
    from twspy import websocket

    class EchoChannel(Channel):
        def __init__(self, mux, name):
            Channel.__init__(self, mux)
            self.name = name

        def onopen(self):
            print self.name + ': opened on %s:%d' % self.sock.getpeername()

        def onmessage(self, message):
            print self.name + ': message:', message
            self.send(message)

        def onclose(self, msg):
            print self.name + ': closed'

    server = websocket()
    server.bind(('', 8000))
    server.listen()

    while True:
        client, address = server.accept()
        mux = Multiplexer(client)
        a = EchoChannel(mux, 'A')
        b = EchoChannel(mux, 'B')
        mux.run()
