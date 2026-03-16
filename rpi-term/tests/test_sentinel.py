from rpi_term.modules import sentinel


def test_detect_completion_extracts_output():
    token = "abcd1234"
    captured = "hello\n__START_abcd1234\nline1\nline2\n__DONE_abcd1234:0\n"
    found, code, out = sentinel.detect_completion(captured, token)
    assert found is True
    assert code == 0
    assert out == "line1\nline2"
