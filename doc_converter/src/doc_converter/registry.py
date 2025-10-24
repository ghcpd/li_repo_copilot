"""Plugin registry and format detection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import entry_points
from pathlib import Path
from typing import Iterator, Mapping, MutableMapping, Sequence

from .exceptions import PluginRegistrationError, UnsupportedFormatError
from .plugins.base import FormatPlugin, HEADER_SAMPLE_BYTES


@dataclass(slots=True)
class RegisteredPlugin:
    name: str
    plugin: FormatPlugin


class PluginRegistry:
    """Manage format plugins and provide detection helpers."""

    def __init__(self) -> None:
        self._plugins: MutableMapping[str, FormatPlugin] = {}

    def __iter__(self) -> Iterator[RegisteredPlugin]:
        for name, plugin in self._plugins.items():
            yield RegisteredPlugin(name=name, plugin=plugin)

    def register(self, plugin: FormatPlugin) -> None:
        if plugin.name in self._plugins:
            raise PluginRegistrationError(f"Plugin with name '{plugin.name}' already registered")

        self._plugins[plugin.name] = plugin

    def unregister(self, name: str) -> None:
        self._plugins.pop(name, None)

    def names(self) -> Sequence[str]:
        return tuple(self._plugins.keys())

    def get(self, name: str) -> FormatPlugin:
        try:
            return self._plugins[name]
        except KeyError as exc:
            raise UnsupportedFormatError(f"No plugin registered under name '{name}'") from exc

    def detect(self, path: Path) -> FormatPlugin:
        header = path.read_bytes()[:HEADER_SAMPLE_BYTES]
        for plugin in self._plugins.values():
            if plugin.matches(path, header):
                return plugin

        raise UnsupportedFormatError(f"No plugin can handle file '{path}'")

    def load_builtin(self) -> None:
        """Load the plugins that ship with the package."""

        module_names = [
            "doc_converter.plugins.docx_parser",
            "doc_converter.plugins.doc_parser",
            "doc_converter.plugins.html_parser",
            "doc_converter.plugins.text_parser",
        ]

        for module_path in module_names:
            module = import_module(module_path)
            for candidate in getattr(module, "PLUGINS", []):
                self.register(candidate)

    def load_entry_points(self, group: str = "doc_converter.plugins") -> None:
        """Load third-party plugins exposed through entry-points."""

        discovered = entry_points().select(group=group)
        for entry in discovered:
            plugin = entry.load()  # type: ignore[assignment]
            if isinstance(plugin, type) and issubclass(plugin, FormatPlugin):
                instance = plugin()
            elif isinstance(plugin, FormatPlugin):
                instance = plugin
            else:
                raise PluginRegistrationError(
                    f"Entry point '{entry.name}' did not return a FormatPlugin (got {type(plugin)!r})"
                )
            self.register(instance)

    def batch_preload(self, mapping: Mapping[FormatPlugin, Sequence[Path]]) -> None:
        for plugin, paths in mapping.items():
            plugin.batch_preload(paths)


def default_registry() -> PluginRegistry:
    registry = PluginRegistry()
    registry.load_builtin()
    registry.load_entry_points()
    return registry
