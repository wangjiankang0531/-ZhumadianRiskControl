"""Opt-in composition with the original loopback project server and lifecycle.

No deployment/configuration is performed. With the option absent, the original
handler and its GIS/layer routing are retained exactly. No default descriptors.
"""
from http.server import HTTPServer
import socket
import sys
from services.client_resource_grants import ClientResourceGrantAuthority,with_client_resource_grants,require

def with_client_resource_server(original_server):
    require(isinstance(original_server,type) and issubclass(original_server,HTTPServer),500,'ORIGINAL_PROJECT_SERVER_REQUIRED')
    class ClientResourceServer(original_server):
        def server_bind(self):
            if self.resource_grant_authority is not None:
                # HTTPServer's SO_REUSEADDR permits duplicate live binds on
                # Windows. Opt-in management must never share an occupied port.
                self.allow_reuse_address=False
                if sys.platform=='win32':
                    self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            super().server_bind()

        def __init__(self,port,repository,access,*,client_resource_installations=None,**original_settings):
            self.resource_grant_authority=None
            authority=None
            # Validate the opt-in before the original constructor binds a port.
            if client_resource_installations is not None:
                authority=ClientResourceGrantAuthority(access,client_resource_installations)
                self.resource_grant_authority=authority
            constructed=False
            try:
                super().__init__(port,repository,access,**original_settings)
                constructed=True
                if authority is not None:
                    self.RequestHandlerClass=with_client_resource_grants(self.RequestHandlerClass)
            except BaseException:
                if authority is not None:authority.close()
                if constructed:super().server_close()
                raise

        def server_close(self):
            if self.resource_grant_authority is not None:self.resource_grant_authority.close()
            super().server_close()

    return ClientResourceServer
