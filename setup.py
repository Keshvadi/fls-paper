# setup.py

from setuptools import setup, find_packages

# Read the contents of the requirements.txt file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read the contents of the README.md file for the long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='fls_analyzer',
    author_email='webidsina@gmail.com', 
    description='A toolkit for the collection and analysis of Free Live Streaming (FLS) websites.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Keshvadi/fls',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=requirements,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Security',
        'Topic :: Internet :: WWW/HTTP',
    ],
    python_requires='>=3.8',
)
