def candidate_runtime_pool_preflight(app, bundle, plan):
    """Resolve the exact candidate's numeric policy before backup or shutdown."""
    import types
    release_path = regular(bundle, 'payload/release-manifest.json')
    release_raw = release_path.read_bytes()
    require(hashlib.sha256(release_raw).hexdigest() == plan['newReleaseSHA256'],
            'CANDIDATE_RELEASE_CHANGED_BEFORE_PREFLIGHT')
    candidate = json.loads(release_raw)
    descriptor = candidate.get(R27_POOL_FIELD)
    if descriptor is None:
        return None
    require(descriptor == R27_POOL_POLICY, 'EXACT_CANDIDATE_POOL_POLICY_REQUIRED')
    name = 'tools/original_server_release_parameters.py'
    source = check_file(bundle / 'payload', name, candidate['controllerFiles'][name])
    source_raw = source.read_bytes()
    require(len(source_raw) <= 128 * 1024 and
            hashlib.sha256(source_raw).hexdigest() == candidate['controllerFiles'][name],
            'CANDIDATE_PARAMETERS_CHANGED_BEFORE_EXEC')
    private = regular(app, 'private/server-configuration.json')
    require(private.is_file() and private.stat().st_size <= 1024 * 1024,
            'BOUNDED_INSTALLED_CONFIGURATION_REQUIRED')
    raw = private.read_bytes()
    configuration = json.loads(raw)
    require(configuration.get('schema') == 'zhumadian.original.server.configuration.v1',
            'INSTALLED_CONFIGURATION_SCHEMA_REQUIRED')
    module = types.ModuleType('owned_candidate_numeric_parameters')
    module.__file__ = str(source)
    exec(compile(source_raw, str(source), 'exec'), module.__dict__)
    budget = module.connection_pool_budget(configuration)
    require(budget['policy'] == descriptor, 'CANDIDATE_BUDGET_POLICY_MISMATCH')
    return {'budget': budget, 'configurationSHA256': hashlib.sha256(raw).hexdigest(),
            'candidateParametersSHA256': candidate['controllerFiles'][name]}

