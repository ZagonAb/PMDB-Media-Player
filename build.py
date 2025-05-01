import os
import platform
import glob
import shutil
import PyInstaller.__main__
from PyInstaller.utils.hooks import collect_data_files

def get_data_files():
    data_files = []

    icons = glob.glob('assets/icons/*.png') + glob.glob('assets/icons/*.ico')
    data_files.extend([(icon, 'assets/icons') for icon in icons])
    py_files = glob.glob('PMDB_MP/*.py')
    data_files.extend([(py_file, 'PMDB_MP') for py_file in py_files])

    return data_files

def build():
    if platform.system() != 'Linux':
        print("Este script de construcción es solo para Linux")
        print("Para Windows, por favor usa la versión portable con Python")
        return

    opts = [
        'main.py',
        '--name=PMDB_Media_Player',
        '--windowed',
        '--icon=assets/icons/pmdbmp.ico',
        '--onefile',
        '--noconfirm',
        '--clean'
    ]

    hidden_imports = [
        '--hidden-import=customtkinter',
        '--hidden-import=vlc',
        '--hidden-import=PIL',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=PIL.ImageTk'
    ]
    opts.extend(hidden_imports)

    collect_options = [
        '--collect-all=customtkinter',
        '--collect-data=Pillow',
        '--collect-submodules=PIL'
    ]
    opts.extend(collect_options)
    separator = ':'
    for src, dst in get_data_files():
        opts.append(f'--add-data={src}{separator}{dst}')

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

    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('dist', ignore_errors=True)
    print("\nIniciando construcción para Linux con opciones:")
    print(" ".join(opts))
    PyInstaller.__main__.run(opts)

    print("\n¡Build para Linux completado exitosamente!")
    print(f"Ejecutable creado en: dist/PMDB_Media_Player")

if __name__ == '__main__':
    build()
