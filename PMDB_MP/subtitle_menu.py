import customtkinter as ctk
from PMDB_MP.locales import get_locale

class SubtitleMenu:
    def __init__(self, root, parent_frame, embedded_subtitles, select_callback, locale=None):
        self.locale = locale or get_locale("es")
        """
        Constructor del menú de subtítulos.

        Args:
            root: Ventana principal de tkinter
            parent_frame: Frame contenedor de los controles
            embedded_subtitles: Lista de subtítulos embebidos
            select_callback: Función a llamar cuando se selecciona un subtítulo
        """
        self.root = root
        self.parent_frame = parent_frame
        self.embedded_subtitles = embedded_subtitles
        self.select_callback = select_callback
        self.subtitle_menu_frame = None
        self.click_outside_id = None

    def show(self, button):
        """Muestra el menú de subtítulos alineado con el botón dado"""
        # Cerrar si ya está abierto
        if self.subtitle_menu_frame and self.subtitle_menu_frame.winfo_exists():
            self._close_menu()
            return

        if not self.embedded_subtitles:
            return

        # Configuración de estilos
        bg_color = "#202227"
        btn_color = "#303338"
        text_color = "white"
        hover_color = "#404348"
        separator_color = "#50555f"

        # Obtener dimensiones de la ventana
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        # Obtener posición del botón de subtítulos para alinear el menú
        btn_x = button.winfo_rootx() - self.root.winfo_rootx()

        # Obtener posición del contenedor de controles
        container_top = self.parent_frame.winfo_rooty() - self.root.winfo_rooty()

        # Crear frame del menú
        self.subtitle_menu_frame = ctk.CTkFrame(
            self.root,
            fg_color=bg_color,
            border_width=1,
            border_color=separator_color,
            corner_radius=0
        )

        # Frame interno para contenido
        content_frame = ctk.CTkFrame(
            self.subtitle_menu_frame,
            fg_color=bg_color
        )
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Título
        title_label = ctk.CTkLabel(
            content_frame,
            text=self.locale["select_subtitle"],
            fg_color=bg_color,
            text_color=text_color,
            font=("Segoe UI", 12, "bold")
        )
        title_label.pack(padx=5, pady=(5, 3), fill='x')

        # Separador
        separator = ctk.CTkFrame(
            content_frame,
            height=1,
            fg_color=separator_color
        )
        separator.pack(fill='x', pady=2)

        # Función de cierre y selección
        def select_and_close(sub_id):
            self.select_callback(sub_id)
            self._close_menu()

        # Botón para desactivar subtítulos
        disable_btn = ctk.CTkButton(
            content_frame,
            text=self.locale["disable_subtitles"],
            fg_color=btn_color,
            text_color=text_color,
            hover_color=hover_color,
            command=lambda: select_and_close(-1)
        )
        disable_btn.pack(fill='x', padx=5, pady=2)

        # Separador
        separator2 = ctk.CTkFrame(
            content_frame,
            height=1,
            fg_color=separator_color
        )
        separator2.pack(fill='x', pady=2)

        # Calcular altura máxima disponible para scroll_frame
        max_scroll_height = container_top - 20
        scroll_height = min(max_scroll_height, 150)

        # Frame desplazable para tracks con altura adaptativa
        scroll_frame = ctk.CTkScrollableFrame(
            content_frame,
            fg_color=bg_color,
            height=scroll_height,
            width=230
        )
        scroll_frame.pack(fill='x', padx=5, pady=2)

        # Botones para cada track
        for sub in self.embedded_subtitles:
            btn_text = f"Track {sub['id']}: {sub['name']}"
            if len(btn_text) > 30:
                btn_text = btn_text[:27] + "..."

            sub_btn = ctk.CTkButton(
                scroll_frame,
                text=btn_text,
                fg_color=btn_color,
                text_color=text_color,
                hover_color=hover_color,
                anchor='w',
                command=lambda id=sub['id']: select_and_close(id)
            )
            sub_btn.pack(fill='x', padx=0, pady=2)

        # Calcular dimensiones y posición óptimas
        self.subtitle_menu_frame.update_idletasks()
        menu_width = self.subtitle_menu_frame.winfo_reqwidth()
        menu_height = self.subtitle_menu_frame.winfo_reqheight()

        # Ajustar posición horizontal
        menu_x = btn_x
        if menu_x + menu_width > window_width:
            menu_x = window_width - menu_width - 10
        if menu_x < 10:
            menu_x = 10

        # Posicionamiento vertical
        menu_y = container_top - menu_height

        # Ajustar si se sale por arriba
        if menu_y < 10:
            if container_top + 150 <= window_height:
                menu_y = container_top + 10
            else:
                menu_y = 10
                new_height = container_top - 20
                if new_height >= 100:
                    scroll_frame.configure(height=new_height - 70)

        # Posicionar el menú
        self.subtitle_menu_frame.place(
            x=menu_x,
            y=menu_y,
            anchor="nw"
        )

        # Cerrar al hacer clic fuera
        def on_click_outside(event):
            if (self.subtitle_menu_frame and
                self.subtitle_menu_frame.winfo_exists() and
                not self.subtitle_menu_frame.winfo_containing(event.x, event.y)):
                self._close_menu()

        # Guardar el ID del binding para poder eliminar después
        self.click_outside_id = self.root.bind("<Button-1>", on_click_outside)

        # Cerrar al perder el foco
        def on_focus_out(event):
            if self.subtitle_menu_frame and self.subtitle_menu_frame.winfo_exists():
                self._close_menu()

        self.subtitle_menu_frame.bind("<FocusOut>", on_focus_out)

        # Enfocar el menú
        self.subtitle_menu_frame.focus_set()

    def _close_menu(self):
        """Cierra el menú y limpia los recursos"""
        if self.subtitle_menu_frame and self.subtitle_menu_frame.winfo_exists():
            self.subtitle_menu_frame.destroy()

        if self.click_outside_id:
            self.root.unbind("<Button-1>", self.click_outside_id)
            self.click_outside_id = None
