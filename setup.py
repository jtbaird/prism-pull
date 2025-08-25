from setuptools import setup, find_packages

setup(
    name="prism-pull",
    version="0.1.0",
    description="Python package to pull PRISM weather data via web automation.",
    author="John Baird",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "selenium"
    ],
    python_requires=">=3.13",
)