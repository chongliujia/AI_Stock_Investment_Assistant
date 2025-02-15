from setuptools import setup, find_packages

setup(
    name="open-multi-agent-framework",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.0",
        "yfinance>=0.2.3",
        "pandas>=1.3.0",
        "python-dotenv>=0.19.0",
        "requests>=2.26.0",
        "openai>=1.0.0"
    ],
) 