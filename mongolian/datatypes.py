import functools
import logging
import operator
import uuid

from .condition import Condition, SimpleCondition, NAryCondition


logger = logging.getLogger('mm.mongo')


class DataType(object):

    BASETYPE = object

    def __init__(self, map_key=None):
        self._map_key = map_key

    def set_default_map_key(self, map_key):
        if self._map_key is None:
            self._map_key = map_key

    def set(self, instance, value):
        if not isinstance(value, self.BASETYPE) and value is not None:
            raise TypeError("Value has type '{0}' instead of '{1}'".format(
                type(value).__name__, self.BASETYPE.__name__))
        instance._data[self._map_key] = value

    def __set__(self, instance, value):
        self.set(instance, value)
        logger.debug('Setting value {0} of {1} to instance {2}'.format(value, self, instance))
        instance.make_dirty()

    def __get__(self, instance, owner):
        return DataAccessor(instance, self)

    # def dump(self, instance):
    #     return self._data

    def __repr__(self):
        return '<{0} field, _map_key: {1}>'.format(
            type(self).__name__, self._map_key)


def type_checking(f):
    @functools.wraps(f)
    def wrapper(self, other):
        assert isinstance(other, self.field.BASETYPE), "Type mismatch, "\
            "field {0} has type {1}, operand's type is {2}".format(
                self._map_key, self.field.BASETYPE.__name__, type(other).__name__)
        return f(self, other)
    return wrapper


class DataAccessor(object):
    def __init__(self, instance, field):
        self.field = field
        self.instance = instance

    @property
    def _value(self):
        return self.instance._data.get(self._map_key, None)

    @property
    def _map_key(self):
        return self.field._map_key

    def __getitem__(self, key):
        value = self._value.__getitem__(key)
        if isinstance(value, DataType):
            return value.__get__(self.instance, None)
        else:
            return value

    def __setitem__(self, key, value):
        # support for indexed datatypes (e.g. dict)
        self.instance.make_dirty()
        if isinstance(self._value[key], DataType):
            return self._value[key].__set__(self.instance, value)
        else:
            return self._value.__setitem__(key, value)

    def __delitem__(self, key):
        assert self.owner
        self.owner.make_dirty()
        del self.value[key]

    def __eq__(self, other):
        if isinstance(other, DataAccessor):
            return self.field._map_key == other.field._map_key
        assert isinstance(other, self.field.BASETYPE), "Type mismatch, "\
            "field {0} has type {1}, operand's type is {2}".format(
                self._map_key, self.field.BASETYPE.__name__, type(other).__name__)
        return SimpleCondition(self, operator.__eq__, other)

    @type_checking
    def __ne__(self, other):
        return SimpleCondition(self, operator.__ne__, other)

    @type_checking
    def __ge__(self, other):
        return SimpleCondition(self, operator.__ge__, other)

    @type_checking
    def __gt__(self, other):
        return SimpleCondition(self, operator.__gt__, other)

    @type_checking
    def __le__(self, other):
        return SimpleCondition(self, operator.__le__, other)

    @type_checking
    def __lt__(self, other):
        return SimpleCondition(self, operator.__lt__, other)

    def __and__(self, other):
        if isinstance(other, DataAccessor):
            return NAryCondition(
                operator.__and__,
                SimpleCondition(self.field, operator.truth, True),
                SimpleCondition(other.field, operator.truth, True))
        elif isinstance(other, Condition):
            return NAryCondition(
                operator.__and__,
                SimpleCondition(self.field, operator.truth, True),
                other)

    def __or__(self, other):
        if isinstance(other, DataAccessor):
            return NAryCondition(
                operator.__or__,
                SimpleCondition(self.field, operator.truth, True),
                SimpleCondition(other.field, operator.truth, True))
        elif isinstance(other, Condition):
            return NAryCondition(
                operator.__or__,
                SimpleCondition(self.field, operator.truth, True),
                other)

    def __invert__(self):
        return SimpleCondition(self.field, operator.truth, False)

    def __hash__(self):
        return hash(self.field._map_key)

    def __repr__(self):
        return '<{0}, {1}>'.format(type(self).__name__, self._value)


class Int(DataType):
    BASETYPE = int

    def set(self, instance, value):
        if isinstance(value, float):
            value = int(value)
        super(Int, self).set(instance, value)


class Float(DataType):
    BASETYPE = float

    def set(self, instance, value):
        if isinstance(value, (int, long)):
            value = float(value)
        super(Float, self).set(instance, value)


class String(DataType):
    BASETYPE = str

    def __init__(self, encoding='utf-8', **kwargs):
        super(String, self).__init__(**kwargs)
        self.encoding = encoding

    def set(self, instance, value):
        if isinstance(value, unicode):
            value = value.encode(self.encoding)
        super(String, self).set(instance, value)


class Bool(DataType):
    BASETYPE = bool

    def set(self, instance, value):
        super(String, self).set(instance, bool(value))


class Dict(DataType):
    BASETYPE = dict

    def __getitem__(self, key):
        return self._value[key]

    def __setitem__(self, key, value):
        self._value[key] = value


class ArrayAccessor(DataAccessor):
    def __init__(self, instance, field, itemtype):
        self.field = field
        self.instance = instance
        self.itemtype = itemtype

    @property
    def _value(self):
        value = self.instance._data.get(self._map_key, None)
        if value is None:
            value = []
            self.instance._data[self._map_key] = value
        return value

    def item(self, value):
        new_item = self.itemtype(map_key='{0}_{1}'.format(
            self._map_key, uuid.uuid4().hex))
        new_item.set(self.instance, value)
        return new_item

    def append(self, value):
        self.instance.make_dirty()
        return self._append(value)

    def _append(self, value):
        return self._value.append(self.item(value))

    def insert(self, idx, obj):
        self.instance.make_dirty()
        return self._value.insert(idx, self.item(obj))

    # def index

    def pop(self):
        self.instance.make_dirty()
        return self._value.pop()

    # def remove

    def reverse():
        self.instance.make_dirty()
        return self._value.reverse()

    def __len__(self):
        return len(self._value)

    def extend(self, ext):
        self.instance.make_dirty()
        for el in ext:
            self._append(el)

    # def clean()

class Array(DataType):
    BASETYPE = list

    def __init__(self, itemtype, map_key=None):
        super(Array, self).__init__(map_key=map_key)
        self.itemtype = itemtype

    def set(self, instance, vals):
        acc = ArrayAccessor(instance, self, self.itemtype)
        while len(acc):
            acc.pop()
        for val in vals:
            acc.append(val)

    def __get__(self, instance, owner):
        return ArrayAccessor(instance, self, self.itemtype)

    def __set__(self, instance, vals):
        self.set(instance, vals)

    def __call__(self, **kwargs):
        return Array(self.itemtype, **kwargs)
