from genai_project import __version__


def test_version():
    assert isinstance(__version__, str)
    assert __version__ == "0.1.0"
