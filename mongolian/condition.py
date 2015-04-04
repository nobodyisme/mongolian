import operator

from bson import SON

import datatypes


class Condition(object):
    def mongo_op(self):
        return OP_TO_MONGO_OP[self.op]

    def __and__(self, other):
        if isinstance(other, datatypes.DataAccessor):
            return NAryCondition(
                operator.__and__,
                self,
                SimpleCondition(other.field, operator.truth, True))
        return NAryCondition(operator.__and__, self, other)

    def __or__(self, other):
        if isinstance(other, datatypes.DataAccessor):
            return NAryCondition(
                operator.__or__,
                self,
                SimpleCondition(other.field, operator.truth, True))
        return NAryCondition(operator.__or__, self, other)

    def not_(self):
        return UnaryCondition(operator.__not__, self)


class SimpleCondition(Condition):

    def __init__(self, field, op, value):
        self.field = field
        self.op = op
        self.value = value

    def __nonzero__(self):
        return self.field._value == self.value


class ComplexCondition(Condition):
    pass


class NAryCondition(ComplexCondition):

    def __init__(self, op, *args):
        self.op = op
        self.conditions = []
        self.field = None
        affected_fields = set()
        if not len(args):
            raise TypeError('Complex condition requires at least '
                'one child condition')

        if len(args) == 1:
            if isinstance(args[0], (tuple, list)):
                args = args[0]

        for cond in args:
            if not isinstance(cond, Condition):
                raise TypeError('Complex condition does not operate '
                    'on type "{0}"'.format(type(cond).__name__))
            self.conditions.append(cond)
            affected_fields.add(cond.field)

        if len(affected_fields) == 1:
            self.field = affected_fields.pop()


class UnaryCondition(NAryCondition):

    def __init__(self, op, *args):
        if not len(args) == 1:
            raise TypeError('Unary condition supports exactly one condition')
        super(UnaryCondition, self).__init__(op, *args)

        if self.op == operator.not_ and self.field is None:
            raise TypeError('Operator $not requires single field condition')


class Renderer(object):

    @staticmethod
    def render(cond):
        if isinstance(cond, datatypes.DataAccessor):
            return Renderer.render(SimpleCondition(
                cond.field, operator.truth, True))

        if isinstance(cond, SimpleCondition):
            if cond.op == operator.eq:
                return SON([(cond.field._map_key, cond.value)])
            else:
                return SON([(cond.field._map_key,
                             SON([(cond.mongo_op(),
                                   cond.value)]) )])
        elif isinstance(cond, UnaryCondition):
            r = Renderer.render(cond.conditions[0])

            # e.g., $not cannot be top-level operator,
            # works only when field is defined by lower conditions
            assert cond.field, "Unknown top-level operator {0}".format(
                cond.mongo_op())
            val = r[cond.field._map_key]
            if not isinstance(val, SON):
                val = SON([('$eq', val)])
            return SON([(cond.field._map_key,
                         SON([(cond.mongo_op(), val)]) )])

        elif isinstance(cond, NAryCondition):
            # r = [Renderer.render(c) for c in cond.conditions]

            if cond.op == operator.and_:
                # special case, uniting similar field conditions
                ordered_fields = []
                by_fields_rendered = {}
                for c in cond.conditions:
                    if not c.field._map_key in by_fields_rendered:
                        by_fields_rendered[c.field._map_key] = []
                        ordered_fields.append(c.field._map_key)
                    by_fields_rendered[c.field._map_key].append(Renderer.render(c))
                print by_fields_rendered
                for field, crs in by_fields_rendered.items():
                    if field is None:
                        continue
                    if len(crs) <= 1:
                        continue
                    sons = []
                    for cr in crs:
                        if isinstance(cr[field], SON):
                            sons.append(cr[field])
                        else:
                            sons.append(SON([('$eq', cr)]))

                    by_fields_rendered[field] = [SON([
                        (field,
                        SON(reduce(operator.add, [s.items() for s in sons])))
                    ])]
                print by_fields_rendered
                if len(by_fields_rendered) == 1 and by_fields_rendered.keys()[0] is not None:
                    field, crs = by_fields_rendered.items()[0]
                    return crs[0]
                else:
                    # TODO: remove else part, fallback to default realization
                    sons = []
                    for field in ordered_fields:
                        for cr in by_fields_rendered[field]:
                            sons.append(cr)

                    return SON([(cond.mongo_op(), sons)])

            return SON([(cond.mongo_op(), [
                Renderer.render(c) for c in cond.conditions
            ])])
        else:
            raise TypeError('Cannot render object of type "{0}"'.format(
                type(cond).__name__))




OP_TO_MONGO_OP = {
    operator.eq: '$eq',
    operator.__eq__: '$eq',

    operator.ne: '$ne',
    operator.__ne__: '$ne',

    operator.gt: '$gt',
    operator.__gt__: '$gt',

    operator.ge: '$gte',
    operator.__ge__: '$gte',

    operator.lt: '$lt',
    operator.__lt__: '$lt',

    operator.le: '$lte',
    operator.__le__: '$lte',

    operator.contains: '$in',
    operator.__contains__: '$in',

    operator.not_: '$not',
    operator.__not__: '$not',

    operator.and_: '$and',
    operator.__and__: '$and',

    operator.or_: '$or',
    operator.__or__: '$or',

    operator.truth: '$exists',
}
