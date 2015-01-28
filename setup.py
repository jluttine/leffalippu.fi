from setuptools import setup, find_packages
from leffalippu import __version__

setup(
    name='leffalippu',
    version=__version__,

    url='http://leffalippu.fi/',
    author='Jaakko Luttinen',
    author_email='jaakko.luttinen@iki.fi',

    packages=find_packages(),
    include_package_data=True,
    scripts=['scripts/manage.py'],

    install_requires=(
        'django>=1.7',
    )
)
