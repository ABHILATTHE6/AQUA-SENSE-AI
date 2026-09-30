from src.validation.observation import ObservationValidationError, validate_observation

def base_observation():
    return {
        'observation_id': 'weather|LOC001|2026-09-30T12:00:00+05:30|rainfall_mm',
        'observed_at': '2026-09-30T12:00:00+05:30',
        'location_id': 'LOC001',
        'source': 'test-source',
        'variable': 'rainfall_mm',
        'value': 12.5,
        'unit': 'mm',
    }

def expect_rejection(observation):
    try:
        validate_observation(observation)
    except ObservationValidationError:
        return
    raise AssertionError('invalid observation was accepted')

def test_valid_observation():
    validate_observation(base_observation())

def test_rejects_unknown_variable():
    observation = base_observation(); observation['variable'] = 'rain_probability'; observation['unit'] = 'pct'
    expect_rejection(observation)

def test_rejects_wrong_unit():
    observation = base_observation(); observation['unit'] = 'litre'
    expect_rejection(observation)

def test_rejects_invalid_humidity():
    observation = base_observation(); observation.update(variable='relative_humidity_pct', unit='pct', value=101)
    expect_rejection(observation)

def test_rejects_negative_rainfall():
    observation = base_observation(); observation['value'] = -1
    expect_rejection(observation)
