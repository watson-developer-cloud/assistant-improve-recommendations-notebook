# -*- coding: utf8 -*-
#
# This file were created by Python Boilerplate. Use Python Boilerplate to start
# simple, usable and best-practices compliant Python projects.
#
# Learn more about it at: http://github.com/fabiommendes/python-boilerplate/
#

import setuptools

__version__ = '1.1.5'

# Convert README.md to README.rst for pypi
try:
    from pypandoc import convert_file

    def read_md(f):
        return convert_file(f, 'rst')

except:
    print('warning: pypandoc module not found, '
          'could not convert Markdown to RST')

    def read_md(f):
        return open(f, 'rb').read().decode(encoding='utf-8')

setuptools.setup(
    # Basic info
    name='assistant_improve_toolkit',
    version=__version__,
    author='IBM Watson',
    author_email='watdevex@us.ibm.com',
    maintainer='Zhe Zhang',
    maintainer_email='zhangzhe@us.ibm.com',
    url='https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook',
    description='Assistant Improve Toolkit',
    license='Apache 2.0',
    long_description=read_md('README.md'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    # Packages and depencies
    package_dir={'': 'src'},
    packages=setuptools.find_packages('src'),
    install_requires=[
        'pandas==1.0.3',
        'bokeh==2.0.0',
        'tqdm==4.43.0',
        'scikit-learn>=0.21.3',
        'matplotlib==3.2.1',
        'XlsxWriter==1.2.8',
        'ibm-watson>=4.3.0',
        'numpy>=1.18.2',
        'requests>=2.18.4',
        'xlrd==1.2.0'
    ],

    zip_safe=False,
    platforms='any',
)
