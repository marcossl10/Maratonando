from setuptools import setup, find_packages

setup(
    name="maratonando",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "requests",
        "beautifulsoup4",
        "Pillow",
        "packaging",
    ],
    entry_points={
        "console_scripts": [
            "maratonando=maratonando_src.main:start",
        ],
    },
)