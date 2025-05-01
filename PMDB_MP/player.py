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
from PMDB_MP.locales import get_locale
import traceback
import ctypes
from ctypes.util import find_library


class VideoPlayer:
    def __init__(self, video_path, language='es'):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        from PMDB_MP.locales import get_locale
        self.locale = get_locale(language)
        video_name = os.path.basename(video_path)
        self.bg_color = "#202227"
        self.bg_color2 = "black"
        self.btn_color = "#303338"
        self.progress_color = "#50555f"
        self.empty_bar_color = "#383838"
        self.root = ctk.CTk()
        self.root.title(self.locale["player_title"].format(video_name))
        self.root.geometry("800x600")
        self.root.minsize(600,400)
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

        self.root.update()
        self.controls_visible = True
        self.video_frame = tk.Frame(self.root, bg=self.bg_color2)
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        self.control_frame = ctk.CTkFrame(self.root)
        self.control_frame.pack(fill=tk.X, padx=0, pady=0)
        self.progress_frame = ctk.CTkFrame(self.control_frame)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.progress = ProgressBar(self.progress_frame)
        self.progress.pack(fill=tk.X)
        self.progress.set_seek_callback(self._seek_video)
        self.button_frame = ctk.CTkFrame(self.control_frame)
        self.button_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.is_fullscreen = False
        self.original_geometry = self.root.geometry()
        self._setup_vlc(video_path)
        self.subtitle_path = self._find_subtitle_file(video_path)
        self.subtitle_enabled = False

        print(f"[INIT] ¿Subtítulo encontrado?: {self.subtitle_path is not None}")
        print(f"[INIT] Estado inicial de subtítulo: {self.subtitle_enabled}")

        if self.subtitle_path:
            print(f"[INIT] Intentando cargar pero desactivar subtítulo: {self.subtitle_path}")
            print(f"[INIT] Estado de subtítulos antes de configurar: {self.player.video_get_spu()}")
            self.player.video_set_subtitle_file(self.subtitle_path)
            self.player.video_set_spu(-1)
            print(f"[INIT] Estado de subtítulos después de configurar: {self.player.video_get_spu()}")

        self.player.video_set_spu(-1)
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
            show_subtitle_menu_cmd=self._show_subtitle_menu,
            locale=self.locale
        )

        has_subtitle = self.subtitle_path is not None
        self.controls.set_subtitle_state(has_subtitle, self.subtitle_enabled)
        if has_subtitle:
            self.player.video_set_spu(-1)

        self.controls.set_volume_change_callback(self._on_volume_change)
        self.controls.pack(fill=tk.X)

        events = self.media.event_manager()
        events.event_attach(vlc.EventType.MediaParsedChanged, self.on_media_parsed)

        self.player.set_media(self.media)
        self.player.video_set_scale(0)

        if sys.platform == "linux":
            self.root.update_idletasks()
            x_window_id = self.video_frame.winfo_id()
            self.player.set_xwindow(x_window_id)
        elif sys.platform == "win32":
            self.player.set_hwnd(self.video_frame.winfo_id())
        elif sys.platform == "darwin":
            self.player.set_nsobject(self.video_frame.winfo_id())

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
        self.video_frame.bind("<Left>", self._handle_rewind)
        self.video_frame.bind("<Right>", self._handle_forward)
        self.video_frame.bind("<space>", self._handle_play_pause)
        self.video_frame.bind("<Up>", self._handle_volume_up)
        self.video_frame.bind("<Down>", self._handle_volume_down)
        self.video_frame.bind("<Button-1>", lambda e: self.video_frame.focus_set())
        self.video_frame.bind("<Double-Button-1>", lambda e: self._toggle_fullscreen())
        self._start_player_thread()
        self.root.after(1000, self._refresh_duration)
        self.root.after(100, self.update_ui)
        self._init_fullscreen_controls()
        self.player.audio_set_volume(50)
        self.root.update()

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

        self.progress.time_label.configure(
            fg_color=self.bg_color,
            bg_color=self.bg_color,
            text_color="white"
        )

        self.controls.configure(
            fg_color=self.bg_color,
            bg_color=self.bg_color,
            corner_radius=0,
            border_width=0
        )

        for widget in self.controls.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                try:
                    widget.configure(
                        fg_color=self.btn_color,
                        bg_color=self.bg_color,
                        hover_color="#404348",
                        text_color="white",
                        corner_radius=5
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

        try:
            self.controls.volume_slider.configure(
                fg_color=self.empty_bar_color,
                bg_color=self.bg_color,
                button_color=self.progress_color,
                button_hover_color="#60656f",
                progress_color=self.progress_color
            )
        except Exception as e:
            print(f"Error configurando volumen: {e}")

        if self.subtitle_path:
            self.root.after(1000, self._ensure_subtitles_off)
        self.pegasus_utils = PegasusUtils()
        self.video_name = os.path.splitext(os.path.basename(video_path))[0]
        self._setup_save_events()
        self.saved_position = self.pegasus_utils.get_video_position(self.video_name)
        if self.saved_position > 0:
            print(f"Posición guardada encontrada: {self.saved_position}ms")
            self.root.after(1000, lambda: self._seek_to_saved_position())

        def _load_saved_position(self):
            if self.saved_position > 0 and self.media_ready:
                self.player.set_time(self.saved_position)
                self.update_ui()

        def close_player(self):
            try:
                if hasattr(self, 'player') and self.player:
                    player_state = self.player.get_state()
                    if player_state != vlc.State.Ended:
                        current_pos = self.player.get_time()
                        if current_pos > 0:
                            self.pegasus_utils.save_video_position(self.video_name, current_pos)
                            print(f"Posición final guardada: {current_pos}ms")

                    self.player.stop()
                    self.player.release()
                    self.is_playing = False

                if hasattr(self, 'instance') and self.instance:
                    self.instance.release()

            except Exception as e:
                print(f"Error al cerrar el reproductor: {e}")

            if hasattr(self, 'root'):
                self.root.quit()
                self.root.destroy()

    def _ensure_subtitles_off(self):
        print("[ENSURE_OFF] Comprobando estado de subtítulos")
        current_spu = self.player.video_get_spu()
        print(f"[ENSURE_OFF] Estado actual: {current_spu}")

        if current_spu != -1 and not self.subtitle_enabled:
            print("[ENSURE_OFF] Subtítulos activados cuando no deberían. Desactivando...")
            self.player.video_set_spu(-1)
            print(f"[ENSURE_OFF] Nuevo estado: {self.player.video_get_spu()}")

    def _find_subtitle_file(self, video_path):
        base_path = os.path.splitext(video_path)[0]
        subtitle_extensions = ['.srt', '.sub', '.ass', '.vtt']

        for ext in subtitle_extensions:
            subtitle_path = f"{base_path}{ext}"
            if os.path.exists(subtitle_path):
                return subtitle_path
        return None

    def _toggle_subtitle(self):
        print(f"[TOGGLE] Estado actual antes de toggle: {self.subtitle_enabled}")
        print(f"[TOGGLE] SPU actual antes de toggle: {self.player.video_get_spu()}")
        print(f"[TOGGLE] Subtítulo embebido actual: {self.current_embedded_sub}")
        self.subtitle_enabled = not self.subtitle_enabled
        print(f"[TOGGLE] Nuevo estado después de toggle: {self.subtitle_enabled}")

        if self.subtitle_enabled:
            if self.subtitle_path:
                print(f"[TOGGLE] Activando subtítulo externo: {self.subtitle_path}")
                try:
                    result = self.player.video_set_subtitle_file(self.subtitle_path)
                    print(f"[TOGGLE] Resultado de cargar subtítulo externo: {result}")
                    self.player.video_set_spu(0)
                    self.current_embedded_sub = -1
                except Exception as e:
                    print(f"[TOGGLE] Error al cargar subtítulo externo: {e}")
                    if self.current_embedded_sub != -1:
                        print("[TOGGLE] Fallback a subtítulo embebido")
                        self.player.video_set_spu(self.current_embedded_sub)

            elif self.current_embedded_sub != -1:
                print(f"[TOGGLE] Activando subtítulo embebido ID: {self.current_embedded_sub}")
                self.player.video_set_spu(self.current_embedded_sub)

            elif self.embedded_subtitles:
                first_sub_id = self.embedded_subtitles[0]["id"]
                print(f"[TOGGLE] Activando primer subtítulo embebido disponible: {first_sub_id}")
                self.player.video_set_spu(first_sub_id)
                self.current_embedded_sub = first_sub_id
        else:
            print("[TOGGLE] Desactivando todos los subtítulos")
            self.player.video_set_spu(-1)

        final_spu = self.player.video_get_spu()
        print(f"[TOGGLE] SPU después de toggle: {final_spu}")
        print(f"[TOGGLE] Estado final subtítulos: {'ACTIVO' if final_spu != -1 else 'INACTIVO'}")

        self.controls.set_subtitle_state(
            available=(bool(self.subtitle_path) or bool(self.embedded_subtitles)),
            enabled=self.subtitle_enabled
        )

    def _increase_volume(self):
        current_vol = self.player.audio_get_volume()
        new_vol = min(100, current_vol + 5)
        self.player.audio_set_volume(new_vol)
        self.controls.volume_slider.set(new_vol)
        if self.controls.is_muted and new_vol > 0:
            self._toggle_mute()

    def _decrease_volume(self):
        current_vol = self.player.audio_get_volume()
        new_vol = max(0, current_vol - 5)
        self.player.audio_set_volume(new_vol)
        self.controls.volume_slider.set(new_vol)
        if new_vol == 0 and not self.controls.is_muted:
            self._toggle_mute()

    def _toggle_fullscreen(self):
        if self.is_fullscreen:
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()
        self.controls.update_fullscreen_button(self.is_fullscreen)

    def _enter_fullscreen(self):
        self.original_geometry = self.root.geometry()
        self.root.attributes("-fullscreen", True)
        self.is_fullscreen = True
        self.control_frame.pack_forget()
        self.control_frame.place(
            relx=0.5,
            rely=1.0,
            anchor="s",
            relwidth=0.6,
            y=-20,
            bordermode="outside"
        )

        self.video_frame.configure(bg="black")
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

        self.progress.configure(
            fg_color="#202227",
            bg_color="#202227"
        )

        self.progress.progress_slider.configure(
            fg_color="#383838",
            progress_color="#50555f",
            border_width=0,
            corner_radius=5
        )

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
                        fg_color="#303338",
                        bg_color="#202227",
                        hover_color="#404348",
                        text_color="white",
                        corner_radius=5
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
        self.control_frame.lift()
        self.controls_visible = True
        self._reset_hide_controls_timer()
        self.video_frame.bind("<Motion>", self._on_mouse_motion)
        self.root.bind("<Motion>", self._on_mouse_motion)
        self.video_frame.focus_set()
        self.root.after(100, lambda: self.video_frame.focus_force())

    def _exit_fullscreen(self):
        self.root.attributes("-fullscreen", False)
        self.root.geometry(self.original_geometry)
        self.is_fullscreen = False
        self.control_frame.place_forget()
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        self.control_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=0, pady=0)
        self.video_frame.configure(bg="black")

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

        self.progress.configure(
            fg_color="#202227",
            bg_color="#202227"
        )

        self.progress.progress_slider.configure(
            fg_color="#383838",
            progress_color="#50555f",
            border_width=0,
            corner_radius=5
        )

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
                        fg_color="#303338",
                        bg_color="#202227",
                        hover_color="#404348",
                        text_color="white",
                        corner_radius=5
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
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(self.locale["confirm_exit_title"],)
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
        frame = ctk.CTkFrame(dialog)
        frame.pack(padx=20, pady=20, fill='both', expand=True)

        label = ctk.CTkLabel(
            frame,
            text=self.locale["confirm_exit_message"],
            wraplength=350
        )
        label.pack(pady=10)
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=10)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=self.locale["cancel_button"],
            command=on_cancel
        )
        cancel_btn.pack(side='left', padx=10)

        exit_btn = ctk.CTkButton(
            btn_frame,
            text=self.locale["exit_button"],
            command=on_exit,
            fg_color="#d9534f",
            hover_color="#c9302c"
        )
        exit_btn.pack(side='left', padx=10)
        self._center_window(dialog)
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)

    def _save_and_close(self):
        self._save_position()
        self.close_player()

    def _center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def _seek_video(self, position):
        if not self.media_ready:
            self.total_time = self.media.get_duration()
            self.media_ready = (self.total_time > 0)

        if self.media_ready and self.total_time > 0:
            target_time = int(position * self.total_time)
            self.player.set_time(target_time)
            self.update_ui()
            self._save_position_after_action()

    def _refresh_duration(self):
        if not self.media_ready:
            self.total_time = self.media.get_duration()
            self.media_ready = (self.total_time > 0)
        self.root.after(1000, self._refresh_duration)

    def _setup_vlc(self, video_path):
        vlc_args = [
            '--no-xlib',
            '--quiet',
            '--no-sub-autodetect-file'
        ]
        print("[SETUP_VLC] Configurando VLC con flags para desactivar subtítulos")
        self.instance = vlc.Instance(vlc_args)
        self.player = self.instance.media_player_new()
        self.media = self.instance.media_new(video_path)
        print("[SETUP_VLC] Desactivando subtítulos explícitamente")
        self.player.video_set_spu(-1)
        self.media.parse_with_options(vlc.MediaParseFlag.local, 0)
        events = self.media.event_manager()
        events.event_attach(vlc.EventType.MediaParsedChanged, self.on_media_parsed)

        self.player.set_media(self.media)
        self.player.video_set_scale(0)
        if sys.platform == "linux":
            self.root.update_idletasks()
            x_window_id = self.video_frame.winfo_id()
            self.player.set_xwindow(x_window_id)
        elif sys.platform == "win32":
            self.player.set_hwnd(self.video_frame.winfo_id())
        elif sys.platform == "darwin":
            self.player.set_nsobject(self.video_frame.winfo_id())

    def _start_player_thread(self):
        self.player_thread = Thread(target=self._start_player)
        self.player_thread.daemon = True
        self.player_thread.start()

    def _start_player(self):
        time.sleep(0.5)
        print(f"[START_PLAYER] Estado de subtítulos antes: {self.player.video_get_spu()}")
        self.player.video_set_spu(-1)
        print(f"[START_PLAYER] Estado de subtítulos después de desactivar: {self.player.video_get_spu()}")
        print(f"Estado inicial del reproductor: {self.player.get_state()}")

        self.root.after(1000, lambda: self.video_frame.focus_set())
        self.player.play()
        self.is_playing = True
        print(f"Estado después de play(): {self.player.get_state()}")
        timeout = time.time() + 5
        while not self.media_ready and time.time() < timeout:
            time.sleep(0.1)

        self._detect_embedded_subtitles()
        self.player.video_set_scale(0)
        self.player.video_set_aspect_ratio("")
        self.root.after(0, lambda: self.controls.update_play_pause_button(True))

        while self.is_playing:
            time.sleep(0.1)
            player_state = self.player.get_state()

            if player_state == vlc.State.Ended:
                print("Video terminado, eliminando posición guardada...")
                self.pegasus_utils.remove_video_position(self.video_name)
                self.root.after(0, self.close_player)
                break

    def _detect_embedded_subtitles(self):
        try:
            timeout = time.time() + 5
            while not self.player.is_playing() and time.time() < timeout:
                time.sleep(0.1)
            track_list = self.player.video_get_spu_description()
            print(f"[SUBTITLE_DETECT] Raw tracks: {track_list}")

            if track_list:
                self.embedded_subtitles = [
                    {"id": track[0], "name": track[1].decode('utf-8') if isinstance(track[1], bytes) else track[1]}
                    for track in track_list if track[0] != -1
                ]
                print(f"[SUBTITLE_DETECT] Subtítulos embebidos encontrados: {self.embedded_subtitles}")
                self.root.after(0, lambda: self.controls.set_embedded_subtitles_state(bool(self.embedded_subtitles)))
            else:
                print("[SUBTITLE_DETECT] No se encontraron subtítulos embebidos")
                self.embedded_subtitles = []
        except Exception as e:
            print(f"[SUBTITLE_DETECT] Error detectando subtítulos embebidos: {str(e)}")
            self.embedded_subtitles = []

    def _show_subtitle_menu(self):
        if not hasattr(self, '_subtitle_menu'):
            self._subtitle_menu = SubtitleMenu(
                root=self.root,
                parent_frame=self.control_frame,
                embedded_subtitles=self.embedded_subtitles,
                select_callback=self._select_embedded_subtitle,
                locale=self.locale
            )

        self._subtitle_menu.show(self.controls.embedded_sub_button)

    def _select_embedded_subtitle(self, sub_id):
        self.current_embedded_sub = sub_id
        self.player.video_set_spu(sub_id)
        self.subtitle_enabled = (sub_id != -1)
        self.controls.set_subtitle_state(True, self.subtitle_enabled)

        if hasattr(self, 'subtitle_menu') and self.subtitle_menu.winfo_exists():
            self.subtitle_menu.destroy()

        print(f"Subtítulo embebido seleccionado: ID={sub_id}")

    def on_media_parsed(self, event):
        self.media_ready = True
        self.total_time = self.media.get_duration()
        current_spu = self.player.video_get_spu()
        print(f"[MEDIA_PARSED] Media preparado. Estado actual de subtítulos: {current_spu}")

        if current_spu != -1 and not self.subtitle_enabled:
            print("[MEDIA_PARSED] Detectada activación automática de subtítulos. Desactivando...")
            self.player.video_set_spu(-1)
            print(f"[MEDIA_PARSED] Nuevo estado de subtítulos: {self.player.video_get_spu()}")

    def update_ui(self):
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
        if self.is_playing or self.player.get_state() == vlc.State.Paused:
            current_pos = self.player.get_time()
            if current_pos > 0:
                self.pegasus_utils.save_video_position(self.video_name, current_pos)
                print(f"Posición guardada: {current_pos}ms")

    def _setup_save_events(self):
        self.root.bind("<space>", lambda e: self._save_position_after_action())
        self.progress.progress_slider.bind("<ButtonRelease-1>",
                                         lambda e: self._save_position())

        self.root.bind("<Left>", lambda e: self._save_position_after_action())
        self.root.bind("<Right>", lambda e: self._save_position_after_action())

    def _save_position_after_action(self, delay=500):
        self.root.after(delay, self._save_position)

    def toggle_play_pause(self, event=None):
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
        if hasattr(self, 'player') and self.player:
            player_state = self.player.get_state()
            if player_state != vlc.State.Ended:
                current_pos = self.player.get_time()
                if current_pos > 0:
                    self.pegasus_utils.save_video_position(self.video_name, current_pos)
                    print(f"Posición final guardada: {current_pos}ms")
            else:
                print("Video terminado, no se guarda posición")

            self.player.stop()
            self.is_playing = False

        if hasattr(self, 'root'):
            self.root.quit()
            self.root.destroy()

    def run(self):
        self.root.mainloop()

    def _rewind_10s(self, event=None):
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
        current_volume = self.player.audio_get_volume()
        if current_volume > 0:
            self.last_volume = current_volume
            self.player.audio_set_volume(0)
            self.controls.volume_slider.set(0)
        else:
            volume = getattr(self, 'last_volume', 50)
            self.player.audio_set_volume(volume)
            self.controls.volume_slider.set(volume)

        is_muted = (self.player.audio_get_volume() == 0)
        self.controls.is_muted = is_muted
        self.controls._update_mute_icon()

    def _on_volume_change(self, volume):
        volume = int(float(volume))
        self.player.audio_set_volume(volume)
        is_muted = (volume == 0)
        if is_muted != self.controls.is_muted:
            self._toggle_mute()

        if volume > 0:
            self.last_volume = volume

    def _on_mouse_motion(self, event):
        if self.is_fullscreen:
            if not self.controls_visible:
                self._show_controls()
            self._reset_hide_controls_timer()
            self.last_mouse_position = (event.x, event.y)
            self.mouse_idle_time = 0

    def _show_controls(self):
        if self.is_fullscreen and not self.controls_visible:
            self.control_frame.place(
                relx=0.5,
                rely=1.0,
                anchor="s",
                relwidth=0.6,
                y=-20,
                bordermode="outside"
            )
            self.control_frame.lift()
            self.controls_visible = True
            self._reset_hide_controls_timer()

    def _hide_controls(self):
        if self.is_fullscreen and self.controls_visible:
            self.control_frame.place_forget()
            self.controls_visible = False
        self.hide_controls_timer_id = None

    def _reset_hide_controls_timer(self):
        if hasattr(self, 'hide_controls_timer_id') and self.hide_controls_timer_id:
            self.root.after_cancel(self.hide_controls_timer_id)
        self.hide_controls_timer_id = self.root.after(1000, self._hide_controls)

    def _init_fullscreen_controls(self):
        self.controls_visible = True
        self.last_mouse_position = (0, 0)
        self.mouse_idle_time = 0
        self.root.after(100, self._check_mouse_activity)

    def _check_mouse_activity(self):
        if self.is_fullscreen:
            mouse_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
            mouse_y = self.root.winfo_pointery() - self.root.winfo_rooty()
            current_pos = (mouse_x, mouse_y)

            if current_pos != self.last_mouse_position:
                self.last_mouse_position = current_pos
                self.mouse_idle_time = 0

                if not self.controls_visible:
                    self._show_controls()
            else:
                self.mouse_idle_time += 100

                if self.mouse_idle_time > 3000 and self.controls_visible:
                    self._hide_controls()
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
