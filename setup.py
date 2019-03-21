import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(name='meerkat',
                 version='0.2',
                 description='A data aquiisition library for Raspberry Pi and MicroPython',
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 url='https://github.com/crdietrich/meerkat',
                 author='Colin Dietrich',
                 author_email='repos@wildjuniper.com',
                 license='MIT',
                 packages=setuptools.find_packages(),
                 zip_safe=False,
                 classifiers=[
                     "Programming Language :: Python :: 3",
                     "Development Status :: 3 - Alpha",
                     "License :: OSI Approved :: MIT License",
                     "Operating System :: OS Independent",
                 ]
                 )
