from setuptools import setup, find_packages

setup(
    name="PMDB_MP",
    version="1.0.0",
    author="Gonzalo Abbate",
    description="Reproductor multimedia avanzado",
    packages=find_packages(),
    install_requires=[
        'python-vlc',
        'customtkinter',
        'Pillow'
    ],
    entry_points={
        'console_scripts': [
            'pmdb-mp=main:main',
        ],
    },
    package_data={
        'PMDB_MP': ['assets/icons/*.png'],
    },
)
