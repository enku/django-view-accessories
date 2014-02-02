from view_accessories import __version__

from setuptools import setup

setup(
    name='django-view-accessories',
    description='Django View Accessories',
    long_description='An alternative to Django\'s Class-based views.',
    author='Albert Hopkins',
    author_email='marduk@python.net',
    license='BSD',
    install_requires=['Django>=1.5.5,<1.7'],
    packages=['view_accessories'],
    version=__version__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Framework :: Django',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
    ],
)
