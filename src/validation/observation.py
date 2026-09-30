"""Application-level validation for the AQUA-SENSE observation contract."""

from datetime import datetime
from math import isfinite
from typing import Any

VARIABLE_RULES = {
    'rainfall_mm': ('mm', 0.0),
    'air_temperature_c': ('degC', -80.0),
    'relative_humidity_pct': ('pct', 0.0),
    'et0_mm': ('mm', 0.0),
    'soil_moisture_m3_m3': ('m3/m3', 0.0),
    'groundwater_depth_m': ('m', 0.0),
    'irrigation_demand_mm': ('mm', 0.0),
}
QUALITY_FLAGS = {'observed', 'estimated', 'imputed', 'suspect', 'missing'}

class ObservationValidationError(ValueError):
    """Raised when an observation violates the canonical contract."""

def validate_observation(observation: dict[str, Any]) -> None:
    required = {'observation_id','observed_at','location_id','source','variable','value','unit'}
    missing = required - observation.keys()
    if missing:
        raise ObservationValidationError(f'missing required fields: {", ".join(sorted(missing))}')
    if not isinstance(observation['observation_id'], str) or not observation['observation_id']:
        raise ObservationValidationError('observation_id must be a non-empty string')
    try:
        datetime.fromisoformat(observation['observed_at'].replace('Z', '+00:00'))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ObservationValidationError('observed_at must be a valid ISO-8601 timestamp') from exc
    for field in ('location_id','source','variable','unit'):
        if not isinstance(observation[field], str) or not observation[field]:
            raise ObservationValidationError(f'{field} must be a non-empty string')
    variable = observation['variable']
    if variable not in VARIABLE_RULES:
        raise ObservationValidationError(f'unsupported variable: {variable}')
    expected_unit, minimum = VARIABLE_RULES[variable]
    if observation['unit'] != expected_unit:
        raise ObservationValidationError(f'{variable} requires unit {expected_unit}, got {observation["unit"]}')
    value = observation['value']
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ObservationValidationError('value must be a finite number')
    if value < minimum:
        raise ObservationValidationError(f'{variable} must be >= {minimum}, got {value}')
    if variable == 'relative_humidity_pct' and value > 100:
        raise ObservationValidationError('relative_humidity_pct must be <= 100')
    if variable == 'soil_moisture_m3_m3' and value > 1:
        raise ObservationValidationError('soil_moisture_m3_m3 must be <= 1')
    quality_flag = observation.get('quality_flag')
    if quality_flag is not None and quality_flag not in QUALITY_FLAGS:
        raise ObservationValidationError(f'unsupported quality_flag: {quality_flag}')
    latitude = observation.get('latitude')
    if latitude is not None and not isinstance(latitude, (int, float)):
        raise ObservationValidationError('latitude must be numeric')
    if latitude is not None and not -90 <= latitude <= 90:
        raise ObservationValidationError('latitude must be between -90 and 90')
    longitude = observation.get('longitude')
    if longitude is not None and not isinstance(longitude, (int, float)):
        raise ObservationValidationError('longitude must be numeric')
    if longitude is not None and not -180 <= longitude <= 180:
        raise ObservationValidationError('longitude must be between -180 and 180')
