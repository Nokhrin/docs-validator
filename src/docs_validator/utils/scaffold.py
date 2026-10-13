import logging
import shutil
import stat
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import TextIO, Callable

log = logging.getLogger(__name__)

TEMPLATE_PACKAGE = "docs_validator.utils.templates"


@dataclass(frozen=True)
class TemplatesSpec:
    source_filename: str
    target_path: Path


@dataclass(frozen=True)
class TemplateTask:
    enabled: bool
    spec: TemplatesSpec
    post_process: Callable[[Path], None] | None = None


def _set_executable(path: Path) -> None:
    """Does chmod +x"""
    current_mode = path.stat().st_mode
    path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def process_template(task: TemplateTask, force: bool, stream: TextIO):
    target = task.spec.target_path

    if target.exists() and not force:
        msg = f"File {target} already exists. Use --force to overwrite.\n"
        stream.write(msg)
        log.warning(msg.strip())
        return 1
    try:
        src_resource = files(TEMPLATE_PACKAGE).joinpath(task.spec.source_filename)
        if not src_resource.is_file():
            raise FileNotFoundError(
                f"Template '{task.spec.source_filename}' not found in package."
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        with src_resource.open("rb") as src, target.open("wb") as dst:
            shutil.copyfileobj(src, dst)

        if task.post_process:
            task.post_process(target)

        stream.write(f"Created: {target}\n")
        log.info("Created file: %s", target)

        return 0

    except (OSError, FileNotFoundError) as e:
        msg = f"Failed to write {target} from template '{task.spec.source_filename}': {e}\n"
        stream.write(msg)
        log.error(msg.strip())
        return 1


@dataclass(frozen=True)
class SetupOptions:
    force: bool
    config: bool
    github: bool
    gitlab: bool
    precommit: bool

    def __post_init__(self):
        if not any(
            (
                self.config,
                self.github,
                self.gitlab,
                self.precommit,
            )
        ):
            raise ValueError("Setup requires at least one option")


def execute_setup(
    options: SetupOptions,
    stream: TextIO,
) -> int:
    tasks = [
        TemplateTask(
            options.config,
            TemplatesSpec(".docs_validator.toml", Path(".docs_validator.toml")),
        ),
        TemplateTask(
            options.github,
            TemplatesSpec(
                ".github.workflows.docs_validation.yml",
                Path(".github/workflows/docs_validation.yml"),
            ),
        ),
        TemplateTask(
            options.gitlab,
            TemplatesSpec(".gitlab-ci.yml", Path(".gitlab-ci.yml")),
        ),
        TemplateTask(
            options.precommit,
            TemplatesSpec(
                ".githooks.pre-commit.docs_validator",
                Path(".githooks/pre-commit"),
            ),
            post_process=_set_executable,
        ),
    ]

    for task in tasks:
        if task.enabled:
            result = process_template(task, options.force, stream)
            if result != 0:
                return result

    return 0
