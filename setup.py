from setuptools import setup, find_packages

setup(
    name='netbox-ttyd-terminal',
    version='0.1.0',
    description='A NetBox plugin that integrates TTYD as a web SSH terminal for devices',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)

