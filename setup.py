from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
version = {}
with open(os.path.join(here, "src", "version.py")) as f:
    exec(f.read(), version)

setup(
    name="app-service",
    version=version["__version__"],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "lib_version @ git+https://github.com/remla2025-team9/lib-version.git@a1#egg=lib_version",
        "flask",
        "flask-cors",
        "requests",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "app-service = src.main:app",
        ],
    },
)
