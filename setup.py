# Copyright (C) 2022 Keyu Tian. All rights reserved.
import setuptools
from toolky import __version__


with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='toolky',
    version=__version__,
    author='Keyu Tian',
    author_email='tiankeyu.00@gmail.com',
    description='tools',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/keyu-codebase/toolky',
    packages=setuptools.find_packages(),
    package_data={
        # 引入任何包下面的 *.txt、*.rst 文件
        # "": ["*.txt", "*.rst"],
        # 引入 hello 包下面的 *.msg 文件
        # "hello": ["*.msg"],
    },
    platforms=['all'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    python_requires='>=3.6',
    install_requires=[
        'chardet',
        # 'pathos',
    ],
    entry_points={
        'console_scripts': [
            'sea = toolky.cli.search:main'
        ]
    }
)


