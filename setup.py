from setuptools import setup

setup(
    name="computer_use_demo",
    version="0.1.0",
    packages=["computer_use_demo"],
    install_requires=[
        "anthropic",
        "streamlit",
        "httpx",
    ],
    entry_points={
        "console_scripts": [
            "computer-control-gui=computer_use_demo.streamlit:main",
            "computer-control=computer_use_demo.terminal:main",
        ],
    },
)