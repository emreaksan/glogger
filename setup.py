"""Setup module for project."""

import setuptools


setuptools.setup(
    name='glogger',
    version='0.1.0',
    description='A logging utility for dumping structured data into Google Sheet',
    author='Emre Aksan (@emreaksan), Manuel Kaufmann (@kaufManu), Seonwook Park (@swook)',
    url='https://github.com/pypa/sampleproject',
    
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires='>=3.5',
    install_requires=[
        'gspread==3.6.0',
        'google-auth==1.16.1',
        'numpy==1.18.5',
        ],
    )
