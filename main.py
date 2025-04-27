import os
import sys
import argparse  # Importar el módulo argparse para manejar argumentos

# Añade el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PMDB_MP.player import VideoPlayer

def main():
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(description='PMDB Media Player')
    parser.add_argument('video_path', help='Ruta del archivo de video')
    parser.add_argument('--fullscreen', action='store_true',
                      help='Iniciar en modo pantalla completa')

    args = parser.parse_args()

    # Verificar si el archivo existe
    if not os.path.exists(args.video_path):
        print(f"Error: El archivo '{args.video_path}' no existe.")
        sys.exit(1)

    print("Iniciando PMDB Media Player...")
    app = VideoPlayer(args.video_path)

    # Si se especificó --fullscreen, activar pantalla completa
    if args.fullscreen:
        app.root.after(100, app._toggle_fullscreen)  # Pequeño delay para asegurar que la ventana esté lista

    app.run()

if __name__ == "__main__":
    main()
