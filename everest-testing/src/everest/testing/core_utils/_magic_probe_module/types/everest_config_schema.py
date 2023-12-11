
# Auto Generated using JsonSchemaParser via
#     file = settings.everest_schemas_dir / "config.yaml"  # path to Everest config schema
#     json_schema = yaml.safe_load(file.read_text())
#     print(JsonSchemaParser(json.dumps(json_schema),
#                            use_standard_collections=True,
#                            use_double_quotes=True,
#                            field_constraints=True,
#                            use_annotated=True,
#                            use_union_operator=True,
#                            collapse_root_models=True,
#                            class_name="EverestConfig").parse())

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Extra, Field
from typing_extensions import Annotated


class Settings(BaseModel):
    class Config:
        extra = Extra.forbid

    prefix: str | None = None
    config_file: str | None = None
    configs_dir: str | None = None
    schemas_dir: str | None = None
    modules_dir: str | None = None
    interfaces_dir: str | None = None
    types_dir: str | None = None
    errors_dir: str | None = None
    www_dir: str | None = None
    logging_config_file: str | None = None
    controller_port: int | None = None
    controller_rpc_timeout_ms: int | None = None
    mqtt_broker_host: str | None = None
    mqtt_broker_port: int | None = None
    mqtt_everest_prefix: str | None = None
    mqtt_external_prefix: str | None = None
    telemetry_prefix: str | None = None
    telemetry_enabled: bool | None = None
    validate_schema: bool | None = None


class Telemetry(BaseModel):
    id: Annotated[
        int,
        Field(
            description="Telemetry from modules using the same id will be grouped together"
        ),
    ]


class Connection(BaseModel):
    class Config:
        extra = Extra.forbid

    module_id: Annotated[
        str,
        Field(
            description="module_id this requirement id maps to",
            pattern="^[a-zA-Z_][a-zA-Z0-9_.-]*$",
        ),
    ]
    implementation_id: Annotated[
        str,
        Field(
            description="implementation_id this requirement id maps to",
            pattern="^[a-zA-Z_][a-zA-Z0-9_.-]*$",
        ),
    ]


class ActiveModules(BaseModel):
    class Config:
        extra = Extra.forbid

    module: Annotated[
        str,
        Field(
            description="Module name (e.g. directory name in the modules subdirectory)",
            pattern="^[a-zA-Z_][a-zA-Z0-9_-]*$",
        ),
    ]
    config_module: Annotated[
        dict[str, bool | int | float | str] | None,
        Field(description="Config map for the module"),
    ] = None
    config_implementation: Annotated[
        dict[str, dict[str, bool | int | float | str]] | None,
        Field(description="List of config maps for each implementation"),
    ] = {}
    telemetry: Annotated[
        Telemetry | None,
        Field(
            description="If this object is present telemetry for the module will be enabled"
        ),
    ] = None
    connections: Annotated[
        dict[str, list[Connection]] | None,
        Field(
            description="List of requirements: a mapping of all requirement ids listed in the module's manifest to module_id (declared in this file) and implementation_id (declared in manifest)."
        ),
    ] = {}


class EverestConfigSchema(BaseModel):
    class Config:
        extra = Extra.forbid

    settings: Settings | None = None
    active_modules: dict[str, ActiveModules]
    x_module_layout: Annotated[Any | None, Field(alias="x-module-layout")] = None

