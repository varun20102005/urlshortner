from app.utils import encode_base62


def test_encode_zero():
    assert encode_base62(0) == "0"


def test_encode_one():
    assert encode_base62(1) == "1"


def test_encode_62():
    assert encode_base62(62) == "10"


def test_encode_positive_number():
    result = encode_base62(12345)

    assert isinstance(result, str)
    assert len(result) > 0