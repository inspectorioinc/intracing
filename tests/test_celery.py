import mock
from celery.signals import worker_init

from .utils import get_flask_app


class TestFlaskTracingHelper(object):

    @mock.patch('celery.signals.worker_init')
    def test_no_celery(self, *mocks):
        import celery.signals
        del celery.signals.worker_init
        get_flask_app()

    @mock.patch('intracing.base.TracingHelper.apply_patches')
    def test_celery_apply_patches(self, apply_patches_mock):
        worker_init.receivers = []
        get_flask_app()
        worker_init.send(None)
        apply_patches_mock.assert_called_once_with()
