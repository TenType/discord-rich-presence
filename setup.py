from setuptools import setup
import discordrp

with open('./README.md') as file:
    long_description = file.read()

setup(
    name=discordrp.__title__,
    version=discordrp.__version__,
    description='A lightweight and safe module for creating custom rich presences on Discord.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/TenType/discord-rich-presence',
    author=discordrp.__author__,
    license=discordrp.__license__,
    keywords=['discord', 'presence', 'rich presence', 'activity', 'rpc'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Typing :: Typed',
    ],
    python_requires='>=3.9',
)
