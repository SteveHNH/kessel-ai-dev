import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "assess.py"
SPEC = importlib.util.spec_from_file_location("clowder_v2_assess", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def complete_source() -> str:
    return """
from app_common_python import get_v2_dependency_endpoint

def resolve():
    endpoint = get_v2_dependency_endpoint("rbac", "service")
    if endpoint is not None and endpoint.uri:
        return endpoint.uri, endpoint.ca_certificate, endpoint.authenticated
    return None

def request(config, headers):
    if config.authenticated and "Authorization" not in headers:
        headers["Authorization"] = "Bearer token"
    return Session().get(config.uri, headers=headers, verify=config.ca_certificate or True)
"""


def complete_go_source() -> str:
    return """
package client

import clowder "github.com/redhatinsights/app-common-go/pkg/api/v1"

func resolve() string {
	endpoint, ok := clowder.GetV2DependencyEndpoint("rbac", "service")
	if !ok || endpoint.Uri == "" {
		return ""
	}
	_ = endpoint.Authenticated
	if endpoint.CaCertificate != nil {
		_ = *endpoint.CaCertificate
	}
	return endpoint.Uri
}
"""


def test_complete_python_usage_passes_mechanical_checks(tmp_path):
    write(tmp_path, "app/client.py", complete_source())
    write(tmp_path, "pyproject.toml", 'dependencies = ["app-common-python~=0.3.0"]\n')
    write(tmp_path, "requirements.txt", "app-common-python==0.3.0\n")

    result = MODULE.analyze(tmp_path, "after")

    assert result.passed
    assert result.helper_calls
    assert not result.errors


def test_dictionary_endpoint_access_is_error(tmp_path):
    write(
        tmp_path,
        "client.py",
        """
from app_common_python import get_v2_dependency_endpoint
endpoint = get_v2_dependency_endpoint("rbac", "service")
uri = endpoint.get("uri")
auth = endpoint["authenticated"]
""",
    )
    write(tmp_path, "requirements.txt", "app-common-python==0.3.0\n")

    result = MODULE.analyze(tmp_path, "after")

    assert not result.passed
    assert sum("dictionary" in finding.message for finding in result.errors) == 2


def test_stale_hermetic_version_is_error(tmp_path):
    write(tmp_path, "app/client.py", complete_source())
    write(tmp_path, "pyproject.toml", 'dependencies = ["app-common-python~=0.3.0"]\n')
    write(tmp_path, ".hermetic_builds/requirements.txt", "app-common-python==0.2.9\n")

    result = MODULE.analyze(tmp_path, "after")

    messages = [finding.message for finding in result.errors]
    assert any("below 0.3.0" in message for message in messages)
    assert any("disagree" in message for message in messages)


def test_before_phase_allows_no_helpers(tmp_path):
    write(tmp_path, "app/client.py", "def request():\n    return None\n")

    result = MODULE.analyze(tmp_path, "before")

    assert result.passed
    assert not result.helper_calls


def test_after_phase_requires_v2_helper(tmp_path):
    write(
        tmp_path,
        "app/client.py",
        "from app_common_python import DependencyEndpoints\n\ndef request():\n    return DependencyEndpoints\n",
    )

    result = MODULE.analyze(tmp_path, "after")

    assert not result.passed
    assert any(
        "No Python Clowder V2 helper" in finding.message for finding in result.errors
    )


def test_non_python_repo_warns_without_failing(tmp_path):
    write(tmp_path, "client.go", "package client\n")

    result = MODULE.analyze(tmp_path, "after")

    assert result.passed
    assert any("language-specific" in finding.message for finding in result.warnings)


def test_complete_go_usage_passes_mechanical_checks(tmp_path):
    write(tmp_path, "client/client.go", complete_go_source())
    write(
        tmp_path,
        "go.mod",
        "module example.com/consumer\n\n"
        "require github.com/redhatinsights/app-common-go "
        "v1.6.10-0.20260723122147-856fbc993206\n",
    )

    result = MODULE.analyze(tmp_path, "after")

    assert result.passed
    assert any("GetV2DependencyEndpoint" in call for call in result.helper_calls)
    assert result.go_dependency_versions == {
        "go.mod": ["v1.6.10-0.20260723122147-856fbc993206"]
    }
    assert not result.errors


def test_after_phase_requires_go_v2_helper(tmp_path):
    write(
        tmp_path,
        "client.go",
        'package client\n\nimport _ "github.com/redhatinsights/app-common-go/pkg/api/v1"\n',
    )
    write(
        tmp_path,
        "go.mod",
        "module example.com/consumer\n\n"
        "require github.com/redhatinsights/app-common-go v1.6.9\n",
    )

    result = MODULE.analyze(tmp_path, "after")

    assert not result.passed
    assert any("app-common-go V2 helper" in finding.message for finding in result.errors)


def test_go_helper_definition_is_not_consumer_usage(tmp_path):
    write(
        tmp_path,
        "client.go",
        "package client\n\n"
        "func GetV2DependencyEndpoint(app, name string) (string, bool) {\n"
        '\treturn "", false\n'
        "}\n",
    )

    result = MODULE.analyze(tmp_path, "after")

    assert result.passed
    assert not result.helper_calls


def test_go_v2_uri_is_required(tmp_path):
    write(
        tmp_path,
        "client.go",
        complete_go_source().replace("\treturn endpoint.Uri\n", "\treturn \"set\"\n").replace(
            '\tif !ok || endpoint.Uri == "" {\n', "\tif !ok {\n"
        ),
    )
    write(
        tmp_path,
        "go.mod",
        "module example.com/consumer\n\n"
        "require github.com/redhatinsights/app-common-go "
        "v1.6.10-0.20260723122147-856fbc993206\n",
    )

    result = MODULE.analyze(tmp_path, "after")

    assert not result.passed
    assert any("'.Uri'" in finding.message for finding in result.errors)


def test_report_exposes_human_review_section(tmp_path):
    write(tmp_path, "app/client.py", complete_source())
    write(tmp_path, "requirements.txt", "app-common-python==0.3.0\n")

    report = MODULE.render_markdown(MODULE.analyze(tmp_path, "after"))

    assert "### Verified Evidence" in report
    assert "### Mechanical Errors" in report
    assert "### Human Verification Required" in report
