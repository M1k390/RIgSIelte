from setuptools import setup, find_packages
import re

VERSIONFILE="src/rigproc/version.py"
with open(VERSIONFILE, "rt") as vf:
    verstrline = vf.read()
VSRE= r"^__version__= ['\"]([^'\"]*)['\"]"
mo= re.search(VSRE, verstrline, re.M)
if mo:
    version = mo.group(1)
    print(f'Found version: {version}\n')
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="rigproc",
    version=version,
    author="Ikos Consulting",
    author_email="mdebiaggi@ikosconsulting.com, mgullo@ikosconsulting.com",
    description="Sielte Rig application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="git@bitbucket.org:slt-iks/rig.git",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Linux",
    ],
    entry_points={
        "console_scripts":[
            "runrig= rigproc.central.__main__:run",
            ],
        },
    python_requires='>=3.7.4',
)