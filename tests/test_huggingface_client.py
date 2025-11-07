import importlib
import logging

import pytest

def _reload_modules():
    # reload config first so HF_TOKEN is picked up, then reload the client module
    import picklechecker.config as cfg  # noqa: F401
    importlib.reload(cfg)
    hf_mod = importlib.reload(importlib.import_module("picklechecker.huggingface.client"))
    return hf_mod

def test_download_repo_includes_token_when_set(monkeypatch, caplog):
    monkeypatch.setenv("HF_TOKEN", "token-xyz")
    hf_mod = _reload_modules()

    called = {}

    def fake_snapshot_download(**kwargs):
        called.update(kwargs)
        return "/tmp/fake-repo"

    monkeypatch.setattr(hf_mod, "snapshot_download", fake_snapshot_download)

    caplog.set_level(logging.INFO)
    client = hf_mod.HuggingfaceClient(download_dir="dl_dir")
    client.download_repo("owner/repo", allow_patterns=["*.pt", "*.bin"])

    assert called["repo_id"] == "owner/repo"
    assert called["local_dir"] == "dl_dir"
    assert called["allow_patterns"] == ["*.pt", "*.bin"]
    assert called.get("token") == "token-xyz"
    assert "fake-repo" in caplog.text


def test_download_repo_omits_token_when_not_set(monkeypatch):
    # Ensure HF_TOKEN is present in the environment but empty before reloading config.
    # This prevents python-dotenv from repopulating it from a .env file during import.
    monkeypatch.setenv("HF_TOKEN", "")
    hf_mod = _reload_modules()

    called = {}

    def fake_snapshot_download(**kwargs):
        called.update(kwargs)
        return "/tmp/no-token"

    monkeypatch.setattr(hf_mod, "snapshot_download", fake_snapshot_download)

    client = hf_mod.HuggingfaceClient(download_dir="dl_no_token")
    client.download_repo("owner/repo2", allow_patterns=[])

    assert called["repo_id"] == "owner/repo2"
    assert called["local_dir"] == "dl_no_token"
    # token should not be present in kwargs when HF_TOKEN is unset
    assert "token" not in called


def test_download_file_calls_hf_hub_download_and_returns_path(monkeypatch, caplog):
    monkeypatch.setenv("HF_TOKEN", "file-token")
    hf_mod = _reload_modules()

    called = {}

    def fake_hf_hub_download(repo_id, filename, token, local_dir, etag_timeout):
        called.update(
            {
                "repo_id": repo_id,
                "filename": filename,
                "token": token,
                "local_dir": local_dir,
                "etag_timeout": etag_timeout,
            }
        )
        return f"{local_dir}/{filename}"

    monkeypatch.setattr(hf_mod, "hf_hub_download", fake_hf_hub_download)

    caplog.set_level(logging.INFO)
    client = hf_mod.HuggingfaceClient(download_dir="files_dir")
    client.download_file("my/repo", "config.json")

    assert called["repo_id"] == "my/repo"
    assert called["filename"] == "config.json"
    assert called["token"] == "file-token"
    assert called["local_dir"] == "files_dir"
    assert "config.json" in caplog.text


def test_download_repo_propagates_exception_as_client_error(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "err-token")
    hf_mod = _reload_modules()

    def raising_snapshot(*args, **kwargs):
        raise ValueError("underlying failure")

    monkeypatch.setattr(hf_mod, "snapshot_download", raising_snapshot)
    client = hf_mod.HuggingfaceClient(download_dir="err_dir")

    with pytest.raises(hf_mod.HuggingfaceClientError) as excinfo:
        client.download_repo("bad/repo", allow_patterns=[])

    # original exception should be chained
    assert isinstance(excinfo.value.__cause__, ValueError)


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