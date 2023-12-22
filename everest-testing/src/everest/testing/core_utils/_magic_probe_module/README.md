# The Magic Probe Module

## Motivation

The "pure" Probe Module comes with the issue of high configuration effort. To "quickly" test another's module interface,
a lot of configuration is required. Furthermore, if a probe module's commands are called that are not explicitly implemented,
the process hangs without further notification.

The idea behind the "magic" probe module is similar to the distinction of the "Mock" and "MagicMock" classes in
Python unittests: The latter "out of the box" provides all magic methods (for comparisons etc.) and requires less configuration.

The Magic Probe Module should configure itself automatically as much as possible and mitigate the drawbacks of the default
one.


## Core Concepts

The Magic Probe Module:
- Gets activated by the marker `@magic_probe_module` and this then available via the `magic_probe_module` fixture.
- Is automatically configured to fulfill _any_ requirement that is not fulfilled in the provided Everest configuration.
- Also detects existing requirement fulfillments in the provided Everest configuration (in case certain implementation ids shall be useed)
- Automatically implements _any_ command and wraps it into mock calls. The `implement_command` method of the Magic Probe Module
allows to set the return value or side effect of each command. This can be done even after module startup. Per default,
it provides a auto-generated value. Can be set (via the strict parameter of the `@magic_probe_module` to _strict_ mode to
raise an Exception per default instead)
- Possesses a value generator that is capable of generating any EVerest type (as far as specified in the Json Schema; works most of the timel™)

## Requirements

The magic probe module currently requires packages:
- pydantic >= 2
- rstr 

## Usage Examples

Given the config:

```yaml
active_modules:
  ocpp:
    module: OCPP201
    config_module:
      ChargePointConfigPath: config.json
      EnableExternalWebsocketControl: true
    connections: {}
x-module-layout: {}


```

the following example (assuming correct imports) works:

```python

@pytest.mark.asyncio
@pytest.mark.ocpp_version("ocpp2.0.1")
@pytest.mark.everest_core_config("everest-config-ocpp201-magic-probe-module.yaml")
@pytest.mark.magic_probe_module()
async def test_against_occp(central_system: CentralSystem,
                            test_controller,
                            magic_probe_module,
                            test_utility: TestUtility):
    test_controller.start()
    magic_probe_module.start()
    await magic_probe_module.wait_to_be_ready()
    await central_system.wait_for_chargepoint()
    
    # get all implementations for a certain interface
    evse_managers = [impl for impl, intf in magic_probe_module.get_interface_implementations().items() if
                     intf.interface == "evse_manager"] 

    for evse_manager_implementation in evse_managers:
        magic_probe_module.publish_variable(evse_manager_implementation, "iso15118_certificate_request",
                                            {"exiRequest": "bla",
                                             "iso15118SchemaVersion": "mock_iso15118_schema_version",
                                             "certificateAction": "ba"})
        await asyncio.sleep(1)
        # The OCPP module should have called the "enable" endpoint of the evse_manager, this command is automatically implemented
        magic_probe_module.implementation_mocks[evse_manager_implementation].enable.assert_called_with(
            {"connector_id": ANY})

```

Note that under the hood the Magic Probe Module will create the following configuration that EVerest is started with:
```yaml
active_modules:
  ocpp:
    config_module:
      CertsPath: /tmp/sharedtmp/pytest/test_against_occp0/certs
      ChargePointConfigPath: /tmp/sharedtmp/pytest/test_against_occp0/ocpp_config/config.json
      CoreDatabasePath: /tmp/sharedtmp/pytest/test_against_occp0/ocpp_config
      DeviceModelDatabasePath: /tmp/sharedtmp/pytest/test_against_occp0/ocpp_config/device_model_storage.db
      EnableExternalWebsocketControl: true
      MessageLogPath: /tmp/sharedtmp/pytest/test_against_occp0/ocpp_config/logs
    connections:
      evse_manager:
      - implementation_id: ProbeModuleConnectorA
        module_id: probe
      kvs:
      - implementation_id: kvs
        module_id: probe
      security:
      - implementation_id: evse_security
        module_id: probe
      system:
      - implementation_id: system
        module_id: probe
    module: OCPP201
  probe:
    connections:
      auth_token_provider:
      - implementation_id: auth_provider
        module_id: ocpp
      auth_token_validator:
      - implementation_id: auth_validator
        module_id: ocpp
      empty:
      - implementation_id: main
        module_id: ocpp
      ocpp_data_transfer:
      - implementation_id: data_transfer
        module_id: ocpp
    module: ProbeModule
settings:
  controller_port: 0
  mqtt_everest_prefix: everest_5b6796904fe04146b0b79dd07de69c65
  mqtt_external_prefix: external_5b6796904fe04146b0b79dd07de69c65
  telemetry_prefix: telemetry_5b6796904fe04146b0b79dd07de69c65
x-module-layout: {}

```

## Todos

- Issue with invalid values (e.g. Connector ids must be sequential)
- Downgrade to Pydantic 1