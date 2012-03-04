import os
from copy import deepcopy
from glob import glob

import yaml

from .common import *

class ObjectNotFound(Exception): pass
class LocationNotFound(ObjectNotFound): pass


class Db(object):
    _instance = None

    @classmethod
    def init(cls, config):
        obj_db = cls(config.get('kings', 'content_path'))
        cls._instance = obj_db
        obj_db.reload()
        return obj_db

    @classmethod
    def instance(cls):
        assert cls._instance
        return cls._instance

    def __init__(self, content_path, objects=None):
        self.content_path = content_path
        self.objects = objects or {}

    def __contains__(self, oid):
        return oid in self.objects

    def reload(self):
        for filename in glob(os.path.join(self.content_path, '*.yaml')):
            self.from_yaml(filename=filename)

    def from_yaml(self, oid=None, filename=None):
        assert oid or filename and not (oid and filename)
        if oid:
            filename = "{0}/{1}.yaml".format(self.content_path, oid)
        data = yaml.load(open(filename))
        cls = globals()[data['type']]
        return cls.init(**data)

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
    instance_counter = 0

    @classmethod
    def init(cls, **kwargs):
        obj = cls(**kwargs)
        Db.instance().add(obj)
        return obj

    @classmethod
    def clone(cls, oid):
        db = Db.instance()
        try:
            prototype = db.get(oid)
        except ObjectNotFound:
            prototype = db.from_yaml(oid=oid)
        cloned = deepcopy(prototype)

        # Make sure that the cone has a unique oid
        cls.instance_counter += 1
        instance_num = cls.instance_counter
        cloned._oid = "{0}:{1}".format(cloned.oid, instance_num)

        db.add(cloned)
        return cloned

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

    def location(self):
        if self.location_oid:
            try:
                return Db.instance().get(self.location_oid)
            except ObjectNotFound:
                log.warn("No location found for oid {0}".format(self.location_oid))
                return None
        else:
            return None

    def move_to(self, target_oid):
        if target_oid in Db.instance():
            self._location_oid = target_oid
        else:
            raise LocationNotFound(target_oid)

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
            if rest:
                try:
                    return self.look(Db.instance().get(rest))
                except ObjectNotFound:
                    return "There's no \"{0}\" here.".format(rest)
            else:
                return self.look(self.location())
        elif verb == "spawn":
            thing = Npc.clone('mouse')
            thing._location_oid = self.location_oid
            return ""
        elif verb == "exit":
            self.running = False
            return "Goodbye"
        else:
            room = self.location()
            exits = room.exits
            if verb in exits:
                try:
                    self.move_to(exits[verb])
                except LocationNotFound:
                    return "Oops, location not found"
                else:
                    return self.look(self.location())
        return "I don't know what {0} means".format(verb)

    def close(self):
        Db.instance().remove(self)

    def look(self, obj):
        output = [obj.long_desc]
        if hasattr(obj, "exits"):
            if obj.exits:
                exits = "Exits: {0}".format(", ".join(sorted(obj.exits.keys())))
            else:
                exits = "There are no obvious exists"
            output.append(exits)

            things = Db.instance().query(location_oid=self.location_oid)
            if things:
                output.extend([t.short_desc for t in things if t.oid != self.oid])

        return "\n".join(output)

class Npc(Object):
    pass

class Location(Object):
    def __init__(self, exits=None, npcs=None, **kwargs):
        super(Location, self).__init__(**kwargs)
        self._exits = exits or {}
        for npc_oid in npcs or []:
            cloned = Npc.clone(npc_oid)
            cloned._location_oid = self.oid

    @property
    def exits(self):
        return self._exits

