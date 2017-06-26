from setuptools import setup


try:
    with open('README.rst') as f:
        readme = f.read()
except IOError:
    readme = ''


name = 'chainerboard'
version = '0.1'
release = '0.1.0'

setup(
    name=name,
    author='Yuta Koreeda',
    author_email='secret-email@example.com',
    maintainer='Yuta Koreeda',
    maintainer_email='secret-email@example.com',
    version=release,
    description='Visualization toolkit for Chainer',
    long_description=readme,
    url='https://github.com/koreyou/chainerboard',
    packages=[
        'chainerboard'
    ],
    license='MIT',
    install_requires=[
        'Click',
        'flask',
        'plotly',
        'colorlover',
        'numpy'
    ],
    entry_points = {
        'console_scripts': ['chainerboard=chainerboard.cli:cli'],
    },
    classifiers=[
        "Environment :: Console",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis"
    ]
)
