import os
from os import getenv as env

UPLOAD_BRANCH = "dev"

if env('CIRCLE_BRANCH') == UPLOAD_BRANCH:
    os.system('python3 setup.py build')
    os.system('python3 setup.py sdist bdist_wheel')
    os.system('twine upload -u {} -p {} dist/*'.format(
        env('PYPI_USERNAME'), env('PYPI_PASSWORD')
    ))
