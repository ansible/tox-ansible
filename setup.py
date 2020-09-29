import io

from setuptools import find_packages, setup

setup(
    name="tox-ansible",
    description="Auto-generate environments for molecule role testing",
    long_description_content_type="text/markdown",
    long_description=io.open("README.md", encoding="utf-8").read(),
    author="Greg Hellings",
    author_email="greg.hellings@gmail.com",
    url="https://github.com/ansible-community/tox-ansible",
    license="GPLv3",
    version="0.11.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
    entry_points={"tox": ["ansible-collection = tox_ansible.hooks"]},
    install_requires=["tox>=2.7", "pyyaml"],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Framework :: tox",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Testing",
    ],
)
