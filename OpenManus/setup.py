from setuptools import find_packages, setup


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="data-ai",
    version="0.2.0",
    author="badhope",
    author_email="",
    description="DATA-AI - 智能化数据处理和分析平台，支持多种 AI 工具和代理",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/badhope/Data-Agent",
    packages=find_packages(),
    # Web 模式核心依赖（与 requirements.txt 保持一致）
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "websockets>=11.0.0",
        "python-multipart>=0.0.6",
        "openai>=1.0.0",
        "tenacity>=8.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
        "tomli>=2.0.0; python_version<'3.11'",
        "httpx>=0.25.0",
        "aiofiles>=24.1.0",
        "loguru>=0.7.0",
        "rich>=13.0.0",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "markdown>=3.5.0",
        "pygments>=2.16.0",
        "jinja2>=3.1.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "Pillow>=10.0.0",
        "aiosqlite>=0.19.0",
    ],
    # 可选依赖分组
    extras_require={
        "full": [
            "anthropic>=0.18.0",
            "tiktoken>=0.7.0",
            "aiohttp>=3.9.0",
            "pdfplumber>=0.10.0",
            "python-pptx>=0.6.21",
            "pymupdf>=1.23.0",
            "python-docx>=0.8.11",
            "mcp>=1.0.0",
            "duckduckgo-search>=6.0.0",
            "googlesearch-python>=1.3.0",
        ],
        "browser": [
            "browser-use>=0.1.40",
            "playwright",
        ],
        "cloud": [
            "boto3>=1.37.0",
        ],
        "cli": [
            "datasets>=3.2,<3.5",
            "gymnasium>=1.0,<1.2",
            "browsergym~=0.13.3",
            "unidiff~=0.7.5",
            "html2text~=2024.2.26",
            "colorama~=0.4.6",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "data-ai=main:main",
        ],
    },
)
