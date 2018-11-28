import mock
import sys

from six.moves import builtins

original_import = __import__


@mock.patch.dict(sys.modules)
def test_init():
    import intracing
    assert hasattr(intracing, 'default_app_config')
    assert hasattr(intracing, 'configure_tracing')

    def custom_import(name, *args):
        if name in {'django', 'flask'}:
            raise ImportError
        return original_import(name, *args)

    with mock.patch.object(builtins, '__import__', custom_import):
        del sys.modules['intracing']
        import intracing
        assert not hasattr(intracing, 'default_app_config')
        assert not hasattr(intracing, 'configure_tracing')
