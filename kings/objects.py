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

    def query(self, **kwargs):
        objs = []
        for obj in self.objects.values():
            for key, val in kwargs.items():
                if getattr(obj, key) != val:
                    break
            else:
                objs.append(obj)

        return objs


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

    def __repr__(self):
        return '{0}(**{1})'.format(self.__class__.__name__, self.__dict__)

class Player(Object):
    @property
    def short_desc(self):
        return self.oid

    def interpret(self, line):
        sep = " "
        verb, sep, rest = line.partition(sep)
        if verb == "ls":
            return repr(Db.instance().objects)
        elif verb == "look":
            return self.look(self.location)
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
                    return self.look(self.location)
        return "I don't know what {0} means".format(verb)

    def close(self):
        Db.instance().remove(self)

    def look(self, obj):
        output = [obj.long_desc]
        if obj.exits:
            exits = "Exits: {0}".format(", ".join(sorted(obj.exits.keys())))
        else:
            exits = "There are no obvious exists"
        output.append(exits)
        
        things = Db.instance().query(location_oid=self.location_oid)
        if things:
            output.extend([t.short_desc for t in things if t.oid != self.oid])

        return "\n".join(output)


class Location(Object):
    def __init__(self, exits=None, **kwargs):
        super(Location, self).__init__(**kwargs)
        self._exits = exits or {}

    @property
    def exits(self):
        return self._exits

