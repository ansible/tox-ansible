import io
from setuptools import setup, find_packages


setup(
    name='tox-ansible-collection',
    description='Auto-generate environments for molecule role testing',
    long_description=io.open('README.md', encoding='utf-8').read(),
    author='Greg Hellings',
    author_email='greg.hellings@gmail.com',
    url='https://github.com/greg-hellings/tox-ansible-collection',
    license='GPLv3',
    version='0.1',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    entry_points={
        'tox': ['ansible-collection = tox_ansible_collection.hooks'],
    },
    install_requires=['tox>=2.0', 'pyyaml'],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Framework :: tox',
        'License :: OSI Approved :: GPLv3',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Testing'
    ]
)
