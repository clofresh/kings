from .objects import Db, Player
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
        self.server = StreamServer((self.address, self.port), self.connect)
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            log.info("Received KeyboardInterrupt, exiting")

    def connect(self, socket, address):
        log.info('New connection from %s:%s' % address)
        player = Player.init(oid='carlo', location_oid='town_square')
        player.run(socket.makefile())
