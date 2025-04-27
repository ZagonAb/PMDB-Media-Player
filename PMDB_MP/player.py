import os
import sys
import vlc
import time
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import customtkinter as ctk
from threading import Thread
from PMDB_MP.controls import PlayerControls
from PMDB_MP.progress import ProgressBar
from PMDB_MP.pegasus_utils import PegasusUtils
from PMDB_MP.subtitle_menu import SubtitleMenu


class VideoPlayer:
    def __init__(self, video_path):
        # Configuración de CustomTkinter con tema personalizado
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        video_name = os.path.basename(video_path)
        # Configurar colores personalizados para la aplicación
        self.bg_color = "#202227"  # Color de fondo unificado
        self.bg_color2 = "black"
        self.btn_color = "#303338"  # Color de botones
        self.progress_color = "#50555f"  # Color de progreso
        self.empty_bar_color = "#383838"  # Color de barra vacía

        # Crear ventana principal
        self.root = ctk.CTk()
        self.root.title(f"PMDB Media Player - {video_name}")
        self.root.geometry("800x600")
        self.root.minsize(600,400)

        # ===== NUEVO CÓDIGO PARA EL ICONO =====
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "assets", "icons", "pmdbmp.png")

            if os.path.exists(icon_path):
                if sys.platform == "win32":
                    self.root.iconbitmap(icon_path)
                else:
                    icon = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"No se pudo cargar el icono: {str(e)}")
        # ===== FIN DEL NUEVO CÓDIGO =====

        self.root.update() # Forzar actualización

        self.controls_visible = True

        # Crear marco para el video
        self.video_frame = tk.Frame(self.root, bg=self.bg_color2)
        self.video_frame.pack(fill=tk.BOTH, expand=True)

        # Crear marco para los controles
        self.control_frame = ctk.CTkFrame(self.root)
        self.control_frame.pack(fill=tk.X, padx=0, pady=0)

        # Marco para la barra de progreso
        self.progress_frame = ctk.CTkFrame(self.control_frame)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        # Componente de barra de progreso personalizada
        self.progress = ProgressBar(self.progress_frame)
        self.progress.pack(fill=tk.X)
        self.progress.set_seek_callback(self._seek_video)  # Configurar callback para clics

        # Marco para los botones
        self.button_frame = ctk.CTkFrame(self.control_frame)
        self.button_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Añadir estado de pantalla completa
        self.is_fullscreen = False
        self.original_geometry = self.root.geometry()

        self._setup_vlc(video_path)

        self.subtitle_path = self._find_subtitle_file(video_path)
        self.subtitle_enabled = False

        print(f"[INIT] ¿Subtítulo encontrado?: {self.subtitle_path is not None}")
        print(f"[INIT] Estado inicial de subtítulo: {self.subtitle_enabled}")

        # Asegura que subtítulos estén desactivados correctamente
        if self.subtitle_path:
            print(f"[INIT] Intentando cargar pero desactivar subtítulo: {self.subtitle_path}")
            # Antes de cualquier acción con subtítulos
            print(f"[INIT] Estado de subtítulos antes de configurar: {self.player.video_get_spu()}")
            self.player.video_set_subtitle_file(self.subtitle_path)  # Carga el archivo pero no lo muestra
            self.player.video_set_spu(-1)  # Desactiva explícitamente los subtítulos
            print(f"[INIT] Estado de subtítulos después de configurar: {self.player.video_get_spu()}")

        self.player.video_set_spu(-1)
        # Variables para subtítulos embebidos
        self.embedded_subtitles = []
        self.current_embedded_sub = -1

        self.controls = PlayerControls(
            self.button_frame,
            play_pause_cmd=self.toggle_play_pause,
            close_cmd=self.close_player,
            rewind_cmd=self._rewind_10s,
            forward_cmd=self._forward_10s,
            toggle_mute_cmd=self._toggle_mute,
            toggle_fullscreen_cmd=self._toggle_fullscreen,
            toggle_subtitle_cmd=self._toggle_subtitle,
            show_subtitle_menu_cmd=self._show_subtitle_menu
        )

        # Configurar estado inicial de subtítulos
        has_subtitle = self.subtitle_path is not None
        self.controls.set_subtitle_state(has_subtitle, self.subtitle_enabled)
        if has_subtitle:
            self.player.video_set_spu(-1)

        # Asignar el callback después de crear los controles
        self.controls.set_volume_change_callback(self._on_volume_change)

        self.controls.pack(fill=tk.X)

        # Configuración de VLC
        vlc_args = ['--no-xlib', '--quiet']
        self.instance = vlc.Instance(vlc_args)
        self.player = self.instance.media_player_new()
        self.media = self.instance.media_new(video_path)

        # Configurar eventos del media
        self.media.parse_with_options(vlc.MediaParseFlag.local, 0)
        events = self.media.event_manager()
        events.event_attach(vlc.EventType.MediaParsedChanged, self.on_media_parsed)

        self.player.set_media(self.media)
        self.player.video_set_scale(0)

        # Configurar ventana según el sistema operativo
        if sys.platform == "linux":
            self.root.update_idletasks()
            x_window_id = self.video_frame.winfo_id()
            self.player.set_xwindow(x_window_id)
        elif sys.platform == "win32":
            self.player.set_hwnd(self.video_frame.winfo_id())
        elif sys.platform == "darwin":
            self.player.set_nsobject(self.video_frame.winfo_id())

        # Variables de estado
        self.is_playing = False
        self.media_ready = False
        self.total_time = 0

        self.root.protocol("WM_DELETE_WINDOW", self.close_player)
        self.root.bind("<Escape>", self._exit_fullscreen_or_close)
        self.root.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.root.bind("<Left>", self._handle_rewind)
        self.root.bind("<Right>", self._handle_forward)
        self.root.bind("<space>", self._handle_play_pause)
        self.root.bind("<Up>", self._handle_volume_up)
        self.root.bind("<Down>", self._handle_volume_down)

        # Duplicar los bindings en el video_frame también
        self.video_frame.bind("<Left>", self._handle_rewind)
        self.video_frame.bind("<Right>", self._handle_forward)
        self.video_frame.bind("<space>", self._handle_play_pause)
        self.video_frame.bind("<Up>", self._handle_volume_up)
        self.video_frame.bind("<Down>", self._handle_volume_down)

        self.video_frame.bind("<Button-1>", lambda e: self.video_frame.focus_set())
        self.video_frame.bind("<Double-Button-1>", lambda e: self._toggle_fullscreen())
        # Iniciar reproductor en hilo separado
        self._start_player_thread()
        self.root.after(1000, self._refresh_duration)  # Comienza después de 1 segundo

        # Iniciar actualización de UI
        self.root.after(100, self.update_ui)
        self._init_fullscreen_controls()
        self.player.audio_set_volume(50)

        # Aplicar estilo unificado desde el inicio (antes del primer frame)
        self.root.update()  # Asegurar que todos los widgets estén creados

        # Configuración unificada para contenedores
        self.control_frame.configure(
            fg_color=self.bg_color,
            bg_color=self.bg_color,
            corner_radius=0,
            border_width=0
        )

        self.progress_frame.configure(
            fg_color=self.bg_color,
            bg_color=self.bg_color,
            corner_radius=0,
            border_width=0
        )

        self.button_frame.configure(
            fg_color=self.bg_color,
            bg_color=self.bg_color,
            corner_radius=0,
            border_width=0
        )

        # Configurar la ProgressBar (el contenedor)
        self.progress.configure(
            fg_color=self.bg_color,
            bg_color=self.bg_color
        )

        self.progress.progress_slider.configure(
            fg_color=self.empty_bar_color,
            progress_color=self.progress_color,
            button_color="#b1bacc",
            button_hover_color="#b1bacc",
            border_width=0,
            corner_radius=5
        )

        # Configurar la etiqueta de tiempo
        self.progress.time_label.configure(
            fg_color=self.bg_color,
            bg_color=self.bg_color,
            text_color="white"
        )

        # Configurar widgets dentro de PlayerControls
        self.controls.configure(
            fg_color=self.bg_color,
            bg_color=self.bg_color,
            corner_radius=0,
            border_width=0
        )

        # Configurar todos los botones manteniendo su apariencia visible
        for widget in self.controls.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                try:
                    widget.configure(
                        fg_color=self.btn_color,  # Color para los botones
                        bg_color=self.bg_color,
                        hover_color="#404348",
                        text_color="white",
                        corner_radius=5  # Mantener un poco de radio en botones
                    )
                except Exception as e:
                    print(f"Error configurando botón: {e}")
            else:
                try:
                    widget.configure(
                        fg_color=self.bg_color,
                        bg_color=self.bg_color
                    )
                except Exception as e:
                    print(f"Error configurando widget: {e}")

        # Configurar el slider de volumen específicamente
        try:
            self.controls.volume_slider.configure(
                fg_color=self.empty_bar_color,  # Color más oscuro para la barra vacía
                bg_color=self.bg_color,
                button_color=self.progress_color,
                button_hover_color="#60656f",
                progress_color=self.progress_color
            )
        except Exception as e:
            print(f"Error configurando volumen: {e}")

        if self.subtitle_path:
            # Intentar desactivar los subtítulos después de 1 segundo (cuando todo esté cargado)
            self.root.after(1000, self._ensure_subtitles_off)

        # Inicializar utilidades Pegasus
        self.pegasus_utils = PegasusUtils()

        # Obtener nombre del video (sin extensión)
        self.video_name = os.path.splitext(os.path.basename(video_path))[0]
        # Configurar eventos adicionales
        self._setup_save_events()

        # Cargar posición guardada si existe
        self.saved_position = self.pegasus_utils.get_video_position(self.video_name)
        if self.saved_position > 0:
            print(f"Posición guardada encontrada: {self.saved_position}ms")
            # Cambiar esto:
            # self.root.after(1000, self._load_saved_position)  # Línea problemática
            # Por esto:
            self.root.after(1000, lambda: self._seek_to_saved_position())  # Nueva línea

        def _load_saved_position(self):
            """Carga la posición guardada del video"""
            if self.saved_position > 0 and self.media_ready:
                self.player.set_time(self.saved_position)
                self.update_ui()

        def close_player(self):
            """Cierra el reproductor guardando la posición actual"""
            if self.is_playing:
                current_position = self.player.get_time()
                if current_position > 0:
                    self.pegasus_utils.save_video_position(self.video_name, current_position)

            self.player.stop()
            self.is_playing = False
            self.root.quit()
            self.root.destroy()

    def _ensure_subtitles_off(self):
        """Asegura que los subtítulos estén desactivados"""
        print("[ENSURE_OFF] Comprobando estado de subtítulos")
        current_spu = self.player.video_get_spu()
        print(f"[ENSURE_OFF] Estado actual: {current_spu}")

        if current_spu != -1 and not self.subtitle_enabled:
            print("[ENSURE_OFF] Subtítulos activados cuando no deberían. Desactivando...")
            self.player.video_set_spu(-1)
            print(f"[ENSURE_OFF] Nuevo estado: {self.player.video_get_spu()}")

    def _find_subtitle_file(self, video_path):
        """Busca archivos de subtítulos con el mismo nombre base"""
        base_path = os.path.splitext(video_path)[0]
        subtitle_extensions = ['.srt', '.sub', '.ass', '.vtt']

        for ext in subtitle_extensions:
            subtitle_path = f"{base_path}{ext}"
            if os.path.exists(subtitle_path):
                return subtitle_path
        return None

    def _toggle_subtitle(self):
        """Alterna entre subtítulos externos/embebidos con manejo detallado"""
        print(f"[TOGGLE] Estado actual antes de toggle: {self.subtitle_enabled}")
        print(f"[TOGGLE] SPU actual antes de toggle: {self.player.video_get_spu()}")
        print(f"[TOGGLE] Subtítulo embebido actual: {self.current_embedded_sub}")

        self.subtitle_enabled = not self.subtitle_enabled
        print(f"[TOGGLE] Nuevo estado después de toggle: {self.subtitle_enabled}")

        if self.subtitle_enabled:
            # Prioridad 1: Subtítulos externos si existen
            if self.subtitle_path:
                print(f"[TOGGLE] Activando subtítulo externo: {self.subtitle_path}")
                try:
                    result = self.player.video_set_subtitle_file(self.subtitle_path)
                    print(f"[TOGGLE] Resultado de cargar subtítulo externo: {result}")
                    self.player.video_set_spu(0)  # Activar track 0 del archivo externo
                    self.current_embedded_sub = -1  # Resetear subtítulo embebido
                except Exception as e:
                    print(f"[TOGGLE] Error al cargar subtítulo externo: {e}")
                    # Fallback a subtítulos embebidos si hay error
                    if self.current_embedded_sub != -1:
                        print("[TOGGLE] Fallback a subtítulo embebido")
                        self.player.video_set_spu(self.current_embedded_sub)

            # Prioridad 2: Subtítulos embebidos si existen y no hay externos
            elif self.current_embedded_sub != -1:
                print(f"[TOGGLE] Activando subtítulo embebido ID: {self.current_embedded_sub}")
                self.player.video_set_spu(self.current_embedded_sub)

            # Prioridad 3: Primer subtítulo embebido si no hay selección previa
            elif self.embedded_subtitles:
                first_sub_id = self.embedded_subtitles[0]["id"]
                print(f"[TOGGLE] Activando primer subtítulo embebido disponible: {first_sub_id}")
                self.player.video_set_spu(first_sub_id)
                self.current_embedded_sub = first_sub_id
        else:
            # Desactivar todos los subtítulos
            print("[TOGGLE] Desactivando todos los subtítulos")
            self.player.video_set_spu(-1)

        # Verificar estado final
        final_spu = self.player.video_get_spu()
        print(f"[TOGGLE] SPU después de toggle: {final_spu}")
        print(f"[TOGGLE] Estado final subtítulos: {'ACTIVO' if final_spu != -1 else 'INACTIVO'}")

        # Actualizar controles UI
        self.controls.set_subtitle_state(
            available=(bool(self.subtitle_path) or bool(self.embedded_subtitles)),
            enabled=self.subtitle_enabled
        )

    def _increase_volume(self):
        """Aumenta el volumen en 5%"""
        current_vol = self.player.audio_get_volume()
        new_vol = min(100, current_vol + 5)
        self.player.audio_set_volume(new_vol)
        self.controls.volume_slider.set(new_vol)
        if self.controls.is_muted and new_vol > 0:
            self._toggle_mute()  # Desmutea si estaba muteado

    def _decrease_volume(self):
        """Disminuye el volumen en 5%"""
        current_vol = self.player.audio_get_volume()
        new_vol = max(0, current_vol - 5)
        self.player.audio_set_volume(new_vol)
        self.controls.volume_slider.set(new_vol)
        if new_vol == 0 and not self.controls.is_muted:
            self._toggle_mute()  # Mutea si llega a 0

    def _toggle_fullscreen(self):
        """Alterna entre modo pantalla completa y normal"""
        if self.is_fullscreen:
            # Salir de pantalla completa
            self._exit_fullscreen()
        else:
            # Entrar en pantalla completa
            self._enter_fullscreen()

        # Actualizar el botón
        self.controls.update_fullscreen_button(self.is_fullscreen)

    def _enter_fullscreen(self):
        """Configura la interfaz para pantalla completa con todos los elementos en color #202227"""
        # Guardar geometría actual para restaurar después
        self.original_geometry = self.root.geometry()

        # Entrar en pantalla completa
        self.root.attributes("-fullscreen", True)
        self.is_fullscreen = True

        # Cambiar a place() para los controles con 60% de ancho y centrado
        self.control_frame.pack_forget()
        self.control_frame.place(
            relx=0.5,
            rely=1.0,
            anchor="s",
            relwidth=0.6,
            y=-20,
            bordermode="outside"
        )

        # Color de fondo para el area de video
        self.video_frame.configure(bg="black")

        # Configuración unificada para contenedores con color #202227
        self.control_frame.configure(
            fg_color="#202227",
            bg_color="#202227",
            corner_radius=0,
            border_width=0
        )

        # Configurar frames internos sin bordes ni esquinas
        self.progress_frame.configure(
            fg_color="#202227",
            bg_color="#202227",
            corner_radius=0,
            border_width=0
        )

        self.button_frame.configure(
            fg_color="#202227",
            bg_color="#202227",
            corner_radius=0,
            border_width=0
        )

        # Configurar la ProgressBar (el contenedor)
        self.progress.configure(
            fg_color="#202227",
            bg_color="#202227"
        )

        # IMPORTANTE: Mantener visible la barra de progreso
        self.progress.progress_slider.configure(
            fg_color="#383838",  # Color más oscuro para la barra vacía
            progress_color="#50555f",  # Color de la barra llena
            border_width=0,
            corner_radius=5  # Un pequeño radio para ver mejor la barra
        )

        # Configurar la etiqueta de tiempo
        self.progress.time_label.configure(
            fg_color="#202227",
            bg_color="#202227",
            text_color="white"
        )

        # Configurar widgets dentro de PlayerControls
        self.controls.configure(
            fg_color="#202227",
            bg_color="#202227",
            corner_radius=0,
            border_width=0
        )

        # Configurar todos los botones manteniendo su apariencia visible
        for widget in self.controls.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                try:
                    widget.configure(
                        fg_color="#303338",  # Color para los botones
                        bg_color="#202227",
                        hover_color="#404348",
                        text_color="white",
                        corner_radius=5  # Mantener un poco de radio en botones
                    )
                except Exception as e:
                    print(f"Error configurando botón: {e}")
            else:
                try:
                    widget.configure(
                        fg_color="#202227",
                        bg_color="#202227"
                    )
                except Exception as e:
                    print(f"Error configurando widget: {e}")

        # Configurar el slider de volumen específicamente
        try:
            self.controls.volume_slider.configure(
                fg_color="#383838",  # Color más oscuro para la barra vacía
                bg_color="#202227",
                button_color="#50555f",
                button_hover_color="#60656f",
                progress_color="#50555f"
            )
        except Exception as e:
            print(f"Error configurando volumen: {e}")

        # Asegurar que los controles estén sobre el video
        self.control_frame.lift()

        # Mostrar controles y configurar temporizador de ocultación
        self.controls_visible = True
        self._reset_hide_controls_timer()

        # Configurar eventos de movimiento del ratón
        self.video_frame.bind("<Motion>", self._on_mouse_motion)
        self.root.bind("<Motion>", self._on_mouse_motion)

        # Mantener el foco en el área de video
        self.video_frame.focus_set()
        self.root.after(100, lambda: self.video_frame.focus_force())

    def _exit_fullscreen(self):
        """Restaura la interfaz a modo normal manteniendo los colores unificados"""
        self.root.attributes("-fullscreen", False)
        self.root.geometry(self.original_geometry)
        self.is_fullscreen = False

        # Restaurar el layout normal
        self.control_frame.place_forget()
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        self.control_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=0, pady=0)

        # Mantener los mismos colores que en pantalla completa
        self.video_frame.configure(bg="black")

        # Configuración unificada para contenedores
        self.control_frame.configure(
            fg_color="#202227",
            bg_color="#202227",
            corner_radius=0,
            border_width=0
        )

        self.progress_frame.configure(
            fg_color="#202227",
            bg_color="#202227",
            corner_radius=0,
            border_width=0
        )

        self.button_frame.configure(
            fg_color="#202227",
            bg_color="#202227",
            corner_radius=0,
            border_width=0
        )

        # Configurar la ProgressBar (el contenedor)
        self.progress.configure(
            fg_color="#202227",
            bg_color="#202227"
        )

        # Mantener visible la barra de progreso
        self.progress.progress_slider.configure(
            fg_color="#383838",  # Color más oscuro para la barra vacía
            progress_color="#50555f",  # Color de la barra llena
            border_width=0,
            corner_radius=5  # Un pequeño radio para ver mejor la barra
        )

        # Configurar la etiqueta de tiempo
        self.progress.time_label.configure(
            fg_color="#202227",
            bg_color="#202227",
            text_color="white"
        )

        self.controls.configure(
            fg_color="#202227",
            bg_color="#202227",
            corner_radius=0,
            border_width=0
        )

        for widget in self.controls.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                try:
                    widget.configure(
                        fg_color="#303338",  # Color para los botones
                        bg_color="#202227",
                        hover_color="#404348",
                        text_color="white",
                        corner_radius=5  # Mantener un poco de radio en botones
                    )
                except Exception as e:
                    print(f"Error configurando botón: {e}")
            else:
                try:
                    widget.configure(
                        fg_color="#202227",
                        bg_color="#202227"
                    )
                except Exception as e:
                    print(f"Error configurando widget: {e}")

        try:
            self.controls.volume_slider.configure(
                fg_color="#383838",
                bg_color="#202227",
                button_color="#50555f",
                button_hover_color="#60656f",
                progress_color="#50555f"
            )
        except Exception as e:
            print(f"Error configurando volumen: {e}")

    def _exit_fullscreen_or_close(self, event=None):
        if self.is_fullscreen:
            self._toggle_fullscreen()
        else:
            self._confirm_exit()

    def _confirm_exit(self):
        was_playing = self.player.is_playing()
        if was_playing:
            self.player.pause()
            self.is_playing = False
            self.controls.update_play_pause_button(False)

        # Crear ventana de diálogo
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Confirmar salida")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()

        def on_cancel():
            dialog.destroy()
            if was_playing:
                self.player.play()
                self.is_playing = True
                self.controls.update_play_pause_button(True)

        def on_exit():
            dialog.destroy()
            self._save_and_close()

        # Frame principal
        frame = ctk.CTkFrame(dialog)
        frame.pack(padx=20, pady=20, fill='both', expand=True)

        # Mensaje
        label = ctk.CTkLabel(
            frame,
            text="¿Estás seguro que quieres salir del reproductor?\nSe guardará la posición actual.",
            wraplength=350
        )
        label.pack(pady=10)

        # Frame para botones
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=10)

        # Botón Cancelar
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=on_cancel
        )
        cancel_btn.pack(side='left', padx=10)

        # Botón Salir
        exit_btn = ctk.CTkButton(
            btn_frame,
            text="Salir",
            command=on_exit,
            fg_color="#d9534f",
            hover_color="#c9302c"
        )
        exit_btn.pack(side='left', padx=10)

        # Centrar diálogo
        self._center_window(dialog)

        # Manejar cierre de la ventana (ej. con la X)
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)

    def _save_and_close(self):
        """Guarda la posición y cierra el reproductor"""
        self._save_position()
        self.close_player()

    def _center_window(self, window):
        """Centra una ventana en la pantalla"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def _seek_video(self, position):
        """Salta a una posición y guarda"""
        if not self.media_ready:
            self.total_time = self.media.get_duration()
            self.media_ready = (self.total_time > 0)

        if self.media_ready and self.total_time > 0:
            target_time = int(position * self.total_time)
            self.player.set_time(target_time)
            self.update_ui()
            self._save_position_after_action()  # Guardar después de buscar

    def _refresh_duration(self):
        """Intenta obtener la duración del video manualmente"""
        if not self.media_ready:
            self.total_time = self.media.get_duration()
            self.media_ready = (self.total_time > 0)
        self.root.after(1000, self._refresh_duration)  # Reintentar cada segundo

    def _setup_vlc(self, video_path):
        """Configura el reproductor VLC"""
        vlc_args = [
            '--no-xlib',
            '--quiet',
            '--no-sub-autodetect-file'  # Desactiva autodetección de subtítulos
        ]
        print("[SETUP_VLC] Configurando VLC con flags para desactivar subtítulos")
        self.instance = vlc.Instance(vlc_args)
        self.player = self.instance.media_player_new()
        self.media = self.instance.media_new(video_path)

        # Desactivar subtítulos antes de iniciar la reproducción
        print("[SETUP_VLC] Desactivando subtítulos explícitamente")
        self.player.video_set_spu(-1)

        # Configurar eventos
        self.media.parse_with_options(vlc.MediaParseFlag.local, 0)
        events = self.media.event_manager()
        events.event_attach(vlc.EventType.MediaParsedChanged, self.on_media_parsed)

        self.player.set_media(self.media)
        self.player.video_set_scale(0)

        # Configurar ventana según el sistema operativo
        if sys.platform == "linux":
            self.root.update_idletasks()
            x_window_id = self.video_frame.winfo_id()
            self.player.set_xwindow(x_window_id)
        elif sys.platform == "win32":
            self.player.set_hwnd(self.video_frame.winfo_id())
        elif sys.platform == "darwin":
            self.player.set_nsobject(self.video_frame.winfo_id())

    def _start_player_thread(self):
        """Inicia el reproductor en un hilo separado"""
        self.player_thread = Thread(target=self._start_player)
        self.player_thread.daemon = True
        self.player_thread.start()

    def _start_player(self):
        time.sleep(0.5)
        # Comprobar estado de los subtítulos antes y después
        print(f"[START_PLAYER] Estado de subtítulos antes: {self.player.video_get_spu()}")
        # Desactivar subtítulos al inicio
        self.player.video_set_spu(-1)
        print(f"[START_PLAYER] Estado de subtítulos después de desactivar: {self.player.video_get_spu()}")
        print(f"Estado inicial del reproductor: {self.player.get_state()}")

        self.root.after(1000, lambda: self.video_frame.focus_set())

        # Eliminar la línea problemática: self.player.video_set_subtitle_delay(0)
        # También quitar el bloque try/except con video_set_spu_enabled

        self.player.play()
        self.is_playing = True
        print(f"Estado después de play(): {self.player.get_state()}")

        # Esperar a que el video esté listo (solución previa)
        timeout = time.time() + 5
        while not self.media_ready and time.time() < timeout:
            time.sleep(0.1)

        self._detect_embedded_subtitles()

        # Desactivar escalado automático y usar relación de aspecto nativa
        self.player.video_set_scale(0)  # 0 = sin escalado forzado
        self.player.video_set_aspect_ratio("")  # Cadena vacía = usa la relación original

        # Actualizar UI
        self.root.after(0, lambda: self.controls.update_play_pause_button(True))

        while self.is_playing:
            time.sleep(0.1)
            if not self.player.is_playing() and self.player.get_state() == vlc.State.Ended:
                self.root.after(0, self.close_player)
                break

    def _detect_embedded_subtitles(self):
        """Detecta subtítulos embebidos en el video"""
        try:
            # Esperar a que el reproductor esté listo
            timeout = time.time() + 5
            while not self.player.is_playing() and time.time() < timeout:
                time.sleep(0.1)

            # Obtener tracks de subtítulos
            track_list = self.player.video_get_spu_description()
            print(f"[SUBTITLE_DETECT] Raw tracks: {track_list}")

            if track_list:
                # Filtrar para excluir la opción "Disable" (-1)
                self.embedded_subtitles = [
                    {"id": track[0], "name": track[1].decode('utf-8') if isinstance(track[1], bytes) else track[1]}
                    for track in track_list if track[0] != -1
                ]
                print(f"[SUBTITLE_DETECT] Subtítulos embebidos encontrados: {self.embedded_subtitles}")

                # Actualizar controles
                self.root.after(0, lambda: self.controls.set_embedded_subtitles_state(bool(self.embedded_subtitles)))
            else:
                print("[SUBTITLE_DETECT] No se encontraron subtítulos embebidos")
                self.embedded_subtitles = []
        except Exception as e:
            print(f"[SUBTITLE_DETECT] Error detectando subtítulos embebidos: {str(e)}")
            self.embedded_subtitles = []

    def _show_subtitle_menu(self):
        """Muestra el menú de selección de subtítulos embebidos"""
        if not hasattr(self, '_subtitle_menu'):
            self._subtitle_menu = SubtitleMenu(
                root=self.root,
                parent_frame=self.control_frame,
                embedded_subtitles=self.embedded_subtitles,
                select_callback=self._select_embedded_subtitle
            )

        self._subtitle_menu.show(self.controls.embedded_sub_button)

    def _select_embedded_subtitle(self, sub_id):
        """Selecciona subtítulo y cierra el menú"""
        self.current_embedded_sub = sub_id
        self.player.video_set_spu(sub_id)

        # Actualizar estado del botón de subtítulos
        self.subtitle_enabled = (sub_id != -1)
        self.controls.set_subtitle_state(True, self.subtitle_enabled)

        # Cerrar el menú
        if hasattr(self, 'subtitle_menu') and self.subtitle_menu.winfo_exists():
            self.subtitle_menu.destroy()

        print(f"Subtítulo embebido seleccionado: ID={sub_id}")

    def on_media_parsed(self, event):
        """Callback cuando el media está listo"""
        self.media_ready = True
        self.total_time = self.media.get_duration()

        # Comprobar si los subtítulos se han activado automáticamente
        current_spu = self.player.video_get_spu()
        print(f"[MEDIA_PARSED] Media preparado. Estado actual de subtítulos: {current_spu}")

        # Si se han activado automáticamente, desactivarlos
        if current_spu != -1 and not self.subtitle_enabled:
            print("[MEDIA_PARSED] Detectada activación automática de subtítulos. Desactivando...")
            self.player.video_set_spu(-1)
            print(f"[MEDIA_PARSED] Nuevo estado de subtítulos: {self.player.video_get_spu()}")

    def update_ui(self):
        """Actualiza la interfaz de usuario"""
        if self.is_playing:
            position = self.player.get_time()

            if self.total_time <= 0 and self.media_ready:
                self.total_time = self.media.get_duration()

            if position >= 0 and self.total_time > 0:
                self.progress.update_progress(position, self.total_time)

        self.root.after(100, self.update_ui)

    def _seek_to_saved_position(self, attempts=5):
        if attempts <= 0:
            print("No se pudo cargar la posición guardada - demasiados intentos")
            return

        print(f"Intentando cargar posición guardada (intentos restantes: {attempts})")
        print(f"Media ready: {self.media_ready}, Player exists: {hasattr(self, 'player')}")

        if self.saved_position > 0:
            if self.media_ready and hasattr(self, 'player') and self.player:
                print(f"Saltando a posición guardada: {self.saved_position}ms")
                self.player.set_time(self.saved_position)
                self.update_ui()
            else:
                print("Media no listo, reintentando...")
                self.root.after(500, lambda: self._seek_to_saved_position(attempts-1))

    def _save_position(self):
        """Guarda la posición actual del video"""
        if self.is_playing or self.player.get_state() == vlc.State.Paused:
            current_pos = self.player.get_time()
            if current_pos > 0:
                self.pegasus_utils.save_video_position(self.video_name, current_pos)
                print(f"Posición guardada: {current_pos}ms")

    def _setup_save_events(self):
        """Configura eventos para guardar el progreso"""
        # Guardar al pausar/reanudar
        self.root.bind("<space>", lambda e: self._save_position_after_action())

        # Guardar al hacer clic en la barra de progreso
        self.progress.progress_slider.bind("<ButtonRelease-1>",
                                         lambda e: self._save_position())

        # Guardar al avanzar/retroceder
        self.root.bind("<Left>", lambda e: self._save_position_after_action())
        self.root.bind("<Right>", lambda e: self._save_position_after_action())

    def _save_position_after_action(self, delay=500):
        """Guarda la posición después de un pequeño retraso"""
        self.root.after(delay, self._save_position)

    def toggle_play_pause(self, event=None):
        """Alterna entre play/pause y guarda posición"""
        print("[DEBUG] Ejecutando toggle_play_pause")
        if hasattr(self, 'player') and self.player:
            print(f"Estado actual: {'Reproduciendo' if self.player.is_playing() else 'Pausado'}")
            if self.player.is_playing():
                print("Pausando reproducción...")
                self.player.pause()
                self.is_playing = False
                self._save_position()
            else:
                print("Iniciando reproducción...")
                self.player.play()
                self.is_playing = True
                self._save_position_after_action()

            print(f"Nuevo estado: {'Reproduciendo' if self.player.is_playing() else 'Pausado'}")
            self.controls.update_play_pause_button(self.is_playing)

    def close_player(self):
        """Cierra el reproductor guardando la posición"""
        if hasattr(self, 'player') and self.player:
            current_pos = self.player.get_time()
            if current_pos > 0:
                self.pegasus_utils.save_video_position(self.video_name, current_pos)
                print(f"Posición final guardada: {current_pos}ms")

            self.player.stop()
            self.is_playing = False

        if hasattr(self, 'root'):
            self.root.quit()
            self.root.destroy()

    def run(self):
        """Inicia el bucle principal"""
        self.root.mainloop()

    def _rewind_10s(self, event=None):
        """Retrocede 10 segundos y guarda posición"""
        print("[DEBUG] Ejecutando _rewind_10s")
        if self.media_ready and hasattr(self, 'player') and self.player:
            current_time = self.player.get_time()
            print(f"Tiempo actual: {current_time}")
            new_time = max(0, current_time - 10000)
            print(f"Nuevo tiempo: {new_time}")
            self.player.set_time(new_time)
            print(f"Tiempo después de set_time: {self.player.get_time()}")
            self.update_ui()
            self._save_position_after_action()

    def _forward_10s(self, event=None):
        """Avanza 10 segundos y guarda posición"""
        print("[DEBUG] Ejecutando _forward_10s")
        if self.media_ready and hasattr(self, 'player') and self.player and self.total_time > 0:
            current_time = self.player.get_time()
            print(f"Tiempo actual: {current_time}")
            new_time = min(self.total_time, current_time + 10000)
            print(f"Nuevo tiempo: {new_time}")
            self.player.set_time(new_time)
            print(f"Tiempo después de set_time: {self.player.get_time()}")
            self.update_ui()
            self._save_position_after_action()

    def _toggle_mute(self):
        """Alterna entre muteado y con volumen"""
        current_volume = self.player.audio_get_volume()
        if current_volume > 0:
            self.last_volume = current_volume
            self.player.audio_set_volume(0)
            self.controls.volume_slider.set(0)
        else:
            volume = getattr(self, 'last_volume', 50)
            self.player.audio_set_volume(volume)
            self.controls.volume_slider.set(volume)

        # Actualizar estado en controles
        is_muted = (self.player.audio_get_volume() == 0)
        self.controls.is_muted = is_muted
        self.controls._update_mute_icon()  # Esto actualizará el icono

    def _on_volume_change(self, volume):
        """Maneja cambios en el volumen"""
        volume = int(float(volume))  # Asegurar que es entero

        # Actualizar volumen en VLC
        self.player.audio_set_volume(volume)

        # Actualizar estado de mute (si volumen llega a 0)
        is_muted = (volume == 0)
        if is_muted != self.controls.is_muted:
            self._toggle_mute()  # Esto actualizará tanto el estado como el icono

        # Guardar último volumen si no está muteado
        if volume > 0:
            self.last_volume = volume

    def _on_mouse_motion(self, event):
        """Maneja el movimiento del ratón en modo pantalla completa"""
        if self.is_fullscreen:
            # Solo mostrar controles si están ocultos actualmente
            if not self.controls_visible:
                self._show_controls()
            # Reiniciar temporizador para ocultarlos
            self._reset_hide_controls_timer()

            # Actualizar posición del mouse para el sistema de inactividad
            self.last_mouse_position = (event.x, event.y)
            self.mouse_idle_time = 0

    def _show_controls(self):
        """Muestra los controles manteniendo el 60% de ancho"""
        if self.is_fullscreen and not self.controls_visible:
            self.control_frame.place(
                relx=0.5,
                rely=1.0,
                anchor="s",
                relwidth=0.6,  # Mantener 60% de ancho
                y=-20,         # Mismo margen que en _enter_fullscreen
                bordermode="outside"
            )
            self.control_frame.lift()
            self.controls_visible = True
            self._reset_hide_controls_timer()

    def _hide_controls(self):
        """Oculta los controles"""
        if self.is_fullscreen and self.controls_visible:
            self.control_frame.place_forget()
            self.controls_visible = False
        self.hide_controls_timer_id = None

    def _reset_hide_controls_timer(self):
        """Reinicia el temporizador para ocultar los controles"""
        # Cancelar temporizador existente si hay uno
        if hasattr(self, 'hide_controls_timer_id') and self.hide_controls_timer_id:
            self.root.after_cancel(self.hide_controls_timer_id)

        # Configurar nuevo temporizador (3 segundos)
        self.hide_controls_timer_id = self.root.after(1000, self._hide_controls)

    def _init_fullscreen_controls(self):
        """Inicializa el sistema de control para pantalla completa"""
        # Crear un estado de control
        self.controls_visible = True
        self.last_mouse_position = (0, 0)
        self.mouse_idle_time = 0

        # Iniciar un temporizador para verificar el estado del mouse
        self.root.after(100, self._check_mouse_activity)

    def _check_mouse_activity(self):
        """Verifica periódicamente si el mouse se ha movido"""
        if self.is_fullscreen:
            # Obtener posición actual del mouse
            mouse_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
            mouse_y = self.root.winfo_pointery() - self.root.winfo_rooty()
            current_pos = (mouse_x, mouse_y)

            # Comparar con la última posición conocida
            if current_pos != self.last_mouse_position:
                #print(f"Mouse movido a: {current_pos}")
                self.last_mouse_position = current_pos
                self.mouse_idle_time = 0

                # Mostrar controles si están ocultos
                if not self.controls_visible:
                    self._show_controls()
            else:
                # Incrementar tiempo de inactividad
                self.mouse_idle_time += 100  # 100ms

                # Ocultar controles si han pasado 3 segundos sin movimiento
                if self.mouse_idle_time > 3000 and self.controls_visible:
                    self._hide_controls()

        # Programar la próxima verificación
        self.root.after(100, self._check_mouse_activity)

    def _handle_rewind(self, event=None):
        print("[DEBUG] Tecla izquierda presionada - Retroceder 10s")
        self._rewind_10s()
        return "break"

    def _handle_forward(self, event=None):
        print("[DEBUG] Tecla derecha presionada - Avanzar 10s")
        self._forward_10s()
        return "break"

    def _handle_play_pause(self, event=None):
        print("[DEBUG] Barra espaciadora presionada - Play/Pause")
        self.toggle_play_pause()
        return "break"

    def _handle_volume_up(self, event=None):
        self._increase_volume()
        return "break"

    def _handle_volume_down(self, event=None):
        self._decrease_volume()
        return "break"
