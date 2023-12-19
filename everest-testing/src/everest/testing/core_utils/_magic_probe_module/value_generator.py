import logging
from dataclasses import dataclass, field
from datetime import datetime
from functools import singledispatchmethod, wraps
from itertools import count

import rstr

from everest.testing.core_utils._magic_probe_module.types.json_schema_models import JsonSchema, StringJsonSchema, NumberJsonSchema, \
    BaseJsonSchema, NullJsonSchema, ArrayJsonSchema, ObjectJsonSchema, BooleanJsonSchema, IntegerJsonSchema
from .types.everest_type import EverestType


class ValueGenerator:
    _MAX_DEPTH = 100

    @dataclass
    class _GeneratorContext:
        history: list[JsonSchema] = field(default_factory=list)
        key_history: list[str] = field(default_factory=list)

        @property
        def depth(self) -> int:
            return len(self.history)

    @staticmethod
    def _generation_step(fun):
        @wraps(fun)
        def _generation_func(self, what: JsonSchema, context):
            context.history.append(what)
            if what.ref:
                what = self._everest_types[what.ref].json_schema
                return self._generate_json_schema(what, context)
            return fun(self, what, context)
        return _generation_func

    def __init__(self, everest_types: list[EverestType]):

        self._float_generator = (v / 10 for v in count(10))
        self._int_generator = count(1)
        self._string_generator = (f"test_string_{v}" for v in count(1))
        self._bool_generator = ((v % 2) == 0 for v in count(1))
        self._builtin_datetime_generator = (datetime.fromtimestamp(v * 60 * 60 * 24) for v in count(1))

        self._everest_types = {e.json_ref: e for e in everest_types}

    @singledispatchmethod
    def generate(self, what):
        raise NotImplementedError(f"no implemented for {what}")

    @generate.register
    def _(self, what: BaseJsonSchema):
        return self._generate_json_schema(what)

    def _generate_json_schema(self, schema: JsonSchema, context: _GeneratorContext | None = None):

        context = context if context else self._GeneratorContext()

        if isinstance(schema, ArrayJsonSchema):
            return self._generate_array(schema, context)
        elif hasattr(schema, "enum") and schema.enum:
            return self._generate_enum(schema, context)
        if isinstance(schema, StringJsonSchema):
            return self._generate_str(schema, context)
        elif isinstance(schema, NumberJsonSchema):
            return self._generate_float(schema, context)
        elif isinstance(schema, IntegerJsonSchema):
            return self._generate_int(schema, context)
        elif isinstance(schema, BooleanJsonSchema):
            return self._generate_bool(schema, context)
        elif isinstance(schema, ObjectJsonSchema):
            return self._generate_object(schema, context)
        elif isinstance(schema, NullJsonSchema):
            return self._generate_null(schema, context)
        else:
            raise NotImplementedError(f"unsupported schema type {type(schema)}")

    @generate.register
    def _(self, what: EverestType):
        return self.generate(what.json_schema)

    @generate.register
    def _(self, what: str, context: _GeneratorContext | None = None):
        return self.generate(self._everest_types[what])

    @_generation_step
    def _generate_enum(self, what: BaseJsonSchema, context: _GeneratorContext):
        assert what.enum
        index = next(self._int_generator) % len(what.enum)
        return what.enum[index]

    @_generation_step
    def _generate_str(self, what: StringJsonSchema, context: _GeneratorContext) -> str:
        s = next(self._string_generator)
        if what.pattern:
            s = rstr.xeger(what.pattern)
            return s
        if what.minLength:
            s = (what.minLength - len(s)) * "0" + s
        if what.maxLength:
            s = s[:what.maxLength]
        return s

    @_generation_step
    def _generate_float(self, what: NumberJsonSchema, context: _GeneratorContext):
        number = next(self._float_generator)
        min = what.minimum if what.minimum else 0
        if number < min:
            number = number + min
        if what.maximum and number > what.maximum:
            number = min + (number - min) % (what.maximum - min)
        if what.multipleOf:
            logging.warning("multipleOf not supported yet")

        return number

    @_generation_step
    def _generate_int(self, what: IntegerJsonSchema, context: _GeneratorContext):
        if context.key_history and context.key_history[-1] == "id":
            return 1

        number = next(self._int_generator)
        min = what.minimum if what.minimum else 0
        if number < min:
            number = number + min
        if what.maximum and number > what.maximum:
            number = min + (number - min) % (what.maximum - min)
        if what.multipleOf:
            logging.warning("multipleOf not supported yet")

        return number

    @_generation_step
    def _generate_bool(self, what: BooleanJsonSchema, context: _GeneratorContext) -> bool:
        return next(self._bool_generator)

    @_generation_step
    def _generate_object(self, what: ObjectJsonSchema, context: _GeneratorContext):
        value = {}
        for key, p in what.properties.items():
            if context.depth < self._MAX_DEPTH or key in what.required:
                context.key_history.append(key)
                value[key] = self._generate_json_schema(p, context)
        return value

    @_generation_step
    def _generate_array(self, what: ArrayJsonSchema, context: _GeneratorContext):
        if context.depth > self._MAX_DEPTH:
            return []

        target_schema = what.items if not isinstance(what.items, list) else what.items[0]
        context.key_history.append(0)
        return [self._generate_json_schema(target_schema, context)]

    @_generation_step
    def _generate_null(self, what: NullJsonSchema, context: _GeneratorContext):
        raise None
