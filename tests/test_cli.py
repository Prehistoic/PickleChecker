import logging
from unittest import mock

import pytest
from click.testing import CliRunner

import picklechecker.cli as cli


def test_directory_option_calls_logger_info(tmp_path, monkeypatch):
    runner = CliRunner()
    fake_logger = mock.Mock()
    monkeypatch.setattr(cli, "logger", fake_logger)

    result = runner.invoke(cli.main, ["--directory", str(tmp_path)])
    assert result.exit_code == 0
    # Expect an info call indicating a directory scan was launched
    fake_logger.info.assert_any_call("Launching directory scan: %s", str(tmp_path))


def test_model_option_uses_huggingface_client(monkeypatch):
    runner = CliRunner()

    calls = {}

    class FakeClient:
        def __init__(self, download_dir):
            calls["download_dir"] = download_dir

        def download_repo(self, repo_name, allow_patterns):
            calls["repo_name"] = repo_name
            calls["allow_patterns"] = allow_patterns

    fake_logger = mock.Mock()
    monkeypatch.setattr(cli, "HuggingfaceClient", FakeClient)
    monkeypatch.setattr(cli, "logger", fake_logger)

    result = runner.invoke(cli.main, ["--model", "owner/repo"])
    assert result.exit_code == 0
    assert calls["repo_name"] == "owner/repo"
    assert calls["allow_patterns"] == []


def test_model_download_failure_exits_with_error(monkeypatch):
    runner = CliRunner()

    class FailingClient:
        def __init__(self, download_dir):
            pass

        def download_repo(self, repo_name, allow_patterns):
            raise RuntimeError("download failed")

    fake_logger = mock.Mock()
    monkeypatch.setattr(cli, "HuggingfaceClient", FailingClient)
    monkeypatch.setattr(cli, "logger", fake_logger)

    result = runner.invoke(cli.main, ["--model", "owner/repo"])
    # CLI should catch the exception and exit with non-zero
    assert result.exit_code != 0
    # An error log should have been emitted
    fake_logger.error.assert_called()


def test_verbose_flag_sets_global_logging_level(monkeypatch, tmp_path):
    runner = CliRunner()
    set_level = mock.Mock()
    monkeypatch.setattr(cli, "set_global_logging_level", set_level)
    fake_logger = mock.Mock()
    monkeypatch.setattr(cli, "logger", fake_logger)

    result = runner.invoke(cli.main, ["--verbose", "--directory", str(tmp_path)])
    assert result.exit_code == 0
    set_level.assert_called_once_with(logging.DEBUG)