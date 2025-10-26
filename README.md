# PMDB Media Player

Un reproductor multimedia avanzado desarrollado con Python, VLC y CustomTkinter, diseñado exclusivamente para la interfaz [PMDB-Theme](https://github.com/ZagonAb/PMDB-Theme)

![Modo ventana](https://github.com/ZagonAb/PMDB-Media-Player/blob/1ce3b7a661f3fd3d872408b2826129e12b2e08ba/.meta/screenshots/screen.png)
![Pantalla completa](https://github.com/ZagonAb/PMDB-Media-Player/blob/1ce3b7a661f3fd3d872408b2826129e12b2e08ba/.meta/screenshots/screen1.png)

## Características principales

- ✔️ Reproducción de videos con soporte para múltiples formatos
- ✔️ Interfaz moderna y personalizable con CustomTkinter
- ✔️ Soporte para subtítulos (externos y embebidos)
- ✔️ Control de volumen y mute
- ✔️ Funcionalidad de pantalla completa
- ✔️ Guardado automático de posición de reproducción
- ✔️ Atajos de teclado para controles rápidos
- ✔️ **Soporte para gamepads/joysticks (Windows y Linux)**
- ✔️ Interfaz en español e inglés
- ✔️ Integración con la interfaz [PMDB-Theme](https://github.com/ZagonAb/PMDB-Theme)

## Requisitos del sistema

### Dependencias comunes
- Python 3.8 o superior
- VLC media player instalado en el sistema

#### Linux (Debian/Ubuntu)
```bash
sudo apt-get install -y python3-dev python3-pip libvlc-dev vlc libx11-dev libgtk-3-dev
```

#### Windows
- Instalar [VLC media player (64-bit)](https://www.videolan.org/)
- Instalar [Python 3.8+](https://www.python.org/)
- Instalar [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) (requerido por Pygame)

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/ZagonAb/PMDB-Media-Player
cd PMDB-Media-Player
```

2. Crea y activa un entorno virtual de Python (recomendado en **Linux**):

#### Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Instala las dependencias dentro del entorno virtual:
```bash
pip install -r requirements.txt
```
- **En Windows, puede omitir la creación de un entorno virtual e instalar directamente las dependencias necesarias.**
- **"Asegúrese de que la ruta de instalación de VLC esté incluida en la variable de entorno `PATH` de Windows."**

### 🧪 Agregar VLC al `PATH` usando `cmd` (como administrador)

1. **Abre `cmd` como administrador**  

2. **Ejecuta el siguiente comando**  
   Sustituye la ruta si VLC está en otro lugar:

```cmd
setx /M PATH "%PATH%;C:\Program Files\VideoLAN\VLC"
```

> ⚠️ Nota:
> - `/M` modifica el `PATH` **del sistema** (no solo el del usuario).
> - Asegúrate de que la ruta `C:\Program Files\VideoLAN\VLC` es la correcta.

3. **Reinicia el terminal o tu sesión**
   Los cambios no afectan terminales abiertos previamente. Cierra y abre uno nuevo para que el cambio surta efecto.

4. **Verifica que funciona**  
   Escribe en la terminal:
```cmd
vlc --version
```
- Deberías ver la versión de VLC.
---
- Instala las dependencias en windows.

```bash
pip install -r requirements.txt
```

4. Ejecuta el reproductor:
```bash
python main.py /ruta/al/video.mp4
```

Opciones disponibles:
- `--fullscreen`: Inicia en modo pantalla completa
- `--language [es|en]`: Selecciona el idioma de la interfaz

Ejemplo:
```bash
python main.py --language "en" --fullscreen /ruta/al/video.mp4
```

## Construir ejecutable

Para crear un ejecutable independiente (recomendado para su uso con [PMDB-Theme](https://github.com/ZagonAb/PMDB-Theme) en **Linux**):

1. Ejecuta el script de construcción:
```bash
python build.py
```

El ejecutable se generará en `dist/PMDB_Media_Player`

### Nota
- **Windows**: **No es requerido empaquetar; puede utilizar la siguiente línea en `metadata.txt`:"** `python path/to/PMDB-Media-Player/main.py --fullscreen {file.path}`

### Requisitos para gamepads
- En Linux, la mayoría de los gamepads funcionarán inmediatamente
- En Windows, se recomienda usar gamepads compatibles con XInput (como controles de Xbox)
- Para gamepads genéricos en Windows, puedes necesitar [x360ce](https://www.x360ce.com/) para emular un control de Xbox


## Atajos de teclado y controles

| Control               | Función                          |
|-----------------------|----------------------------------|
| **Teclado**           |                                  |
| Espacio               | Play/Pause                       |
| Flecha izquierda      | Retroceder 10 segundos           |
| Flecha derecha        | Avanzar 10 segundos              |
| Flecha arriba         | Aumentar volumen                 |
| Flecha abajo          | Disminuir volumen                |
| F11                   | Alternar pantalla completa       |
| Doble clic            | Alternar pantalla completa       |
| Escape                | Salir de pantalla completa/cerrar|
| **Gamepad**           |                                  |
| Botón A (1)           | Play/Pausa                       |
| Botón B (2)           | Alternar subtítulos              |
| Botón X (3)           | Pantalla completa                |
| Botón Y (4)           | Cerrar reproductor               |
| D-Pad Arriba          | Aumentar volumen                 |
| D-Pad Abajo           | Disminuir volumen                |
| D-Pad Izquierda       | Retroceder 10 segundos           |
| D-Pad Derecha         | Avanzar 10 segundos              |

## Configuración avanzada

El reproductor guarda automáticamente la última posición de reproducción en:

| Sistema | Ubicación |
|---------|-----------|
| Linux | `~/.config/pegasus-frontend/themes/PMDB-Theme/database.json` |
| Linux (Flatpak) | `~/.var/app/org.pegasus_frontend.Pegasus/config/pegasus-frontend/themes/PMDB-Theme/database.json` |
| Windows | `%LOCALAPPDATA%\pegasus-frontend\themes\PMDB-Theme\database.json` |

## Personalización

### Iconos
Coloca archivos PNG en `PMDB_MP/assets/icons/` con estos nombres:

| Función | Archivos |
|---------|----------|
| Reproducción | `play.png`, `pause.png` |
| Volumen | `volume.png`, `mute.png` |
| Pantalla completa | `fullscreen.png`, `no-fullscreen.png` |
| Navegación | `forward.png`, `backward.png` |
| Subtítulos | `subtitle-on.png`, `subtitle-off.png`, `embedded-sub.png` |

## Soporte

Si encuentras algún problema, por favor abre un issue en el [repositorio](https://github.com/ZagonAb/PMDB-Media-Player/issues).

## Licencia

Este proyecto está licenciado bajo los términos de la [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) o posterior, en cumplimiento con los requisitos de licencia de python-vlc/VLC.

---
**Nota**: PMDB Media Player es un proyecto personal sin afiliación oficial con Pegasus Frontend.

----

### 💖 DONATE
I'm a programming enthusiast and passionate about free software, with a special love for classic games and the retro community. All my themes and projects are open-source and available for anyone to use. If you'd like to show your support or help me continue creating and improving these projects, you can make a voluntary donation. Every contribution, no matter how small, allows me to continue improving and maintaining these projects. 👾

[![Support on PayPal](https://img.shields.io/badge/PayPal-0070ba?style=for-the-badge)](https://paypal.me/ZagonAb)
[![Donate using Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/Gonzalo/donate)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-29abe0?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/zagonab)
