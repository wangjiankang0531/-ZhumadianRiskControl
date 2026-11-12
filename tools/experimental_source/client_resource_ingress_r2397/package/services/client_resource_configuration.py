"""Explicit management descriptor config; validate before any data/listener."""
from services.client_resource_grants import ClientResourceGrantAuthority

def validate_client_resource_settings(config,access):
    if 'clientResources' not in config:return
    value=config['clientResources']
    if (not isinstance(value,dict) or set(value)!={'schema','allowedInstallations'}
            or value['schema']!='xnby.client-resources.server-settings.v1'):
        raise ValueError('EXACT_CLIENT_RESOURCE_SETTINGS_REQUIRED')
    authority=ClientResourceGrantAuthority(access,value['allowedInstallations'])
    authority.close()
