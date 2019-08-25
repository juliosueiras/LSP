import re
try:
    from typing_extensions import Protocol
    from typing import Optional, List, Callable, Dict, Any, Tuple, Iterable
    assert Optional and List and Callable and Dict and Any and Tuple and Iterable
except ImportError:
    pass
    Protocol = object  # type: ignore


class Settings(object):

    def __init__(self) -> None:
        self.show_status_messages = True
        self.show_view_status = True
        self.auto_show_diagnostics_panel = True
        self.auto_show_diagnostics_panel_level = 3
        self.show_diagnostics_phantoms = False
        self.show_diagnostics_count_in_view_status = False
        self.show_diagnostics_in_view_status = True
        self.show_diagnostics_severity_level = 3
        self.only_show_lsp_completions = False
        self.diagnostics_highlight_style = "underline"
        self.document_highlight_style = "stippled"
        self.document_highlight_scopes = {
            "unknown": "text",
            "text": "text",
            "read": "markup.inserted",
            "write": "markup.changed"
        }
        self.diagnostics_gutter_marker = "dot"
        self.show_code_actions_bulb = False
        self.complete_all_chars = False
        self.completion_hint_type = "auto"
        self.prefer_label_over_filter_text = False
        self.show_references_in_quick_panel = False
        self.quick_panel_monospace_font = False
        self.log_debug = True
        self.log_server = True
        self.log_stderr = False
        self.log_payloads = False


class ClientStates(object):
    STARTING = 0
    READY = 1
    STOPPING = 2


def config_supports_syntax(config: 'ClientConfig', syntax: str) -> bool:
    for language in config.languages:
        if re.search(r'|'.join(r'\b%s\b' % re.escape(s) for s in language.syntaxes), syntax, re.IGNORECASE):
            return True
    return False


class LanguageConfig(object):
    def __init__(self, language_id: str, scopes: 'List[str]', syntaxes: 'List[str]') -> None:
        self.id = language_id
        self.scopes = scopes
        self.syntaxes = syntaxes


class ClientConfig(object):
    def __init__(self, name: str, binary_args: 'List[str]', tcp_port: 'Optional[int]', scopes=[],
                 syntaxes=[], languageId: 'Optional[str]' = None,
                 languages: 'List[LanguageConfig]' = [], enabled: bool = True, init_options=dict(),
                 settings=dict(), env=dict(), tcp_host: 'Optional[str]' = None) -> None:
        if ' ' in name:
            raise ValueError('config name contains spaces: "{}"'.format(name))
        self.name = name
        self.binary_args = binary_args
        self.tcp_port = tcp_port
        self.tcp_host = tcp_host
        if not languages:
            languages = [LanguageConfig(languageId, scopes, syntaxes)] if languageId else []
        self.languages = languages
        self.enabled = enabled
        self.init_options = init_options
        self.settings = settings
        self.env = env


class ViewLike(Protocol):

    def id(self) -> int:
        ...

    def file_name(self) -> 'Optional[str]':
        ...

    def window(self) -> 'Optional[Any]':  # WindowLike
        ...

    def buffer_id(self) -> int:
        ...

    def substr(self, region: 'Any') -> str:
        ...

    def settings(self) -> 'Any':  # SettingsLike
        ...

    def size(self) -> int:
        ...

    def set_status(self, key: str, status: str) -> None:
        ...

    def sel(self):
        ...

    def score_selector(self, region, scope: str) -> int:
        ...

    def assign_syntax(self, syntax: str) -> None:
        ...

    def set_read_only(self, val: bool) -> None:
        ...

    def run_command(self, command_name: str, command_args: 'Optional[Dict[str, Any]]' = None) -> None:
        ...

    def find_all(self, selector: str) -> 'Iterable[Tuple[int, int]]':
        ...

    def add_regions(self, key: str, regions: 'Iterable[Any]', scope: str = "", icon: str = "", flags: int = 0) -> None:
        ...


class WindowLike(Protocol):
    def id(self) -> int:
        ...

    def is_valid(self):
        ...

    def hwnd(self):
        ...

    def active_view(self) -> 'Optional[ViewLike]':
        ...

    def run_command(self, cmd: str, args: 'Optional[Dict[str, Any]]') -> None:
        ...

    def new_file(self, flags: int, syntax: str) -> ViewLike:
        ...

    def open_file(self, fname: str, flags: int, group: int) -> ViewLike:
        ...

    def find_open_file(self, fname: str) -> 'Optional[ViewLike]':
        ...

    def num_groups(self) -> int:
        ...

    def active_group(self) -> int:
        ...

    def focus_group(self, idx: int) -> None:
        ...

    def active_view_in_group(self, group: int) -> ViewLike:
        ...

    def layout(self):
        ...

    def get_layout(self):
        ...

    def set_layout(self, layout):
        ...

    def create_output_panel(self, name: str, unlisted: bool = False) -> ViewLike:
        ...

    def find_output_panel(self, name: str) -> 'Optional[ViewLike]':
        ...

    def destroy_output_panel(self, name: str) -> None:
        ...

    def active_panel(self) -> 'Optional[str]':
        ...

    def panels(self) -> 'List[str]':
        ...

    def views(self) -> 'List[ViewLike]':
        ...

    def get_output_panel(self, name: str):
        ...

    def show_input_panel(self, caption: str, initial_text: str, on_done, on_change, on_cancel) -> ViewLike:
        ...

    def show_quick_panel(self, items: 'List[Any]', on_select, flags: int,
                         selected_index: int, on_highlight: 'Optional[Any]') -> None:
        ...

    def is_sidebar_visible(self) -> bool:
        ...

    def set_sidebar_visible(self, flag: bool) -> None:
        ...

    def is_minimap_visible(self) -> bool:
        ...

    def set_minimap_visible(self, flag: bool) -> None:
        ...

    def is_status_bar_visible(self) -> bool:
        ...

    def set_status_bar_visible(self, flag: bool) -> None:
        ...

    def get_tabs_visible(self) -> bool:
        ...

    def set_tabs_visible(self, flag: bool) -> None:
        ...

    def is_menu_visible(self) -> bool:
        ...

    def set_menu_visible(self, flag: bool) -> None:
        ...

    def folders(self) -> 'List[str]':
        ...

    def project_file_name(self) -> 'Optional[str]':
        ...

    def project_data(self) -> 'Optional[dict]':
        ...

    def set_project_data(self, v: dict) -> None:
        ...

    def template_settings(self):
        ...

    def lookup_symbol_in_index(self, sym: str) -> 'List[str]':
        ...

    def lookup_symbol_in_open_files(self, sym: str) -> 'List[str]':
        ...

    def extract_variables(self) -> dict:
        ...

    def status_message(self, msg: str) -> None:
        ...
