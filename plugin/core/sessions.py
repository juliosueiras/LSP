from .types import ClientConfig, ClientStates, Settings
from .protocol import Request
from .transports import start_tcp_transport
from .rpc import Client, attach_stdio_client
from .process import start_server
from .logging import debug
import os
from .protocol import completion_item_kinds, symbol_kinds
try:
    from .workspace import Workspace
    from typing import Callable, Dict, Any, Optional, Iterable, List
    assert Callable and Dict and Any and Optional and Iterable and List
    assert Workspace
except ImportError:
    pass


def create_session(config: ClientConfig,
                   workspaces: 'Optional[Iterable[Workspace]]',
                   env: dict,
                   settings: Settings,
                   on_pre_initialize: 'Optional[Callable[[Session], None]]' = None,
                   on_post_initialize: 'Optional[Callable[[Session], None]]' = None,
                   on_post_exit: 'Optional[Callable[[str], None]]' = None,
                   bootstrap_client=None) -> 'Optional[Session]':

    def with_client(client) -> 'Session':
        return Session(
            config=config,
            workspaces=workspaces,
            client=client,
            on_pre_initialize=on_pre_initialize,
            on_post_initialize=on_post_initialize,
            on_post_exit=on_post_exit)

    session = None
    if config.binary_args:
        process = start_server(config.binary_args, env, settings.log_stderr)
        if process:
            if config.tcp_port:
                transport = start_tcp_transport(config.tcp_port, config.tcp_host)
                if transport:
                    session = with_client(Client(transport, settings))
                else:
                    # try to terminate the process
                    try:
                        process.terminate()
                    except Exception:
                        pass
            else:
                session = with_client(attach_stdio_client(process, settings))
    else:
        if config.tcp_port:
            transport = start_tcp_transport(config.tcp_port)
            session = with_client(Client(transport, settings))
        elif bootstrap_client:
            session = with_client(bootstrap_client)
        else:
            debug("No way to start session")
    return session


def get_initialize_params(workspaces: 'Optional[Iterable[Workspace]]', config: ClientConfig):
    root_uri = None
    lsp_workspaces = None
    if workspaces is not None:
        root_uri = next(iter(workspaces)).uri
        lsp_workspaces = [workspace.to_dict() for workspace in workspaces]
    initializeParams = {
        "processId": os.getpid(),
        # REMARK: A language server should forget about the rootUri and migrate to using workspaces instead:
        # https://github.com/Microsoft/vscode/wiki/Adopting-Multi-Root-Workspace-APIs#language-client--language-server
        "rootUri": root_uri,
        "workspaceFolders": lsp_workspaces,
        "capabilities": {
            "textDocument": {
                "synchronization": {
                    "didSave": True
                },
                "hover": {
                    "contentFormat": ["markdown", "plaintext"]
                },
                "completion": {
                    "completionItem": {
                        "snippetSupport": True
                    },
                    "completionItemKind": {
                        "valueSet": completion_item_kinds
                    }
                },
                "signatureHelp": {
                    "signatureInformation": {
                        "documentationFormat": ["markdown", "plaintext"],
                        "parameterInformation": {
                            "labelOffsetSupport": True
                        }
                    }
                },
                "references": {},
                "documentHighlight": {},
                "documentSymbol": {
                    "symbolKind": {
                        "valueSet": symbol_kinds
                    }
                },
                "formatting": {},
                "rangeFormatting": {},
                "declaration": {},
                "definition": {},
                "typeDefinition": {},
                "implementation": {},
                "codeAction": {
                    "codeActionLiteralSupport": {
                        "codeActionKind": {
                            "valueSet": []
                        }
                    }
                },
                "rename": {}
            },
            "workspace": {
                "applyEdit": True,
                "didChangeConfiguration": {},
                "executeCommand": {},
                "symbol": {
                    "symbolKind": {
                        "valueSet": symbol_kinds
                    }
                },
                "workspaceFolders": True
            }
        }
    }
    if config.init_options:
        initializeParams['initializationOptions'] = config.init_options

    return initializeParams


class Session(object):
    def __init__(self,
                 config: ClientConfig,
                 workspaces: 'Optional[Iterable[Workspace]]',
                 client: Client,
                 on_pre_initialize: 'Optional[Callable[[Session], None]]' = None,
                 on_post_initialize: 'Optional[Callable[[Session], None]]' = None,
                 on_post_exit: 'Optional[Callable[[str], None]]' = None) -> None:
        self.config = config
        self.state = ClientStates.STARTING
        self._on_post_initialize = on_post_initialize
        self._on_post_exit = on_post_exit
        self.capabilities = dict()  # type: Dict[str, Any]
        self.client = client
        if on_pre_initialize:
            on_pre_initialize(self)
        self.__initialize(workspaces)

    def has_capability(self, capability):
        return capability in self.capabilities and self.capabilities[capability] is not False

    def get_capability(self, capability):
        return self.capabilities.get(capability)

    def __initialize(self, workspaces: 'Optional[Iterable[Workspace]]') -> None:
        params = get_initialize_params(workspaces, self.config)
        debug("sending initialize params:", params)
        self.client.send_request(Request.initialize(params), self._handle_initialize_result)

    def _handle_initialize_result(self, result):
        self.state = ClientStates.READY
        self.capabilities = result.get('capabilities', dict())
        if self._on_post_initialize:
            self._on_post_initialize(self)

    def end(self):
        self.state = ClientStates.STOPPING
        self.client.send_request(
            Request.shutdown(),
            lambda result: self._handle_shutdown_result(),
            lambda: self._handle_shutdown_result())

    def _handle_shutdown_result(self):
        self.client.exit()
        self.client = None
        self.capabilities = dict()
        if self._on_post_exit:
            self._on_post_exit(self.config.name)
