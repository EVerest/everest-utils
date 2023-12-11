
# Auto Generated using JsonSchemaParser via
#     from datamodel_code_generator import DataModelType, PythonVersion
#     from datamodel_code_generator.model import get_data_model_types
#     data_model_types = get_data_model_types(DataModelType.PydanticV2BaseModel,
#                                             target_python_version=PythonVersion.PY_310)
#
#     file = everest_schemas_dir / "interface.yaml"  # path to Everest config schema
#     json_schema = yaml.safe_load(file.read_text())
#     print(JsonSchemaParser(json.dumps(json_schema),
#                            use_standard_collections=True,
#                            use_double_quotes=True,
#                            field_constraints=True,
#                            use_annotated=True,
#                            use_union_operator=True,
#                            data_model_type=data_model_types.data_model,
#                            data_model_root_type=data_model_types.root_model,
#                            data_model_field_type=data_model_types.field_model,
#                            data_type_manager_type=data_model_types.data_type_manager,
#                            class_name="EverestInterfaceSchema").parse())
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel
from typing_extensions import Annotated


class Reference(RootModel[str]):
    root: Annotated[str, Field(pattern="^/errors/[a-z][a-zA-Z0-9_]*$")]


class Reference1(RootModel[str]):
    root: Annotated[
        str, Field(pattern="^/errors/[a-z][a-zA-Z0-9_]*#/[A-Z][A-Za-z0-9]*$")
    ]


class Error(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    reference: Reference | Reference1


class VarSubschema(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    description: Annotated[str, Field(min_length=2)]
    type: str | list[str]
    qos: Annotated[int | None, Field(2, ge=0, le=2)]
    default: Any | None = None


class CmdArgumentsSubschema1(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    description: Annotated[str, Field(min_length=2)]
    type: str | list[str] = None
    default: Any | None = None


class CmdArgumentsSubschema(RootModel[dict[str, CmdArgumentsSubschema1]]):
    root: dict[str, CmdArgumentsSubschema1]


class CmdResultSubschema(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    description: Annotated[str, Field(min_length=2)]
    type: str | list[str] | None = None
    default: Any | None = None


class Cmds(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    description: Annotated[str, Field(min_length=2)]
    arguments: CmdArgumentsSubschema | None = None
    result: CmdResultSubschema | None = None


class EverestInterfaceSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    description: Annotated[str, Field(min_length=2)]
    cmds: Annotated[
        dict[str, Cmds] | None,
        Field(
            {},
            description="This describes a list of commands for this unit having arguments and result declared as json schema",
        ),
    ]
    vars: Annotated[
        dict[str, VarSubschema] | None,
        Field(
            {}, description="This describes a list of exported variables of this unit"
        ),
    ]
    errors: Annotated[
        list[Error] | None,
        Field(
            [],
            description="This describes a list of error list allowed to be raised by this unit",
        ),
    ]

