import tkinter as tk
import customtkinter as ctk

class ProgressBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master  # Guardamos referencia al padre

        # Configurar columnas para distribución
        self.grid_columnconfigure(0, weight=1)  # espacio izquierdo
        self.grid_columnconfigure(1, weight=9)  # barra de progreso
        self.grid_columnconfigure(2, weight=1)  # contador

        # Barra de progreso con eventos de clic
        self.progress_bar = ctk.CTkProgressBar(self, height=10)
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=(0, 0))
        self.progress_bar.set(0)  # inicio en 0%

        # Bind eventos para clic en la barra
        self.progress_bar.bind("<Button-1>", self._on_click_progress)
        self.progress_bar.bind("<B1-Motion>", self._on_click_progress)  # Para arrastrar

        # Contador con texto por defecto
        self.time_label = ctk.CTkLabel(self, width=100, text="00:00:00 / 00:00:00")
        self.time_label.grid(row=0, column=2, sticky="w", padx=(10, 0))

        # Callback para actualizar posición (se asignará desde player.py)
        self.seek_callback = None

    def set_seek_callback(self, callback):
        """Asigna la función para buscar en el video"""
        self.seek_callback = callback

    def _on_click_progress(self, event):
        """Maneja clics en la barra de progreso"""
        if self.seek_callback:
            # Calcula la posición relativa (0-1) basada en donde se hizo clic
            progress_width = self.progress_bar.winfo_width()
            click_position = min(max(event.x / progress_width, 0.0), 1.0)  # Paréntesis corregido
            self.seek_callback(click_position)

    def update_progress(self, position, duration):
        """Actualiza la barra y el contador"""
        if duration <= 0:
            self.time_label.configure(text="Cargando...")
            self.progress_bar.set(0)
        else:
            relative_pos = min(position / duration, 1.0)
            self.progress_bar.set(relative_pos)
            self.time_label.configure(text=self._format_time(position, duration))

    def _format_time(self, position, duration):
        """Convierte milisegundos a HH:MM:SS"""
        def ms_to_hms(ms):
            seconds = int(ms / 1000)
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"

        return f"{ms_to_hms(position)} / {ms_to_hms(duration)}"
