from pydantic import BaseModel, Field, AliasChoices
from typing import Optional, Any, Dict, Union, List, Literal
from enum import Enum
from pydantic import parse_obj_as


# oriented at
# https://stackoverflow.com/questions/73419115/pydantic-model-for-json-meta-schema

class JsonSchemaType(str, Enum):
    OBJECT = "object"
    ARRAY = "array"
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    NULL = "null"


class BaseJsonSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    default: Any | None = None
    enum: list[Any] | None = None
    ref: str | None = Field(default=None,
                            validation_alias=AliasChoices("$ref", "ref"),
                            serialization_alias="$ref")

    class Config:
        arbitrary_types_allowed = True


class StringJsonSchema(BaseJsonSchema):
    type: Literal["string"]
    minLength: int | None = None
    maxLength: int | None = None
    pattern: str | None = None


class ObjectJsonSchema(BaseJsonSchema):
    type: Literal["object"] = "object"
    properties: dict[str, "JsonSchema"] | None = None
    required: list[str] = Field(default_factory=list)
    additionalProperties: Union[bool, "JsonSchema"] | None = None


class ArrayJsonSchema(BaseJsonSchema):
    type: Literal["array"]
    items: Union["JsonSchema", List["JsonSchema"]]
    minItems: int | None = None
    maxItems: int | None = None
    uniqueItems: bool | None = None


class NumberJsonSchema(BaseJsonSchema):
    type: Literal["number"]
    minimum: float | None = None
    maximum: float | None = None
    exclusiveMinimum: bool | None = None
    exclusiveMaximum: bool | None = None
    multipleOf: float | None = None


class IntegerJsonSchema(BaseJsonSchema):
    type: Literal["integer"]
    minimum: int | None = None
    maximum: int | None = None
    exclusiveMinimum: bool | None = None
    exclusiveMaximum: bool | None = None
    multipleOf: int | None = None


class BooleanJsonSchema(BaseJsonSchema):
    type: Literal["boolean"]


class NullJsonSchema(BaseJsonSchema):
    type: Literal["null"]


JsonSchema = StringJsonSchema | \
             ObjectJsonSchema | \
             ArrayJsonSchema | \
             NumberJsonSchema | \
             IntegerJsonSchema | \
             BooleanJsonSchema | \
             NullJsonSchema

SCHEMAS_BY_TYPE = {"string": StringJsonSchema,
                   "object": ObjectJsonSchema,
                   "array": ArrayJsonSchema,
                   "number": NumberJsonSchema,
                   "integer": IntegerJsonSchema,
                   "boolean": BooleanJsonSchema,
                   "null": NullJsonSchema,
                   }
