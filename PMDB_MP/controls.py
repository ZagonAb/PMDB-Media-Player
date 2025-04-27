import tkinter as tk
import customtkinter as ctk
from PIL import Image
import os
import sys

class PlayerControls(ctk.CTkFrame):
    def __init__(self, master, play_pause_cmd, close_cmd, rewind_cmd, forward_cmd,
                toggle_mute_cmd, toggle_fullscreen_cmd, toggle_subtitle_cmd=None,
                show_subtitle_menu_cmd=None, **kwargs):

        # Añade estos colores al inicio del método
        self.btn_color = "#303338"  # Color de botones normal
        self.hover_color = "#474b50"  # Color al pasar el mouse
        self.text_color = "white"  # Color del texto

        super().__init__(master, **kwargs)

        # Guardamos los comandos como atributos
        self.play_pause_cmd = play_pause_cmd
        self.close_cmd = close_cmd
        self.rewind_cmd = rewind_cmd
        self.forward_cmd = forward_cmd
        self.toggle_mute_cmd = toggle_mute_cmd
        self.toggle_fullscreen_cmd = toggle_fullscreen_cmd
        self.volume_change_cmd = None  # Lo asignaremos después

        self.embedded_subtitles = []

        # Obtener la ruta absoluta al directorio del proyecto
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.volume_icon = self._load_icon("volume")
        self.mute_icon = self._load_icon("mute")
        self.fullscreen_icon = self._load_icon("fullscreen")
        self.no_fullscreen_icon = self._load_icon("no-fullscreen")
        self.play_icon = self._load_icon("play")
        self.pause_icon = self._load_icon("pause")
        self.close_icon = self._load_icon("close")
        self.forward_icon = self._load_icon("forward")
        self.backward_icon = self._load_icon("backward")
        self.subtitle_on_icon = self._load_icon("subtitle-on")
        self.subtitle_off_icon = self._load_icon("subtitle-off")
        self.embedded_sub_icon = self._load_icon("embedded-sub")

        # Configuración del grid (8 columnas ahora para incluir el botón de fullscreen)
        for i in [0,  10]:
            self.grid_columnconfigure(i, weight=1)  # Espacios laterales
        for i in range(1, 10):
            self.grid_columnconfigure(i, weight=0)  # Botones

        # Botón Retroceder 10s
        self.rewind_button = ctk.CTkButton(
            self,
            text="" if self.backward_icon else "⏪ -10s",
            image=self.backward_icon,
            width=30,
            height=30,
            command=rewind_cmd,
            compound="top",
            fg_color=self.btn_color,
            hover_color=self.hover_color,
            text_color=self.text_color
        )
        self.rewind_button.grid(row=0, column=1, padx=5, pady=2)

        # Aplica el mismo estilo a todos los botones:
        button_config = {
            'width': 30,
            'height': 30,
            'compound': "top",
            'fg_color': self.btn_color,
            'hover_color': self.hover_color,
            'text_color': self.text_color,
            'corner_radius': 5
        }

        # Botón Play/Pause
        self.play_pause_button = ctk.CTkButton(
            self,
            text="",
            image=self.pause_icon,
            command=play_pause_cmd,
            **button_config
        )
        self.play_pause_button.grid(row=0, column=2, padx=5, pady=2)

        # Botón Cerrar
        self.close_button = ctk.CTkButton(
            self,
            text="" if self.close_icon else "Cerrar",
            image=self.close_icon,
            command=close_cmd,
            **button_config
        )
        self.close_button.grid(row=0, column=3, padx=5, pady=2)

        # Botón Avanzar 10s
        self.forward_button = ctk.CTkButton(
            self,
            text="" if self.forward_icon else "+10s ⏩",
            image=self.forward_icon,
            command=forward_cmd,
            **button_config
        )
        self.forward_button.grid(row=0, column=4, padx=5, pady=2)

        # Botón Mute
        self.mute_button = ctk.CTkButton(
            self,
            text="" if (self.volume_icon and self.mute_icon) else "🔊",
            image=self.volume_icon,
            command=self._handle_mute_click,
            **button_config
        )
        self.mute_button.grid(row=0, column=5, padx=(5, 0), pady=2)

        # Barra de Volumen
        self.volume_slider = ctk.CTkSlider(
            self,
            from_=0,
            to=100,
            width=100,
            height=16
        )
        self.volume_slider.set(50)
        self.volume_slider.grid(row=0, column=6, padx=(10, 5), pady=5, sticky="ew")

        # Botón Fullscreen (nueva adición)
        self.fullscreen_button = ctk.CTkButton(
            self,
            text="",
            image=self.fullscreen_icon,
            command=self._handle_fullscreen_click,
            **button_config
        )
        self.fullscreen_button.grid(row=0, column=7, padx=5, pady=2)

        # Botón Subtítulos (nuevo)
        self.subtitle_button = ctk.CTkButton(
            self,
            text="",
            image=self.subtitle_off_icon,  # Icono "off" inicial
            command=toggle_subtitle_cmd if toggle_subtitle_cmd else None,
            state="normal" if toggle_subtitle_cmd else "disabled",
            **button_config
        )
        self.subtitle_button.grid(row=0, column=8, padx=5, pady=2)

        # Botón Subtítulos Embebidos (nuevo, columna 9)
        self.embedded_sub_button = ctk.CTkButton(
            self,
            text="",
            image=self.embedded_sub_icon,
            command=show_subtitle_menu_cmd if show_subtitle_menu_cmd else None,
            state="disabled",
            **button_config
        )
        self.embedded_sub_button.grid(row=0, column=9, padx=5, pady=2)

        # Variables para subtítulos embebidos
        self.embedded_subtitles_available = False
        self.subtitle_menu = None

        # Variables de estado
        self.subtitle_available = False
        self.subtitle_enabled = False

        # Eventos de la barra de volumen
        self.volume_slider.bind("<Button-1>", self._handle_volume_change)
        self.volume_slider.bind("<B1-Motion>", self._handle_volume_change)

        self.is_muted = False
        self.is_fullscreen = False

    def set_embedded_subtitles_state(self, available):
        """Habilita/deshabilita el botón de subtítulos embebidos"""
        self.embedded_subtitles_available = available
        state = "normal" if available else "disabled"
        self.embedded_sub_button.configure(state=state)
        print(f"[SUBTITLE_BUTTON] Estado actualizado: {state} (Disponible: {available})")


    def set_subtitle_state(self, available, enabled=False):
        """Configura el estado del botón de subtítulos"""
        self.subtitle_available = available
        self.subtitle_enabled = enabled

        if available:
            self.subtitle_button.configure(state="normal")
            # Icono "on" cuando están activos, "off" cuando no
            icon = self.subtitle_on_icon if enabled else self.subtitle_off_icon
            self.subtitle_button.configure(image=icon)
        else:
            self.subtitle_button.configure(state="disabled")

    def set_volume_change_callback(self, callback):
        """Asigna el callback para cambios de volumen"""
        self.volume_change_cmd = callback

    def _handle_volume_change(self, event=None):
        """Maneja cambios en la barra de volumen"""
        if self.volume_change_cmd:
            self.volume_change_cmd(self.volume_slider.get())

    def _handle_mute_click(self):
        """Versión alternativa que maneja estado local"""
        if self.toggle_mute_cmd:
            self.toggle_mute_cmd()  # Notifica al reproductor
            self.is_muted = not self.is_muted
            self._update_mute_icon()
            # Asegurar sincronización con barra de volumen
            self.volume_slider.set(0 if self.is_muted else getattr(self, 'last_volume', 70))

    def _handle_fullscreen_click(self):
        """Maneja el clic en el botón de pantalla completa"""
        if self.toggle_fullscreen_cmd:
            self.toggle_fullscreen_cmd()  # Notifica al reproductor
            # No cambiamos el estado aquí, lo hará el reproductor al llamar update_fullscreen_button

    def _update_fullscreen_icon(self):
        """Actualiza el icono basado en el estado de pantalla completa"""
        if hasattr(self, 'fullscreen_icon') and hasattr(self, 'no_fullscreen_icon'):
            new_icon = self.no_fullscreen_icon if self.is_fullscreen else self.fullscreen_icon
            self.fullscreen_button.configure(image=new_icon)
        else:
            # Fallback con emojis si hay problemas con los iconos
            self.fullscreen_button.configure(text="🔍" if self.is_fullscreen else "⛶")

    def update_volume_controls(self, volume, is_muted):
        """Actualiza tanto la barra como el botón de mute"""
        self.volume_slider.set(volume)
        self.update_mute_button(is_muted)

        print(f"Ruta base del proyecto: {self.base_path}")
        print(f"Intentando cargar volumen desde: {os.path.join(self.base_path, 'assets', 'icons', 'volume.png')}")
        print(f"El archivo existe: {os.path.exists(os.path.join(self.base_path, 'assets', 'icons', 'volume.png'))}")

    def _update_mute_icon(self):
        """Actualiza el icono basado en el estado mute"""
        if hasattr(self, 'mute_icon') and hasattr(self, 'volume_icon'):
            new_icon = self.mute_icon if self.is_muted else self.volume_icon
            self.mute_button.configure(image=new_icon)
        else:
            # Fallback con emojis si hay problemas con los iconos
            self.mute_button.configure(text="🔇" if self.is_muted else "🔊")

    def _load_icon(self, icon_name):
        base_paths = [
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # PMDB_MP/
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            os.path.dirname(sys.executable),
            getattr(sys, '_MEIPASS', '')
        ]

        file_names = [
            f"{icon_name}.png",
            f"{icon_name}.ico",
        ]

        for base in base_paths:
            if not base:
                continue

            for file in file_names:
                icon_path = os.path.join(base, "assets", "icons", file)
                try:
                    if os.path.exists(icon_path):
                        print(f"Cargando icono desde: {icon_path}")
                        return ctk.CTkImage(Image.open(icon_path), size=(24, 24))
                except Exception as e:
                    print(f"Error cargando {icon_path}: {str(e)}")

        print(f"Icono no encontrado: {icon_name}. Usando texto alternativo.")
        return None

    def update_mute_button(self, is_muted):
        if hasattr(self, 'volume_icon') and self.volume_icon:
            self.mute_button.configure(image=self.mute_icon if is_muted else self.volume_icon)
        else:
            self.mute_button.configure(text="🔇" if is_muted else "🔊")

    def update_play_pause_button(self, is_playing):
        """Actualiza el texto del botón según el estado"""
        self.play_pause_button.configure(text="Pausar" if is_playing else "Reproducir")

    def update_fullscreen_button(self, is_fullscreen):
        """Actualiza el icono del botón de pantalla completa"""
        self.is_fullscreen = is_fullscreen
        if hasattr(self, 'fullscreen_icon') and hasattr(self, 'no_fullscreen_icon'):
            new_icon = self.no_fullscreen_icon if is_fullscreen else self.fullscreen_icon
            self.fullscreen_button.configure(image=new_icon)
        else:
            # Fallback con emojis si hay problemas con los iconos
            self.fullscreen_button.configure(text="🔍" if is_fullscreen else "⛶")

    def update_play_pause_button(self, is_playing):
        """Actualiza el botón play/pause según el estado"""
        self.is_playing = is_playing

        # Determinar qué icono usar basado en el estado y disponibilidad
        if is_playing:
            icon = self.pause_icon
            text = "" if self.pause_icon else "Pausar"
        else:
            icon = self.play_icon
            text = "" if self.play_icon else "Reproducir"

        self.play_pause_button.configure(image=icon, text=text)
