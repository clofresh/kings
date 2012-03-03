import os
from glob import glob

import yaml

from .common import *

class ObjectNotFound(Exception): pass
class LocationNotFound(ObjectNotFound): pass

def from_yaml(filename):
    data = yaml.load(open(filename))
    cls = globals()[data['type']]
    return cls.init(**data)

class Db(object):
    _instance = None

    @classmethod
    def init(cls, config):
        obj_db = cls()
        cls._instance = obj_db
        content_path = config.get('kings', 'content_path')
        files = glob(os.path.join(content_path, '*.yaml'))
        for filename in files:
            from_yaml(filename)
        return obj_db

    @classmethod
    def instance(cls):
        assert cls._instance
        return cls._instance

    def __init__(self, objects=None):
        self.objects = objects or {}

    def __contains__(self, oid):
        return oid in self.objects

    def add(self, obj):
        assert obj.oid
        self.objects[obj.oid] = obj

    def remove(self, obj):
        try:
            del self.objects[obj.oid]
        except KeyError:
            raise ObjectNotFound(obj.oid)

    def get(self, oid):
        try:
            return self.objects[oid]
        except KeyError:
            raise ObjectNotFound(oid)

class Object(object):
    @classmethod
    def init(cls, **kwargs):
        obj = cls(**kwargs)
        Db.instance().add(obj)
        return obj

    def __init__(self, oid=None, short_desc=None, long_desc=None, location_oid=None, **kwargs):
        self._oid = oid
        self._short_desc = short_desc
        self._long_desc = long_desc
        self._location_oid = location_oid

    @property
    def oid(self):
        return self._oid

    @property
    def long_desc(self):
        return self._long_desc

    @property
    def short_desc(self):
        return self._short_desc

    @property
    def location_oid(self):
        return self._location_oid

    @property
    def location(self):
        if self.location_oid:
            try:
                return Db.instance().get(self.location_oid)
            except ObjectNotFound:
                log.warn("No location found for oid {0}".format(self.location_oid))
                return None
        else:
            return None

    def move(self, oid):
        if oid in Db.instance():
            self._location_oid = oid
        else:
            raise LocationNotFound(oid)

class Player(Object):
    def interpret(self, line):
        sep = " "
        verb, sep, rest = line.partition(sep)
        if verb == "ls":
            return repr(Db.instance().objects)
        elif verb == "look":
            return self.location.long_desc
        elif verb == "exit":
            self.running = False
            return "Goodbye"
        else:
            room = self.location
            exits = room.exits
            if verb in exits:
                try:
                    self.move(exits[verb])
                except LocationNotFound:
                    return "Oops, location not found"
                else:
                    return self.location.long_desc
        return "I don't know what {0} means".format(verb)

    def run(self, conn):
        self.running = True
        try:
            while self.running:
                line = conn.readline()
                if line:
                    output = self.interpret(line.strip())
                    conn.write(output + "\n% ")
                    conn.flush()
                    log.info("echoed %r" % line)
                else:
                    self.running = False
        finally:
            log.info("client disconnected")
            Db.instance().remove(self)

class Location(Object):
    def __init__(self, exits=None, **kwargs):
        super(Location, self).__init__(**kwargs)
        self._exits = exits or {}

    @property
    def long_desc(self):
        if self._exits:
            exits = "Exits: {0}".format(", ".join(sorted(self._exits.keys())))
        else:
            exits = "There are no obvious exists"
        return "{0}\n{1}".format(self._long_desc, exits)

    @property
    def exits(self):
        return self._exits

