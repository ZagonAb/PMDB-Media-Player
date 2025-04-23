import os
import sys

# Añade el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PMDB_MP.player import VideoPlayer

def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py ruta_del_video")
        sys.exit(1)

    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"Error: El archivo '{video_path}' no existe.")
        sys.exit(1)

    print("Iniciando PMDB Media Player...")
    app = VideoPlayer(video_path)
    app.run()

if __name__ == "__main__":
    main()
