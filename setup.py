from setuptools import setup, find_packages

setup(
    name="sap_automation",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pywin32==306",
        "pytest==7.4.0",
        "behave==1.2.6",
        "html-testRunner==1.2.1",
        "python-dotenv==1.0.0"
    ],
)
