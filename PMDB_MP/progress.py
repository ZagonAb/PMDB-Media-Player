import tkinter as tk
import customtkinter as ctk

class ProgressBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master

        # Configuración de grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=9)
        self.grid_columnconfigure(2, weight=1)
        self.progress_slider = ctk.CTkSlider(
            self,
            from_=0,
            to=100,
            number_of_steps=10000,
            height=10,
            progress_color="#50555f",
            fg_color="#383838",
            button_color="#50555f",
            button_hover_color="#60656f",
            button_corner_radius=10,
            corner_radius=3
        )
        self.progress_slider.grid(row=0, column=1, sticky="ew", padx=(0, 0))
        self.progress_slider.set(0)
        self.grid_rowconfigure(0, weight=1, pad=3)
        self.time_label = ctk.CTkLabel(self, width=100, text="00:00:00 / 00:00:00")
        self.time_label.grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.seek_callback = None
        self.user_interacting = False
        self.progress_slider.bind("<Button-1>", self._on_click_progress)
        self.progress_slider.bind("<B1-Motion>", self._on_drag_progress)
        self.progress_slider.bind("<ButtonRelease-1>", self._on_release_progress)

    def set_seek_callback(self, callback):
        self.seek_callback = callback

    def _on_click_progress(self, event):
        self.user_interacting = True
        self._update_video_position()
        if self.seek_callback:
            position = self.progress_slider.get() / 100
            self.seek_callback(position)

    def _on_drag_progress(self, event):
        self._update_video_position()

    def _on_release_progress(self, event):
        self.user_interacting = False
        if self.seek_callback:
            position = self.progress_slider.get() / 100
            self.seek_callback(position)

    def _update_video_position(self):
        if self.seek_callback:
            position = self.progress_slider.get() / 100
            self.seek_callback(position)

    def update_progress(self, position, duration):
        if not self.user_interacting:
            if duration <= 0:
                self.time_label.configure(text="Cargando...")
                self.progress_slider.set(0)
            else:
                relative_pos = min((position / duration) * 100, 100)
                self.progress_slider.set(relative_pos)
                self.time_label.configure(text=self._format_time(position, duration))

    def _format_time(self, position, duration):
        def ms_to_hms(ms):
            seconds = int(ms / 1000)
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"

        return f"{ms_to_hms(position)} / {ms_to_hms(duration)}"
