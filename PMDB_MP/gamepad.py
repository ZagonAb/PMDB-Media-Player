import os
import sys
import threading
import time
import traceback
import customtkinter as ctk
import pygame

class GamepadController:

    BUTTON_MAP = {
        0: 'primary',
        1: 'secondary',
        2: 'tertiary',
        3: 'quaternary',
    }

    HAT_MAP = {
        (0, 1): 'vol_up',
        (0, -1): 'vol_down',
        (-1, 0): 'rewind_10s',
        (1, 0): 'forward_10s',
        (0, 0): None,
    }

    ACTION_MAP = {
        'primary': 'play_pause',
        'secondary': 'toggle_subtitle',
        'tertiary': 'fullscreen',
        'quaternary': 'close',
    }

    def __init__(self, player):
        pygame.init()
        pygame.joystick.init()
        self.player = player
        self.joystick = None
        self.running = False
        self.active = False
        self.thread = None
        self.last_event_time = time.time()
        self.debug_mode = True
        self.current_device_name = None
        self.last_notification_time = 0
        self.notification_cooldown = 5.0
        self.notification = None
        self.notification_id = None
        self.notification_timeout = 3000
        self.axis_deadzone = 0.5
        self.last_axis_values = {}
        self.button_repeat_delay = 0.2
        self.last_hat_value = (0, 0)

        self.notification_position = "bottom_left"
        self.notification_duration = 1000

    def debug_log(self, message):
        if self.debug_mode:
            print(f"🕹️ [Gamepad] {message}")

    def _show_notification(self, message, is_success=True):
        self._hide_notification()

        fg_color = "#2AA876" if is_success else "#E74C3C"
        text_color = "white"

        self.notification = ctk.CTkFrame(
            self.player.root,
            corner_radius=0,
            border_width=2,
            fg_color=fg_color,
            border_color="#FFFFFF"
        )

        self.notification_label = ctk.CTkLabel(
            self.notification,
            text=message,
            text_color=text_color,
            font=("Arial", 12, "bold")
        )
        self.notification_label.pack(padx=20, pady=10)

        self.notification.place(
            relx=1.0,
            rely=1.0,
            anchor="se",
            x=-10,
            y=-80
        )

        self.notification_id = self.player.root.after(
            self.notification_timeout,
            self._hide_notification
        )

    def _update_notification(self, message, is_success=True):
        if hasattr(self, 'notification') and self.notification and self.notification.winfo_exists():
            fg_color = "#2AA876" if is_success else "#E74C3C"
            self.notification.configure(fg_color=fg_color)
            self.notification_label.configure(text=message)

            if hasattr(self, 'notification_id') and self.notification_id:
                self.player.root.after_cancel(self.notification_id)
            self.notification_id = self.player.root.after(
                self.notification_timeout,
                self._hide_notification
            )
        else:
            self._show_notification(message, is_success)

    def _hide_notification(self):
        if self.notification:
            self.notification.destroy()
            self.notification = None
        if self.notification_id:
            self.player.root.after_cancel(self.notification_id)
            self.notification_id = None

    def _get_action_handler(self, action_name):
        handlers = {
            'play_pause': self._handle_play_pause,
            'toggle_subtitle': self._cycle_subtitles,
            'fullscreen': self._handle_fullscreen,
            'close': self.player.close_player,
            'rewind_10s': self._handle_rewind,
            'forward_10s': self._handle_forward,
            'vol_up': self._handle_volume_up,
            'vol_down': self._handle_volume_down
        }
        return handlers.get(action_name)
        self.debug_log(f"Handler para '{action_name}': {handler}")
        return handler

    def _handle_play_pause(self):
        self.player.toggle_play_pause()
        state = "PAUSADO" if not self.player.is_playing else "REPRODUCIENDO"
        self._show_notification(f"Reproducción: {state}")

    def _handle_fullscreen(self):
        self.player._toggle_fullscreen()
        state = "Pantalla Completa" if self.player.is_fullscreen else "Ventana"
        self._show_notification(f"Modo: {state}")

    def _handle_volume_up(self):
        current_vol = self.player.player.audio_get_volume()
        new_vol = min(100, current_vol + 5)
        self.player._on_volume_change(new_vol)
        self.player.controls.volume_slider.set(new_vol)
        self._update_notification(f"Volumen: {new_vol}%")

    def _handle_volume_down(self):
        current_vol = self.player.player.audio_get_volume()
        new_vol = max(0, current_vol - 5)
        self.player._on_volume_change(new_vol)
        self.player.controls.volume_slider.set(new_vol)
        self._update_notification(f"Volumen: {new_vol}%")

    def _handle_rewind(self):
        self._seek_relative(-10000)
        current_time = self.player.player.get_time() / 1000
        mins, secs = divmod(int(current_time), 60)
        self._update_notification(f"Retrocedido a {mins:02d}:{secs:02d}")

    def _handle_forward(self):
        self._seek_relative(10000)
        current_time = self.player.player.get_time() / 1000
        mins, secs = divmod(int(current_time), 60)
        self._update_notification(f"Adelantado a {mins:02d}:{secs:02d}")

    def _seek_relative(self, ms):
        try:
            current_time = self.player.player.get_time()
            new_time = max(0, current_time + ms)
            self.player.player.set_time(new_time)
            self.debug_log(f"Navegación: {current_time}ms → {new_time}ms")
        except Exception as e:
            self.debug_log(f"Error en navegación: {str(e)}")

    def _cycle_subtitles(self):
        try:
            has_external_sub = hasattr(self.player, 'subtitle_path') and self.player.subtitle_path

            if not hasattr(self.player, 'embedded_subtitles'):
                self.player._detect_embedded_subtitles()

            has_embedded_subs = bool(getattr(self.player, 'embedded_subtitles', []))

            if not has_external_sub and not has_embedded_subs:
                self.debug_log("No hay subtítulos disponibles")
                self.player.root.after(0, lambda: self._show_notification("No hay subtítulos disponibles", False))
                return

            current_spu = self.player.player.video_get_spu()
            message = "Subtítulos: "

            if current_spu == -1:
                if has_external_sub:
                    try:
                        self.player.player.video_set_subtitle_file(self.player.subtitle_path)
                        self.player.player.video_set_spu(0)
                        self.player.subtitle_enabled = True
                        self.player.current_embedded_sub = -1
                        message += "Externos ACTIVADOS"
                    except Exception as e:
                        message += "Error activando externos"
                        self.debug_log(f"Error cargando subtítulo externo: {e}")
                elif has_embedded_subs:
                    first_sub = self.player.embedded_subtitles[0]
                    try:
                        self.player.player.video_set_spu(first_sub["id"])
                        self.player.subtitle_enabled = True
                        self.player.current_embedded_sub = first_sub["id"]
                        sub_name = first_sub.get('name', first_sub.get('language', f'Pista {first_sub["id"]}'))
                        message += f"{sub_name}"
                    except Exception as e:
                        message += "Error activando incrustados"
                        self.debug_log(f"Error activando subtítulo incrustado: {e}")

            elif current_spu == 0 and has_external_sub and self.player.subtitle_enabled:
                if has_embedded_subs:
                    first_sub = self.player.embedded_subtitles[0]
                    try:
                        self.player.player.video_set_spu(first_sub["id"])
                        self.player.current_embedded_sub = first_sub["id"]
                        sub_name = first_sub.get('name', first_sub.get('language', f'Pista {first_sub["id"]}'))
                        message += f"{sub_name}"
                    except Exception as e:
                        message += "Error cambiando a incrustados"
                        self.debug_log(f"Error cambiando a subtítulo incrustado: {e}")
                else:
                    self.player.player.video_set_spu(-1)
                    self.player.subtitle_enabled = False
                    message += "DESACTIVADOS"

            elif has_embedded_subs and current_spu > 0:
                current_index = next(
                    (i for i, sub in enumerate(self.player.embedded_subtitles)
                    if sub['id'] == current_spu),
                    -1
                )

                if current_index == -1 or current_index == len(self.player.embedded_subtitles) - 1:
                    self.player.player.video_set_spu(-1)
                    self.player.subtitle_enabled = False
                    self.player.current_embedded_sub = -1
                    message += "DESACTIVADOS"
                else:
                    next_index = current_index + 1
                    next_sub = self.player.embedded_subtitles[next_index]
                    try:
                        self.player.player.video_set_spu(next_sub['id'])
                        self.player.current_embedded_sub = next_sub['id']
                        sub_name = next_sub.get('name', next_sub.get('language', f'Pista {next_sub["id"]}'))
                        message += f"{sub_name}"
                    except Exception as e:
                        message += "Error cambiando pista"
                        self.debug_log(f"Error cambiando a siguiente subtítulo: {e}")
            else:
                self.player.player.video_set_spu(-1)
                self.player.subtitle_enabled = False
                message += "DESACTIVADOS"

            is_success = not message.endswith("Error") and not message.endswith("DESACTIVADOS")
            self.player.root.after(0, lambda: self.player.controls.set_subtitle_state(
                has_external_sub or has_embedded_subs,
                self.player.subtitle_enabled
            ))
            self.debug_log(message)
            self.player.root.after(0, lambda: self._show_notification(message, is_success))

        except Exception as e:
            error_msg = f"Error cambiando subtítulos: {str(e)}"
            self.debug_log(error_msg)
            traceback.print_exc()
            self.player.root.after(0, lambda: self._show_notification(error_msg, False))

    def _adjust_volume(self, delta):
        try:
            current = self.player.player.audio_get_volume()
            new_vol = max(0, min(100, current + delta))
            self.debug_log(f"Ajustando volumen: {current} → {new_vol}")
            self.player._on_volume_change(new_vol)
            self.player.controls.volume_slider.set(new_vol)
        except Exception as e:
            self.debug_log(f"Error ajustando volumen: {str(e)}")
            traceback.print_exc()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        self.debug_log("Sistema de gamepad iniciado (pygame)")
        return True

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        pygame.quit()
        self._hide_notification()
        self.debug_log("Sistema de gamepad detenido")

    def _listen(self):
        while self.running:
            if not self.active:
                pygame.joystick.quit()
                pygame.joystick.init()
                joystick_count = pygame.joystick.get_count()

                if joystick_count > 0:
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    self.current_device_name = self.joystick.get_name()
                    self.active = True
                    self.debug_log(f"Gamepad conectado: {self.current_device_name}")
                    self.debug_log(f"Número de hats: {self.joystick.get_numhats()}")
                    self.debug_log(f"Número de botones: {self.joystick.get_numbuttons()}")
                    self.player.root.after(0, lambda: self._show_notification(f"Gamepad conectado: {self.current_device_name}", True))
                else:
                    time.sleep(2)
                    continue

            for event in pygame.event.get():
                if not self.running:
                    break

                self._handle_event(event)

            time.sleep(0.01)

    def _handle_event(self, event):
        try:
            current_time = time.time()

            if event.type == pygame.JOYBUTTONDOWN:
                if current_time - self.last_event_time < self.button_repeat_delay:
                    return

                if event.button in self.BUTTON_MAP:
                    button_function = self.BUTTON_MAP[event.button]
                    action_name = self.ACTION_MAP.get(button_function)
                    if action_name:
                        self.debug_log(f"Botón {event.button} → {action_name}")
                        self.player.root.after(0, self._get_action_handler(action_name))
                        self.last_event_time = current_time

            elif event.type == pygame.JOYHATMOTION:
                self.debug_log(f"HAT evento detectado: {event.value}")

                if (event.value != (0, 0) and
                    event.value != self.last_hat_value and
                    current_time - self.last_event_time > self.button_repeat_delay):

                    self.debug_log(f"Procesando HAT: {event.value}")

                    if event.value in self.HAT_MAP:
                        action_name = self.HAT_MAP[event.value]
                        self.debug_log(f"Action_name encontrado: {action_name}")

                        if action_name:
                            action = self._get_action_handler(action_name)
                            self.debug_log(f"Action handler: {action}")

                            if action:
                                self.debug_log(f"Ejecutando: Cruceta {event.value} → {action_name}")
                                self.player.root.after(0, action)
                                self.last_event_time = current_time
                            else:
                                self.debug_log(f"ERROR: No se encontró handler para {action_name}")
                    else:
                        self.debug_log(f"ERROR: Valor HAT {event.value} no está en HAT_MAP")

                self.last_hat_value = event.value
            elif event.type in [pygame.JOYAXISMOTION, pygame.JOYBUTTONUP]:
                pass

        except Exception as e:
            self.debug_log(f"Error procesando evento: {str(e)}")
            traceback.print_exc()

    def _get_axis_action(self, axis_function, direction):
        axis_actions = {
            'stick_left_x': {'negative': 'rewind_10s', 'positive': 'forward_10s'},
            'stick_left_y': {'negative': 'vol_up', 'positive': 'vol_down'},
            'stick_right_x': {'negative': 'rewind_10s', 'positive': 'forward_10s'},
            'stick_right_y': {'negative': 'vol_up', 'positive': 'vol_down'},
        }
        return axis_actions.get(axis_function, {}).get(direction)
