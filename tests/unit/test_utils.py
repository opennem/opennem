from example.utils import add_example


def test_addition():
    expected = 4
    result = add_example(1, 3)

    assert expected == result
