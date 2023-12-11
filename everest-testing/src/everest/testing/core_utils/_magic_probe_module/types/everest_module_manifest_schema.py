# Auto-generated using JsonSchemaParser via:
#     file = everest_schemas_dir / "manifest.yaml"  # path to Everest config schema
#     json_schema = yaml.safe_load(file.read_text())
#     print(JsonSchemaParser(json.dumps(json_schema),
#                            use_standard_collections=True,
#                            use_double_quotes=True,
#                            field_constraints=True,
#                            use_annotated=True,
#                            use_union_operator=True,
#                            collapse_root_models=True,
#                            class_name="EverestModuleManifest").parse())

from __future__ import annotations

from enum import Enum

from pydantic import AnyUrl, BaseModel, Extra, Field
from typing_extensions import Annotated


class Requires(BaseModel):
    class Config:
        extra = Extra.forbid

    interface: Annotated[str, Field(pattern="^[a-zA-Z_][a-zA-Z0-9_.-]*$")]
    min_connections: Annotated[int | None, Field(ge=0)] = 1
    max_connections: Annotated[int | None, Field(ge=1)] = 1


class Metadata(BaseModel):
    class Config:
        extra = Extra.allow

    base_license: Annotated[
        AnyUrl | None,
        Field(
            description="URI pointing to the base license of this module (e.g. https://opensource.org/licenses/Apache-2.0)"
        ),
    ] = None
    license: Annotated[
        AnyUrl,
        Field(
            description="URI pointing to the license of this module (e.g. https://opensource.org/licenses/Apache-2.0)"
        ),
    ]
    authors: Annotated[
        list[str],
        Field(
            description="Author(s) of this module (an array of strings)",
            min_items=1,
            min_length=2,
        ),
    ]


class Type(Enum):
    boolean = "boolean"
    integer = "integer"
    number = "number"
    string = "string"


class ConfigSetSchema1(BaseModel):
    class Config:
        extra = Extra.allow

    type: Type
    description: Annotated[str, Field(min_length=2)]


class Provides(BaseModel):
    class Config:
        extra = Extra.forbid

    description: Annotated[str, Field(min_length=2)]
    interface: Annotated[
        str,
        Field(
            description="this defines the interface to be implemented",
            min_length=3,
            pattern="^[a-zA-Z_][a-zA-Z0-9_.-]*$",
        ),
    ]
    config: Annotated[
        dict[str, ConfigSetSchema1] | None,
        Field(
            description="Config set for this implementation (and possibly default values) declared as json schema"
        ),
    ] = None


class EverestModuleManifestSchema(BaseModel):
    class Config:
        extra = Extra.forbid

    description: Annotated[str, Field(min_length=2)]
    capabilities: Annotated[
        list[str] | None,
        Field(
            description="linux capabilities this module should have (allowlist)",
            min_items=0,
            min_length=6,
        ),
    ] = []
    config: Annotated[
        dict[str, ConfigSetSchema1] | None,
        Field(
            description="Config set for this module (and possibly default values) declared as json schema"
        ),
    ] = None
    provides: Annotated[
        dict[str, Provides],
        Field(
            description="this configures a list of implementations this module provides along with their api, provided vars and config"
        ),
    ]
    requires: Annotated[
        dict[str, Requires] | None,
        Field(
            description="This describes a list of requirements that must be fulfilled by other modules. The key of this is an arbitrary requirement id that has to be referenced in the connections object by the main config, the values are a list of properties (key-value-pairs) the required module and implementations must have set in their provides section to fulfill this requirement"
        ),
    ] = {}
    metadata: Annotated[
        Metadata, Field(description="this describes some metadata for this module")
    ]
    enable_external_mqtt: Annotated[
        bool | None,
        Field(
            description="this requests access to the external mqtt publishing interface"
        ),
    ] = False
    enable_telemetry: Annotated[
        bool | None,
        Field(description="this requests access to the telemetry publishing interface"),
    ] = False
    enable_global_errors: Annotated[
        bool | None,
        Field(
            description="this requests access to the global error subscription interface"
        ),
    ] = False
