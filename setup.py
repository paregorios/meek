import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="meek",
    version="0.0.1",
    author="Tom Elliott",
    author_email="tom.elliott@nyu.edu",
    description="manage activities",
    license='MIT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    # {project-url}
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.9.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'airtight',
        'maya@git+https://github.com/timofurrer/maya#b12a8dad11aec99ef62b063b5631dce0f528bcb4',
        'textnorm',
        'tzlocal'
    ],
    python_requires='==3.9.7'
)
