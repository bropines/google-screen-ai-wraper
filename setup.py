from setuptools import setup, find_packages

setup(
    name="google_screen_ai",
    version="1.0.0",
    description="Python wrapper and CLI for Google's ScreenAI OCR and Main Content Extraction",
    author="Antigravity",
    packages=find_packages(),
    install_requires=[
        "protobuf>=4.0.0",
        "pillow>=9.0.0",
    ],
    entry_points={
        "console_scripts": [
            "screen-ai=google_screen_ai.__main__:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
    python_requires=">=3.8",
)
