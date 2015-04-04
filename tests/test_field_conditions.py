import pytest

from mongolian import MongoObject
from mongolian.condition import Renderer
from mongolian.datatypes import Int, Float, String, Bool, Dict, Array


@pytest.fixture
def mongo_object_type():

    class MongoObjectType(MongoObject):
        i = Int()
        f = Float()
        s = String()
        b = Bool()
        d = Dict()
        a = Array(String)
        aa = Array(Array(String))

    return MongoObjectType


class TestFieldConditions(object):

    def test_lt_op(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(obj.i < 5).to_dict() == {'i': {'$lt' : 5}}

    def test_lte_op(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(obj.f <= 5.0).to_dict() == {'f': {'$lte' : 5.0}}

    def test_gt_op(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(obj.i > 5).to_dict() == {'i': {'$gt' : 5}}

    def test_gte_op(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(obj.f >= 5.0).to_dict() == {'f': {'$gte' : 5.0}}

    def test_eq_op(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(
            obj.s == 'some string').to_dict() == {'s': 'some string'}

    def test_ne_op(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(
            obj.d != {'key': 5}).to_dict() == {'d': {'$ne' : {'key': 5}}}

    def test_same_field_and(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(
            (obj.i > 5) & (obj.i <= 10)
        ).to_dict() == {'i': {'$gt' : 5, '$lte': 10}}

    def test_same_field_or(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(
            (obj.f < 5.0) | (obj.f >= 10.0)
        ).to_dict() == {'$or': [{'f': {'$lt': 5.0}}, {'f': {'$gte': 10.0}}]}

    def test_diff_field_and(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(
            (obj.i < 5) & (obj.b == True)
        ).to_dict() == {'$and': [{'i': {'$lt': 5}}, {'b': True}]}

    def test_field_not(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(
            ((obj.i > 5) & (obj.i <= 10)).not_()
        ).to_dict() == {'i': {'$not': {'$gt' : 5, '$lte': 10}}}

        with pytest.raises(TypeError):
            # $not works only with one field at a time
            Renderer.render(
                ((obj.i > 5) & (obj.f <= 10.0)).not_()
            )

    def test_field_exists(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(obj.i).to_dict() == {'i': {'$exists': True}}

        assert Renderer.render(
            obj.i & obj.f
        ).to_dict() == {'$and': [{'i': {'$exists': True}},
                                 {'f': {'$exists': True}}]}

        assert Renderer.render(
            (obj.i == 5) & obj.f
        ).to_dict() == {'$and': [{'i': 5},
                                 {'f': {'$exists': True}}]}

        assert Renderer.render(
            obj.i & (obj.f >= 5.0)
        ).to_dict() == {'$and': [{'i': {'$exists': True}},
                                 {'f': {'$gte': 5.0}}]}

    def test_field_not_exists(self, mongo_object_type):
        obj = mongo_object_type()
        assert Renderer.render(~obj.i).to_dict() == {'i': {'$exists': False}}

        assert Renderer.render(
            obj.i & ~obj.f
        ).to_dict() == {'$and': [{'i': {'$exists': True}},
                                 {'f': {'$exists': False}}]}

        assert Renderer.render(
            (obj.i == 5) & ~obj.f
        ).to_dict() == {'$and': [{'i': 5},
                                 {'f': {'$exists': False}}]}
