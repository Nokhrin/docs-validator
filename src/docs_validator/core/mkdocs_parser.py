import logging
from pathlib import Path

from yaml import safe_load, YAMLError

log = logging.getLogger(__name__)

def get_nav_roots(mkdocs_yml_path: Path) -> set[Path]:
    """Returns a set of file paths listed in the navigation menu."""
    nav_files: set[Path] = set()

    if not mkdocs_yml_path.exists():
        log.debug('mkdocs.yml not found: %s', mkdocs_yml_path)
        return nav_files

    try:
        with open(mkdocs_yml_path, 'r', encoding='utf-8') as f:
            config = safe_load(f)
    except YAMLError as err:
        log.error('Failed to read mkdocs.yml: %s', err)
        return nav_files

    nav_section = config.get('nav') if isinstance(config, dict) else None
    if not nav_section:
        log.debug('Navigation section not found in %s', mkdocs_yml_path)
        return nav_files

    def _walk_nav(node) -> None:
        """Recursively walks the navigation structure."""
        if isinstance(node, str):
            p = Path(node)
            if not p.suffix:
                p = p.with_suffix('.md')
            nav_files.add(p)
        elif isinstance(node, dict):
            for value in node.values():
                _walk_nav(value)
        elif isinstance(node, list):
            for item in node:
                _walk_nav(item)

    _walk_nav(nav_section)
    log.debug('Extracted %d paths from mkdocs.yml: %s', len(nav_files), nav_files)
    return nav_files