import json
import logging

import datatypes

logger = logging.getLogger('mm.mongo')


class MongoMeta(type):

    def __init__(self, name, bases, attrs):
        super(MongoMeta, self).__init__(name, bases, attrs)

        fields = set()
        for base in bases:
            if getattr(base, '_FIELDS', None):
                fields.update(base._FIELDS)
        for attr, t in attrs.iteritems():
            if isinstance(t, datatypes.DataType):
                fields.add(attr)
                t.set_default_map_key(attr)

        logger.debug('Fields for type {0}: {1}'.format(name, fields))
        self._FIELDS = tuple(fields)


class MongoObject(object):

    __metaclass__ = MongoMeta

    FIELDS = tuple()

    def __init__(self, *args, **kwargs):
        super(MongoObject, self).__init__(*args, **kwargs)
        self._dirty = False
        self._data = {}

    def make_dirty(self):
        self._dirty = True

    @classmethod
    def new(cls, **kwargs):
        obj = cls()
        for field, val in kwargs.iteritems():
            try:
                setattr(obj, field, val)
            except TypeError as e:
                raise TypeError('Failed to load field {0}: {1}'.format(field, e))
        obj.make_dirty()
        return obj

    def save(self):
        if not self._dirty:
            logger.debug('Object with id {0} has no _dirty flag set'.format(self.id))
            return

        res = self.collection.update({'id': self.id}, self.dump(), upsert=True)
        if res['ok'] != 1:
            logger.error('Unexpected mongo response: {0}, saving object {1}'.format(res, self.dump()))
            raise RuntimeError('Mongo operation result: {0}'.format(res['ok']))
        self._dirty = False

    def dump(self):
        res = {}
        for field in self._FIELDS:
            try:
                item = getattr(self, field)
            except AttributeError:
                logger.error('Failed to dump field {0}, job id {1}'.format(field, self.id))
                raise
            if isinstance(item, datatypes.DataType):
                item = item.dump(self)
            res[field] = item
        return res

    def load(self, data):
        for field in self._FIELDS:
            try:
                setattr(self, field, data.get(field, None))
            except TypeError as e:
                raise TypeError('Failed to load field {0}: {1}'.format(field, e))
        self._dirty = False
