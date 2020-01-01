#!/usr/bin/env python

from setuptools import setup, find_packages
import os

with open('README.md') as f:
    long_description = f.read()

requires = [
    'awscli>=1.10.21',
    'jmespath>=0.9.0',
    'boto3>=1.3.0',
    'click>=6.6',
    'oyaml>=0.9'
]

setup(
    name='cronyo',
    version=open(os.path.join('cronyo', 'VERSION')).read().strip(),
    description='Manage your cron jobs with AWS Cloudwatch and Lambda',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Yoav Aner',
    author_email='yoav@gingerlime.com',
    url='https://github.com/Alephbet/cronyo',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    entry_points="""
        [console_scripts]
        cronyo=cronyo.cli:cli
    """,
    install_requires=requires,
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ),
)
