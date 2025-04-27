LOCALES = {
    "es": {
        "player_title": "PMDB Media Player - {}",
        "confirm_exit_title": "Confirmar salida",
        "confirm_exit_message": "¿Estás seguro que quieres salir del reproductor?\nSe guardará la posición actual.",
        "cancel_button": "Cancelar",
        "exit_button": "Salir",
        "loading": "Cargando...",
        "select_subtitle": "Seleccionar subtítulo",
        "disable_subtitles": "Desactivar subtítulos",
        "play": "Reproducir",
        "pause": "Pausar",
        "close": "Cerrar",
        "rewind": "⏪ -10s",
        "forward": "+10s ⏩",
        "volume": "🔊",
        "mute": "🔇",
        "fullscreen": "⛶",
        "no_fullscreen": "🔍",
        "subtitle_on": "Subtítulos: ON",
        "subtitle_off": "Subtítulos: OFF",
        "embedded_sub": "Subtítulos embebidos"
    },
    "en": {
        "player_title": "PMDB Media Player - {}",
        "confirm_exit_title": "Confirm exit",
        "confirm_exit_message": "Are you sure you want to exit the player?\nCurrent position will be saved.",
        "cancel_button": "Cancel",
        "exit_button": "Exit",
        "loading": "Loading...",
        "select_subtitle": "Select subtitle",
        "disable_subtitles": "Disable subtitles",
        "play": "Play",
        "pause": "Pause",
        "close": "Close",
        "rewind": "⏪ -10s",
        "forward": "+10s ⏩",
        "volume": "🔊",
        "mute": "🔇",
        "fullscreen": "⛶",
        "no_fullscreen": "🔍",
        "subtitle_on": "Subtitles: ON",
        "subtitle_off": "Subtitles: OFF",
        "embedded_sub": "Embedded subtitles"
    }
}

def get_locale(language):
    return LOCALES.get(language, LOCALES["es"])
