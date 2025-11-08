import importlib
import logging
import pytest

# Reload modules to pick up env changes
def _reload_modules():
    import picklechecker.config as cfg
    importlib.reload(cfg)
    return importlib.reload(importlib.import_module("picklechecker.huggingface.client"))


def test_init_warns_when_no_hf_token(monkeypatch, caplog):
    monkeypatch.setenv("HF_TOKEN", "")
    hf_mod = _reload_modules()
    with caplog.at_level(logging.WARNING):
        client = hf_mod.HuggingfaceClient(download_dir="tmp")
    assert "HF_TOKEN is not set" in caplog.text


def test_init_no_warning_when_hf_token_set(monkeypatch, caplog):
    monkeypatch.setenv("HF_TOKEN", "test-token")
    hf_mod = _reload_modules()
    with caplog.at_level(logging.WARNING):
        client = hf_mod.HuggingfaceClient(download_dir="tmp")
    assert "HF_TOKEN is not set" not in caplog.text


def test_download_repo_with_token_and_patterns(monkeypatch, caplog):
    monkeypatch.setenv("HF_TOKEN", "token-xyz")
    hf_mod = _reload_modules()

    called = {}

    def fake_snapshot_download(**kwargs):
        called.update(kwargs)
        return "/tmp/fake-repo"

    monkeypatch.setattr(hf_mod, "snapshot_download", fake_snapshot_download)

    caplog.set_level(logging.DEBUG)
    client = hf_mod.HuggingfaceClient(download_dir="dl_dir")
    client.download_repo("owner/repo", allow_patterns=["*.pt"], ignore_patterns=["*.metadata"])
    assert called["repo_id"] == "owner/repo"
    assert called["local_dir"] == "dl_dir"
    assert called["allow_patterns"] == ["*.pt"]
    assert called["ignore_patterns"] == ["*.metadata"]
    assert called["token"] == "token-xyz"
    assert "Using token to authenticate" in caplog.text


def test_download_repo_without_token(monkeypatch, caplog):
    monkeypatch.setenv("HF_TOKEN", "")
    hf_mod = _reload_modules()

    called = {}

    def fake_snapshot_download(**kwargs):
        called.update(kwargs)
        return "/tmp/no-token-repo"

    monkeypatch.setattr(hf_mod, "snapshot_download", fake_snapshot_download)

    caplog.set_level(logging.DEBUG)
    client = hf_mod.HuggingfaceClient(download_dir="dl_no_token")
    client.download_repo("owner/repo2", allow_patterns=[], ignore_patterns=[])
    assert called["repo_id"] == "owner/repo2"
    assert called["local_dir"] == "dl_no_token"
    assert "token" not in called
    assert "Using token to authenticate" not in caplog.text

def test_download_file_with_token(monkeypatch, caplog):
    monkeypatch.setenv("HF_TOKEN", "file-token")
    hf_mod = _reload_modules()

    called = {}

    def fake_hf_hub_download(**kwargs):
        called.update(kwargs)
        return "/tmp/fake-file"

    monkeypatch.setattr(hf_mod, "hf_hub_download", fake_hf_hub_download)

    caplog.set_level(logging.DEBUG)
    client = hf_mod.HuggingfaceClient(download_dir="files_dir")
    client.download_file("my/repo", "config.json")
    assert called["repo_id"] == "my/repo"
    assert called["filename"] == "config.json"
    assert called["token"] == "file-token"
    assert "Using token to authenticate" in caplog.text


def test_download_file_without_token(monkeypatch, caplog):
    monkeypatch.setenv("HF_TOKEN", "")
    hf_mod = _reload_modules()

    called = {}

    def fake_hf_hub_download(**kwargs):
        called.update(kwargs)
        return "/tmp/no-token-file"

    monkeypatch.setattr(hf_mod, "hf_hub_download", fake_hf_hub_download)

    caplog.set_level(logging.DEBUG)
    client = hf_mod.HuggingfaceClient(download_dir="files_no_token")
    client.download_file("my/repo", "config.json")
    assert "token" not in called
    assert "Using token to authenticate" not in caplog.text


def test_download_file_propagates_exception_as_client_error(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "err-token")
    hf_mod = _reload_modules()

    def raising_file(*args, **kwargs):
        raise RuntimeError("file download failed")

    monkeypatch.setattr(hf_mod, "hf_hub_download", raising_file)
    client = hf_mod.HuggingfaceClient(download_dir="err_files")

    with pytest.raises(hf_mod.HuggingfaceClientError) as excinfo:
        client.download_file("bad/repo", "missing.bin")

    assert isinstance(excinfo.value.__cause__, RuntimeError)