# -*- coding: utf8 -*-
#
# This file were created by Python Boilerplate. Use Python Boilerplate to start
# simple, usable and best-practices compliant Python projects.
#
# Learn more about it at: http://github.com/fabiommendes/python-boilerplate/
#

import setuptools
from os import path

__version__ = '1.3.6'

# read contents of README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as file:
    readme_file = file.read()

setuptools.setup(
    # Basic info
    name='assistant_improve_toolkit',
    author='IBM Watson',
    author_email='watdevex@us.ibm.com',
    maintainer='Zhe Zhang',
    maintainer_email='zhangzhe@us.ibm.com',
    url='https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook',
    description='Assistant Improve Toolkit',
    license='Apache 2.0',
    long_description=readme_file,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    # Packages and depencies
    package_dir={'': 'src'},
    packages=setuptools.find_packages('src'),
    install_requires=[
        'pandas==1.2.1',
        'bokeh==2.0.0',
        'tqdm==4.43.0',
        'scikit-learn>=0.21.3',
        'matplotlib==3.2.1',
        'XlsxWriter==1.2.8',
        'ibm-watson==5.1.0',
        'numpy==1.20.3',
        'requests==2.25.1'
    ],

    zip_safe=False,
    platforms='any',
)
