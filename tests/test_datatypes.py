import pytest

from mongolian import MongoObject
from mongolian.datatypes import Int, Float, String, Dict, Array


@pytest.fixture
def mongo_object_type():

    class MongoObjectType(MongoObject):
        i = Int()
        f = Float()
        s = String()
        d = Dict()
        a = Array(String)
        aa = Array(Array(String))

    return MongoObjectType


class TestDatatypes(object):
    def test_int_datatype(self, mongo_object_type):
        obj = mongo_object_type()
        obj.i = 5
        assert obj.i == 5
        with pytest.raises(TypeError):
            obj.i = 'string'

    def test_float_datatype(self, mongo_object_type):
        obj = mongo_object_type()

        obj.f = 5
        assert type(obj.f._value) == float
        assert obj.f == 5.0

        obj.f = 5.0
        assert type(obj.f._value) == float
        assert obj.f == 5.0

        with pytest.raises(TypeError):
            obj.f = 'string'

    def test_string_datatype(self, mongo_object_type):
        obj = mongo_object_type()

        obj.s = 'string'
        assert type(obj.s._value) == str
        assert obj.s == 'string'

        obj.s = u'string'
        assert type(obj.s._value) == str
        assert obj.s == 'string'

        with pytest.raises(TypeError):
            obj.s = 5

    def test_dict_datatype(self, mongo_object_type):
        obj = mongo_object_type()

        obj.d = {'a': 1,
                 'b': '2'}
        assert type(obj.d._value) == dict
        assert obj.d['a'] == 1
        assert obj.d['b'] == '2'

        with pytest.raises(TypeError):
            obj.d = 5

    def test_array_datatype(self, mongo_object_type):
        obj = mongo_object_type()

        obj.a = ['a', 'b', 'c']
        assert obj.a[1] == 'b'

        obj.a[1] = 'd'
        assert obj.a[1] == 'd'

    def test_enclosed_array_datatype(self, mongo_object_type):
        obj = mongo_object_type()

        obj.aa = [['a', 'b'], ['c', 'd']]
        assert obj.aa[0][0] == 'a'
        assert obj.aa[1][1] == 'd'

        obj.aa[1] = ['e', 'f']
        assert obj.aa[1][1] == 'f'

        obj.aa[1][1] = 'g'
        assert obj.aa[1][1] == 'g'

        with pytest.raises(TypeError):
            obj.aa[1][1] = 5

    def test_descriptors_per_instance(self, mongo_object_type):
        obj1 = mongo_object_type()
        obj2 = mongo_object_type()

        obj1.i = 5
        obj2.i = 6
        assert obj1.i == 5
        assert obj2.i == 6

        obj1.a = ['a', 'b']
        obj2.a = ['c', 'd']
        assert (obj1.a[0], obj1.a[1]) == ('a', 'b')
        assert (obj2.a[0], obj2.a[1]) == ('c', 'd')

