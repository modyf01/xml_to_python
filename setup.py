from setuptools import setup, find_packages

setup(
    name="xml_to_python_generator",
    version="1.0.1",
    description="A Python tool for generating Python classes and scripts from XML files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Krzysztof Ostrowski",
    author_email="krzysztofostrowski2001@gmail.com",
    url="https://github.com/modyf01/XML-to-Python-Generator",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "graphviz",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)