from setuptools import setup, find_packages

setup(
    name="codetango",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "codetango": ["*.py"],
    },
)
