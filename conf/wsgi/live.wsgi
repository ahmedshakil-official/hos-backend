import os
import sys
import site

import dotenv

# The home directory of the user
USERHOME_DIR = '/home/django'
# Load environment vars using dotenv
dotenv.read_dotenv(os.path.join(USERHOME_DIR, '.env'))

# Django directory, where manage.py resides
DPROJECT_DIR = os.path.join(USERHOME_DIR, 'project/projectile')

# Site-packages under virtualenv directory
SITEPACK_DIR = os.path.join(USERHOME_DIR, 'env/lib/python3.12/site-packages')
site.addsitedir(SITEPACK_DIR)

sys.path.append(DPROJECT_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'projectile.settings_live'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()