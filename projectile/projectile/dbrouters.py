import random
import threading
from django.utils.deprecation import MiddlewareMixin

REQUEST_CFG = threading.local()


class RouterMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.method == 'GET':
            REQUEST_CFG.cfg = 'GET'
        return None

    def process_response(self, request, response):
        if hasattr(REQUEST_CFG, 'cfg'):
            del REQUEST_CFG.cfg
        return response


class DatabaseRouter:

    def _default_db(self):
        replicas = ['replica_01', 'replica_02']
        if hasattr(REQUEST_CFG, 'cfg'):
            if REQUEST_CFG.cfg == 'GET':
                return random.choice(replicas)
        return 'default'

    def db_for_read(self, model, **hints):
        return self._default_db()

    def db_for_write(self, model, **hints):
        """
        Writes always go to default.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the default/replica pool.
        """
        db_list = ('default', 'replica_01', 'replica_02', 'no-pooling')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None
