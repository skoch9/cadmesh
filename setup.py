import setuptools
from setuptools import setup


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="cadmesh",
    version="2.0.1",
    author="Sebastian Koch, Joseph Lambourne",
    author_email="s.koch@tu-berlin.de",
    description="Topology, geometry and mesh extraction for CAD files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/skoch9/cadmesh",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    test_suite="test"
)
