from validator.rules import ExternalLinkValidator


class TestExternalLinkValidator:

    def test_is_host_ignored_exact_match_true(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('example.com') is True

    def test_is_host_ignored_subdomain_match_true(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('sub.example.com') is True

    def test_is_host_ignored_nested_subdomain_match_true(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('a.b.example.com') is True

    def test_is_host_ignored_different_domain_false(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('other.com') is False

    def test_is_host_ignored_partial_match_false(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('example.com.evil.com') is False

    def test_is_host_ignored_localhost_exact_match_true(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['localhost'])
        assert validator._is_host_ignored('localhost') is True

    def test_is_host_ignored_localhost_subdomain_match_true(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['localhost'])
        assert validator._is_host_ignored('test.localhost') is True

    def test_is_host_ignored_empty_hostname_false(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('') is False