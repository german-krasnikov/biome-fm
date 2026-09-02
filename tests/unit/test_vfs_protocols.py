import pytest

from biome_fm.models.vfs import LocalVFS, WritableVFS


def test_local_vfs_is_writable():
    assert isinstance(LocalVFS(), WritableVFS)


@pytest.mark.xfail(strict=True, reason="requires sftp-vfs batch: SFTPVfs missing exists/copy/move")
def test_sftp_vfs_is_writable():
    from biome_fm.models.sftp_vfs import SFTPVfs

    v = SFTPVfs.__new__(SFTPVfs)
    assert isinstance(v, WritableVFS)


@pytest.mark.xfail(strict=True, reason="requires sftp-vfs batch: RcloneVFS missing exists/stat/move")
def test_rclone_vfs_is_writable():
    from biome_fm.models.rclone_vfs import RcloneVFS

    v = RcloneVFS.__new__(RcloneVFS)
    assert isinstance(v, WritableVFS)
