from .objects import Db, Player, LookAction
import gevent.queue
import gevent.socket
from gevent.server import StreamServer

from .common import *

class MUD(object):
    @classmethod
    def init(cls, config):
        cls.db = Db.init(config)
        return cls(config.get('kings', 'bind_address'), config.getint('kings', 'port'))

    def __init__(self, address, port):
        self.address = address
        self.port = port

    def run(self):
        log.info('Listening at {0}:{1}'.format(self.address, self.port))
        self.server = StreamServer((self.address, self.port), connect)
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            log.info("Received KeyboardInterrupt, exiting")

class NoInput(Exception): pass

# Runs in its own greenlet
def connect(socket, address):
    log.info('New connection from %s:%s' % address)
    conn = socket.makefile()
    conn.write("User: ")
    conn.flush()
    username = conn.readline().strip()

    # FIXME: add auth
    player = Player.init(oid=username, location_oid="town_square")
    try:
        while player.running:
            action = None
            try:
                gevent.socket.wait_read(conn.fileno(), timeout=0.01, timeout_exc=NoInput())
            except NoInput:
                pass
            else:
                line = conn.readline().strip()
                if line:
                    action = player.interpret(line)

            if not action:
                try:
                    action = player.actions.get(block=True, timeout=0.01)
                except gevent.queue.Empty:
                    pass

            if action:
                # If it's just a string, print it out
                func = getattr(action, 'execute', lambda: str(action))
                message = func()
                conn.write(message + player.prompt)
                conn.flush()

    finally:
        log.info("client disconnected")
        player.close()

