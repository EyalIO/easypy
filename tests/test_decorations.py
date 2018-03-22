import pytest

from easypy.decorations import deprecated_arguments, kwargs_resilient


def test_deprecated_arguments():
    @deprecated_arguments(foo='bar')
    def func(bar):
        return 'bar is %s' % (bar,)

    assert func(1) == func(foo=1) == func(bar=1) == 'bar is 1'

    with pytest.raises(TypeError):
        func(foo=1, bar=2)

    with pytest.raises(TypeError):
        func(1, foo=2)


def test_kwargs_resilient():
    @kwargs_resilient
    def foo(a, b):
        return [a, b]

    assert foo(1, b=2, c=3, d=4) == [1, 2]

    @kwargs_resilient
    def bar(a, b, **kwargs):
        return [a, b, kwargs]

    assert bar(1, b=2, c=3, d=4) == [1, 2, {'c': 3, 'd': 4}]

    @kwargs_resilient(negligible='d')
    def baz(a, b):
        return [a, b]

    # Should only be neglect `d` - not to `c`
    with pytest.raises(TypeError):
        baz(1, b=2, c=3, d=4)
    assert baz(1, b=2, d=4) == [1, 2]

    @kwargs_resilient(negligible=['b', 'd'])
    def qux(a, b, **kwargs):
        return [a, b, kwargs]

    # Should be passing b because it's in the function signature
    # Should be passing c because it's not in `negligible`
    # Should not be passing d because it's in `negligible` and not in the function signature
    assert qux(1, b=2, c=3, d=4) == [1, 2, {'c': 3}]
