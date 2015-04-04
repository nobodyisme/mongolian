import operator

import pytest

from mongolian.condition import *
from mongolian.datatypes import *


SC1_FIELD, SC1_VALUE = String(), 'string'
SC1_FIELD.set_default_map_key('string_field')

SC2_FIELD, SC2_VALUE = Bool(), True
SC2_FIELD.set_default_map_key('bool_field')

SC3_FIELD, SC31_VALUE, SC32_VALUE = Int(), 25, 25
SC3_FIELD.set_default_map_key('int_field')

@pytest.fixture
def simple_conditions():
    field1, value1 = SC1_FIELD, SC1_VALUE
    field2, value2 = SC2_FIELD, SC2_VALUE
    field3, value31, value32 = SC3_FIELD, SC31_VALUE, SC32_VALUE
    sc1 = SimpleCondition(field1, operator.eq, value1)
    sc2 = SimpleCondition(field2, operator.le, value2)
    sc31 = SimpleCondition(field3, operator.ne, value31)
    sc32 = SimpleCondition(field3, operator.le, value32)
    return sc1, sc2, sc31, sc32


class TestConditions(object):
    def test_simple_condition(self):
        field, value = String(), 'some_value'
        field.set_default_map_key('some_field')
        sc = SimpleCondition(field, operator.eq, value)
        assert sc.field._map_key == 'some_field'
        assert sc.value == value

    def test_nary_condition(self, simple_conditions):
        sc1, sc2, sc31, sc32 = simple_conditions
        cc1 = NAryCondition(operator.or_, sc1, sc2)
        cc2 = NAryCondition(operator.and_, [sc1, sc2])

        with pytest.raises(TypeError):
            NAryCondition(operator.and_, sc1, sc2, 'not_a_condition')

        assert cc1.field == None

        cc3 = NAryCondition(operator.and_, sc31, sc32)
        assert cc3.field._map_key == sc31.field._map_key

    def test_unary_condition(self, simple_conditions):
        sc1, sc2 = simple_conditions[:2]
        cc1 = UnaryCondition(operator.not_, sc1)
        cc2 = UnaryCondition(operator.not_, sc2)

        with pytest.raises(TypeError):
            UnaryCondition(operator.not_, sc1, sc2)
        with pytest.raises(TypeError):
            UnaryCondition(operator.not_)

        assert cc1.field._map_key == sc1.field._map_key

    def test_unary_not_condition(self, simple_conditions):
        sc1, sc2 = simple_conditions[:2]
        cc1 = NAryCondition(operator.and_, sc1, sc2)
        with pytest.raises(TypeError):
            UnaryCondition(operator.not_, cc1)


class TestRender(object):
    def test_simple_condition(self, simple_conditions):
        sc1, sc2 = simple_conditions[:2]

        assert Renderer.render(sc1).to_dict() == {SC1_FIELD._map_key: SC1_VALUE}
        assert Renderer.render(sc2).to_dict() == {SC2_FIELD._map_key: {'$lte': SC2_VALUE}}

    def test_unary_condition(self, simple_conditions):
        sc1, sc2 = simple_conditions[:2]

        cc1 = UnaryCondition(operator.not_, sc1)
        assert Renderer.render(cc1).to_dict() == {SC1_FIELD._map_key: {'$not': {'$eq': SC1_VALUE}}}

        cc2 = UnaryCondition(operator.not_, sc2)
        assert Renderer.render(cc2).to_dict() == {SC2_FIELD._map_key: {'$not': {'$lte': SC2_VALUE}}}

    def test_nary_condition(self, simple_conditions):
        sc1, sc2, sc31, sc32 = simple_conditions[:4]

        cc1 = NAryCondition(operator.and_, sc31, sc32)
        assert Renderer.render(cc1).to_dict() == {SC3_FIELD._map_key: {'$ne': SC31_VALUE,
                                                                       '$lte': SC32_VALUE}}

        cc2 = NAryCondition(operator.and_, sc1, sc31, sc32)
        assert Renderer.render(cc2).to_dict() == {'$and': [
               {SC1_FIELD._map_key: SC1_VALUE},
               {SC3_FIELD._map_key: {'$ne': SC31_VALUE,
                                     '$lte': SC32_VALUE}}]}

