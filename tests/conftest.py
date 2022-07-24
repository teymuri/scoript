import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--asset",
        action="store",
        help="Runs no tests. Only generates test assets for comma seperated (without white space) names of functions."
    )

@pytest.fixture
def asset(request):
    return request.config.getoption("--asset")
