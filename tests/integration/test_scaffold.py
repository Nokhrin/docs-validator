import io

import pytest

from docs_validator.utils.scaffold import execute_setup, SetupOptions


def test_execute_setup_creates_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    options = SetupOptions(
        force=False,
        config=True,
        github=True,
        gitlab=False,
        precommit=False,
    )

    stream = io.StringIO()
    result = execute_setup(options, stream)

    assert result == 0
    assert (tmp_path / ".github" / "workflows" / "docs_validation.yml").exists()
    assert (tmp_path / ".docs_validator.toml").exists()
    assert not (tmp_path / ".gitlab-ci.yml").exists()

    output = stream.getvalue()
    assert "Created:" in output


def test_execute_setup_fails_on_existing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".docs_validator.toml").write_text("existing content")

    options = SetupOptions(
        force=False,
        config=True,
        github=False,
        gitlab=False,
        precommit=False,
    )

    stream = io.StringIO()
    result = execute_setup(options, stream)

    assert result == 1
    assert (tmp_path / ".docs_validator.toml").read_text() == "existing content"
    assert "already exists" in stream.getvalue()


def test_execute_setup_overwrites_with_force(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".docs_validator.toml").write_text("existing content")

    options = SetupOptions(
        force=True,
        config=True,
        github=False,
        gitlab=False,
        precommit=False,
    )

    stream = io.StringIO()
    result = execute_setup(options, stream)

    assert result == 0
    assert (tmp_path / ".docs_validator.toml").read_text() != "existing content"
    assert "Created:" in stream.getvalue()


def test_execute_setup_requires_at_least_one_option(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        SetupOptions(
            force=False,
            config=False,
            github=False,
            gitlab=False,
            precommit=False,
        )
