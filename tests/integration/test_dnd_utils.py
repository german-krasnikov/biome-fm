"""Integration tests for views.dnd_utils."""


def test_make_path_mime_sets_all_types(qtbot):
    from biome_fm.views.dnd_utils import make_path_mime

    mime = make_path_mime(["/tmp/a.txt", "/tmp/b.txt"])
    assert mime.hasText()
    assert mime.hasUrls()
    assert len(mime.urls()) == 2


def test_make_path_mime_no_urls(qtbot):
    from biome_fm.views.dnd_utils import make_path_mime

    mime = make_path_mime(["/tmp/a.txt"], urls=False)
    assert not mime.hasUrls()
    assert mime.hasText()
