import os
import platform
import glob
import shutil
import PyInstaller.__main__
from PyInstaller.utils.hooks import collect_data_files

def get_data_files():
    """Prepara todos los archivos adicionales para incluir"""
    data_files = []

    # Iconos desde la raíz del proyecto
    icons = glob.glob('assets/icons/*.png') + glob.glob('assets/icons/*.ico')
    data_files.extend([(icon, 'assets/icons') for icon in icons])

    # Archivos Python del módulo PMDB_MP
    py_files = glob.glob('PMDB_MP/*.py')
    data_files.extend([(py_file, 'PMDB_MP') for py_file in py_files])

    return data_files

def build():
    # Configuración común
    opts = [
        'main.py',
        '--name=PMDB_Media_Player',
        '--onefile',
        '--windowed',
        '--icon=assets/icons/player_icon.ico',
        '--hidden-import=customtkinter',
        '--hidden-import=vlc',
        '--hidden-import=PIL',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=PIL.ImageTk',
        '--collect-all=customtkinter',
        '--collect-data=Pillow',
        '--collect-submodules=PIL'
    ]

    # Añadir archivos de datos
    for src, dst in get_data_files():
        opts.append(f'--add-data={src}:{dst}')

    # Configuración específica para VLC en Linux
    if platform.system() == 'Linux':
        vlc_paths = [
            '/usr/lib/x86_64-linux-gnu/libvlc.so',
            '/usr/lib/x86_64-linux-gnu/libvlccore.so',
            '/usr/lib/x86_64-linux-gnu/vlc/plugins',
        ]

        for path in vlc_paths:
            if os.path.exists(path):
                if os.path.isfile(path):
                    opts.append(f'--add-binary={path}:.')
                elif os.path.isdir(path):
                    opts.append(f'--add-binary={path}/*:vlc/plugins')

    # Ejecutar PyInstaller
    PyInstaller.__main__.run(opts)

if __name__ == '__main__':
    # Limpiar builds anteriores
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('dist', ignore_errors=True)

    # Construir
    build()

    print("\nBuild completado! Ejecutable creado en: dist/PMDB_Media_Player")
