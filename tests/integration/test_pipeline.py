from pathlib import Path

from validator.core.models import DocumentationFile
from validator.pipeline import collect_links

class TestPipeline:

    def test_collect_links_reads_relative_to_root(self, tmp_path):
        doc_file = tmp_path / 'sub' / 'file.md'
        doc_file.parent.mkdir(parents=True, exist_ok=True)
        doc_file.write_text('[Link](./target.md)')

        file_obj = DocumentationFile(path=Path('sub/file.md'), title='File')
        files = {Path('sub/file.md'): file_obj}

        collect_links(files, root_path=tmp_path)

        assert len(file_obj.links_out) == 1