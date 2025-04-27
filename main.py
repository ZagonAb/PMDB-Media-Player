# main.py
import os
import sys
import argparse
from PMDB_MP.player import VideoPlayer
from PMDB_MP.locales import get_locale

def main():
    parser = argparse.ArgumentParser(description='PMDB Media Player')
    parser.add_argument('video_path', help='Ruta del archivo de video')
    parser.add_argument('--fullscreen', action='store_true',
                      help='Iniciar en modo pantalla completa')
    parser.add_argument('--language', choices=['es', 'en'], default='es',
                      help='Idioma de la interfaz (es: español, en: inglés)')

    args = parser.parse_args()

    if not os.path.exists(args.video_path):
        print(f"Error: El archivo '{args.video_path}' no existe.")
        sys.exit(1)

    print("Iniciando PMDB Media Player...")
    app = VideoPlayer(args.video_path, language=args.language)

    if args.fullscreen:
        app.root.after(100, app._toggle_fullscreen)

    app.run()

if __name__ == "__main__":
    main()
