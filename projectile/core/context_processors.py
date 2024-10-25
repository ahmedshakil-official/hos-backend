import os
from validator_collection import checkers
from common.helpers import ReleaseTagManager


#pylint: disable=unused-argument
def config(request):
    _dict = {
        'COUNTRY': 'bd',
        'LANGUAGE': 'en',
    }
    return _dict
