"""SettingsPresenter — drives settings dialog. No Qt imports."""
from __future__ import annotations

from typing import Protocol

from biome_fm.config import Config


class SettingsViewProtocol(Protocol):
    def set_theme(self, name: str) -> None: ...
    def get_theme(self) -> str: ...
    def set_show_hidden(self, val: bool) -> None: ...
    def get_show_hidden(self) -> bool: ...
    def set_sync_browsing(self, val: bool) -> None: ...
    def get_sync_browsing(self) -> bool: ...
    def set_file_type_colors(self, val: bool) -> None: ...
    def get_file_type_colors(self) -> bool: ...
    def set_ai_provider(self, name: str) -> None: ...
    def get_ai_provider(self) -> str: ...
    def set_ai_keys(self, claude: str, openai: str) -> None: ...
    def get_ai_keys(self) -> tuple[str, str]: ...
    def set_ollama(self, url: str, model: str) -> None: ...
    def get_ollama(self) -> tuple[str, str]: ...
    def set_themes_list(self, names: list[str]) -> None: ...
    def set_plugins_list(self, names: list[str]) -> None: ...
    def set_glass(self, val: bool) -> None: ...
    def get_glass(self) -> bool: ...


class SettingsPresenter:
    def __init__(
        self,
        config: Config,
        view: SettingsViewProtocol,
        available_themes: list[str] | None = None,
        available_plugins: list[str] | None = None,
    ) -> None:
        self._config = config
        self._view = view
        self._load(available_themes or [], available_plugins or [])

    def _load(self, themes: list[str], plugins: list[str]) -> None:
        self._view.set_themes_list(themes)
        self._view.set_plugins_list(plugins)
        self._view.set_theme(self._config.theme)
        self._view.set_show_hidden(self._config.show_hidden)
        self._view.set_sync_browsing(self._config.sync_browsing)
        self._view.set_file_type_colors(self._config.file_type_colors)
        self._view.set_ai_provider(self._config.ai_default_provider)
        self._view.set_ai_keys(self._config.ai_claude_key, self._config.ai_openai_key)
        self._view.set_ollama(self._config.ai_ollama_url, self._config.ai_ollama_model)
        self._view.set_glass(self._config.glass)

    def apply(self) -> Config:
        """Read view state → update config → return it."""
        self._config.theme = self._view.get_theme()
        self._config.show_hidden = self._view.get_show_hidden()
        self._config.sync_browsing = self._view.get_sync_browsing()
        self._config.file_type_colors = self._view.get_file_type_colors()
        self._config.ai_default_provider = self._view.get_ai_provider()
        claude, openai = self._view.get_ai_keys()
        self._config.ai_claude_key = claude
        self._config.ai_openai_key = openai
        url, model = self._view.get_ollama()
        self._config.ai_ollama_url = url
        self._config.ai_ollama_model = model
        self._config.glass = self._view.get_glass()
        return self._config
