# PMDB Media Player
- Pegasus Movie Data Base Media Player
- Un reproductor multimedia avanzado desarrollado con Python, VLC y CustomTkinter, diseñado exclusivamente para la interfaz [PMDB-Theme](https://github.com/ZagonAb/PMDB-Theme)
- Pegasus Movie Data Base Media Player (PMDB-MP) es un proyecto personal, sin afiliación ni relación oficial con Pegasus Frontend. Se trata de un desarrollo independiente que comparto de manera abierta con la comunidad.

- Modo ventana.
![screenshot](https://github.com/ZagonAb/PMDB-Media-Player/blob/1ce3b7a661f3fd3d872408b2826129e12b2e08ba/.meta/screenshots/screen.png)
- Pantalla completa.
![screenshot1](https://github.com/ZagonAb/PMDB-Media-Player/blob/1ce3b7a661f3fd3d872408b2826129e12b2e08ba/.meta/screenshots/screen1.png)

## Características principales

- ✔️ Reproducción de videos con soporte para múltiples formatos
- ✔️ Interfaz moderna y personalizable con CustomTkinter
- ✔️ Soporte para subtítulos (externos y embebidos)
- ✔️ Control de volumen y mute
- ✔️ Funcionalidad de pantalla completa
- ✔️ Guardado automático de posición de reproducción
- ✔️ Atajos de teclado para controles rápidos
- ✔️ Interfaz en español e inglés
- ✔️ Integración con la interfaz [PMDB-Theme](https://github.com/ZagonAb/PMDB-Theme)

## Requisitos del sistema

- Python 3.8 o superior
- VLC media player instalado en el sistema
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clona el repositorio:
```bash
git https://github.com/ZagonAb/PMDB-Media-Player
cd PMDB-Media-Player
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso básico

Para reproducir un video:

```bash
python3 main.py /ruta/al/video.mp4
```

Opciones disponibles:
- `--fullscreen`: Inicia en modo pantalla completa
- `--language [es|en]`: Selecciona el idioma de la interfaz

Ejemplo:
```bash
python3 main.py --language "en" --fullscreen /ruta/al/video.mp4
```

## Atajos de teclado

| Tecla               | Función                          |
|---------------------|----------------------------------|
| Espacio             | Play/Pause                       |
| Flecha izquierda    | Retroceder 10 segundos           |
| Flecha derecha      | Avanzar 10 segundos              |
| Flecha arriba       | Aumentar volumen                 |
| Flecha abajo        | Disminuir volumen                |
| F11                 | Alternar pantalla completa       |
| Doble clic          | Alternar pantalla completa       |
| Escape              | Salir de pantalla completa/cerrar|

## Configuración avanzada

El reproductor guarda automáticamente la última posición de reproducción en:
- Linux: `~/.config/pegasus-frontend/themes/PMDB-Theme/database.json`
- Linux ` (Flatpak): ~/.var/app/org.pegasus_frontend.Pegasus/config/pegasus-frontend/themes/PMDB-Theme/database.json`
- Windows: `%LOCALAPPDATA%\pegasus-frontend\themes\PMDB-Theme\database.json`
- macOS: `~/Library/Preferences/pegasus-frontend/themes/PMDB-Theme/database.json`

## Personalización

Puedes personalizar los iconos del reproductor colocando archivos PNG en:
`PMDB_MP/assets/icons/`

Los iconos soportados son:
- `play.png`, `pause.png`
- `volume.png`, `mute.png`
- `fullscreen.png`, `no-fullscreen.png`
- `forward.png`, `backward.png`
- `subtitle-on.png`, `subtitle-off.png`
- `embedded-sub.png`

## Construir ejecutable

- Se recomienda crear un ejecutable independiente para su integración con [PMDB-Theme](https://github.com/ZagonAb/PMDB-Theme)

```bash
python build.py
```

El ejecutable se generará en `dist/PMDB_Media_Player`

## Soporte

Si encuentras algún problema, por favor abre un issue en el repositorio.

## Licencia

Este proyecto está licenciado bajo los términos de la [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.html) o posterior, en cumplimiento con los requisitos de licencia de python-vlc/VLC.
