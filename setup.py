from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="tmd-top",
    version="2.1.5",
    author="Davin",
    author_email="949178863@qq.com",
    description="linux服务器网络流量分析工具，详细到ip连接情况",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitee.com/Davin168/tmd-top",  # 项目GitHub地址或主页
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "tmd_top": ["data/*.mmdb", "data/*.db"],
    },
    python_requires=">=3.8",  # 指定支持的Python版本
    install_requires=[
        "textual==0.76.0",
        "typing_extensions==4.9.0",
        "rich==13.7.1",
        "geoip2==4.8.0",
    ],
    classifiers=[
        # Add classifiers to specify the project's target audience, license, etc.
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'tmd-top=tmd_top.main:main',
        ],
    },
)