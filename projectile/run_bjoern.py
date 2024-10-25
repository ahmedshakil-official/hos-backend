import os
import signal

from django.core.wsgi import get_wsgi_application

import bjoern # pip install bjoern
# https://github.com/jonashaag/bjoern

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projectile.settings")

APPLICATION = get_wsgi_application()

NUM_WORKERS = 1 # match it according to the CPU core
WORKER_P_IDS = []

bjoern.listen(APPLICATION, '0.0.0.0', 8000)
for _ in range(NUM_WORKERS):
    pid = os.fork()

    if pid > 0:
        # in master
        WORKER_P_IDS.append(pid)

    elif pid == 0:
        # in worker
        try:
            bjoern.run()

        except KeyboardInterrupt:
            pass

        exit()

try:
    for _ in range(NUM_WORKERS):
        os.wait()

except KeyboardInterrupt:
    for pid in WORKER_P_IDS:
        os.kill(pid, signal.SIGINT)
