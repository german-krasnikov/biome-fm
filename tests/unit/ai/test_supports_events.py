"""I12: supports_events property on AIProviderProtocol."""
from biome_fm.ai.provider import NoOpProvider


def test_noop_does_not_support_events():
    assert NoOpProvider().supports_events is False


def test_cli_provider_with_parse_events_returns_true():
    from biome_fm.ai.cli.backend_def import BackendDef
    from biome_fm.ai.cli.cli_provider import CliProvider

    backend = BackendDef(
        name="x", binary="echo", models=("m",),
        build_argv=lambda p, m: ["echo", p],
        parse_line=lambda l: l,
        parse_events=lambda l: [("text", l)],
    )
    assert CliProvider(backend).supports_events is True


def test_cli_provider_without_parse_events_returns_false():
    from biome_fm.ai.cli.backend_def import BackendDef
    from biome_fm.ai.cli.cli_provider import CliProvider

    backend = BackendDef(
        name="y", binary="echo", models=("m",),
        build_argv=lambda p, m: ["echo", p],
        parse_line=lambda l: l,
        parse_events=None,
    )
    assert CliProvider(backend).supports_events is False
