import json
from pathlib import Path

from validator.core.models import Link, LinkType, FileToValidate
from validator.serializers import link_to_dict, file_to_dict, files_to_json


class TestSerializers:
    def test_file_with_links_to_dict_success(self):
        ftv = FileToValidate(
            path=Path('TEST-README.md'),
            title='TEST-README-TITLE',
            links_out={
                Link('./guide.md', LinkType.INTERNAL, Path('TEST-README.md'), 1, 'section1')
            }
        )
        ftv_serialized = file_to_dict(ftv)

        assert len(ftv_serialized['links_out']) == 1
        assert ftv_serialized['links_out'][0]['uri'] == './guide.md'

    def test_link_to_dict_success(self):
        link = Link('./guide.md', LinkType.INTERNAL, Path('TEST-README.md'), 1, 'section1')
        expected = {
            'uri': './guide.md',
            'link_type': 'INTERNAL',
            'source_file': 'TEST-README.md',
            'line_number': 1,
            'anchor': 'section1',
        }
        actual = link_to_dict(link)

        assert actual == expected

    def test_files_to_json_success(self):
        ftv_list = [
            FileToValidate(path=Path('TEST-README.md'), title='readme'),
            FileToValidate(path=Path('TEST-LICENSE.md'), title='license'),
            ]
        ftv_list_serialized = files_to_json(ftv_list)

        ftv_list_json = json.loads(ftv_list_serialized)
        assert len(ftv_list_json) == 2
        assert ftv_list_json[0]['title'] == 'readme'
        assert ftv_list_json[1]['path'] == 'TEST-LICENSE.md'