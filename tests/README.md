# Compatibility tests

These tests use Home Assistant's actual tracker entity, state machine, zone component and restore lifecycle with synthetic coordinates and states. They cover named virtual locations, GPS zone transitions, restore behavior and the sensor/number concentration units.

Use Python 3.13 or 3.14 in a virtual environment:

```sh
python -m pip install -r requirements_test.txt
python -m pytest tests/ -q
```

The two environments exercise Home Assistant 2025.6.3 (before the concentration unit enums) and 2026.10.1 (with the replacement enums and tracker deprecation). The removed-constants test is skipped on the older runtime, where the compatibility fallback is expected.

The older environment pins `pycares` to the 4.x API required by its `aiodns` dependency.
