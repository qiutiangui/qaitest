import pytest


class TestSample:
    """示例测试类"""

    def test_example(self):
        assert 1 + 1 == 2

    def test_string(self):
        assert "hello" in "hello world"
