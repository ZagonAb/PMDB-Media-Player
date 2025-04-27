import os
import sys
import json
import platform
from pathlib import Path

class PegasusUtils:
    def __init__(self):
        self.pegasus_config_dir = self._find_pegasus_config_dir()
        self.theme_dir = self._find_theme_dir()
        self.database_path = self._get_database_path()
        self._ensure_dirs_exist()
        self._ensure_database_exists()

    def _find_pegasus_config_dir(self):
        system = platform.system().lower()
        username = os.getenv('USER') or os.getenv('USERNAME')
        possible_paths = []

        if system == 'linux':
            possible_paths.extend([
                Path.home() / '.config' / 'pegasus-frontend',
                Path.home() / '.local' / 'share' / 'pegasus-frontend',
                Path('/etc/xdg/pegasus-frontend'),
                Path('/usr/local/share/pegasus-frontend'),
                Path('/usr/share/pegasus-frontend'),
                Path.home() / '.var' / 'app' / 'org.pegasus_frontend.Pegasus' / 'config' / 'pegasus-frontend'
            ])
        elif system == 'windows':
            appdata = os.getenv('LOCALAPPDATA') or (Path.home() / 'AppData' / 'Local')
            possible_paths.extend([
                Path(appdata) / 'pegasus-frontend',
                Path('C:') / 'ProgramData' / 'pegasus-frontend',
                Path.home() / 'scoop' / 'apps' / 'pegasus' / 'current' / 'config'
            ])
        elif system == 'darwin':  # macOS
            possible_paths.extend([
                Path.home() / 'Library' / 'Preferences' / 'pegasus-frontend',
                Path.home() / 'Library' / 'Application Support' / 'pegasus-frontend',
                Path('/Library') / 'Application Support' / 'pegasus-frontend'
            ])

        exe_dir = Path(sys.argv[0]).parent if hasattr(sys, 'argv') and len(sys.argv) > 0 else Path.cwd()
        possible_paths.extend([
            exe_dir / 'config',
            exe_dir
        ])

        for path in possible_paths:
            if path.exists() and path.is_dir():
                return path

        default_paths = {
            'linux': Path.home() / '.config' / 'pegasus-frontend',
            'windows': Path(os.getenv('LOCALAPPDATA')) / 'pegasus-frontend',
            'darwin': Path.home() / 'Library' / 'Preferences' / 'pegasus-frontend'
        }

        return default_paths.get(system, Path.cwd() / 'config')

    def _find_theme_dir(self):
        theme_locations = [
            self.pegasus_config_dir / 'themes',
            self.pegasus_config_dir.parent / 'themes',
            Path('/usr/share/pegasus-frontend/themes'),
            Path('/usr/local/share/pegasus-frontend/themes')
        ]

        for location in theme_locations:
            pmdb_theme = location / 'PMDB-Theme'
            if pmdb_theme.exists() and pmdb_theme.is_dir():
                return pmdb_theme

        default_location = self.pegasus_config_dir / 'themes' / 'PMDB-Theme'
        return default_location

    def _get_database_path(self):
        return self.theme_dir / 'database.json'

    def _ensure_dirs_exist(self):
        self.theme_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_database_exists(self):
        if not self.database_path.exists():
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=4)

    def save_video_position(self, video_name, position_ms):
        try:
            self._ensure_dirs_exist()

            data = {}
            if self.database_path.exists():
                try:
                    with open(self.database_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except json.JSONDecodeError:
                    data = {}

            if not isinstance(data, dict):
                data = {}

            data[video_name] = {
                "x-lastPosition": position_ms
            }

            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error saving video position: {str(e)}")
            return False

    def get_video_position(self, video_name):
        try:
            if not self.database_path.exists():
                return 0

            with open(self.database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if video_name in data:
                position = data[video_name].get("x-lastPosition", 0)
                return max(0, int(position)) if str(position).isdigit() else 0
            return 0
        except Exception as e:
            print(f"Error al leer posición guardada: {str(e)}")
            return 0

    def remove_video_position(self, video_name):
        try:
            if not self.database_path.exists():
                return True

            with open(self.database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if video_name in data:
                del data[video_name]
                with open(self.database_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
            return False
        except Exception as e:
            print(f"Error removing video position: {str(e)}")
            return False

    def get_system_info(self):
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "pegasus_config": str(self.pegasus_config_dir),
            "theme_dir": str(self.theme_dir),
            "database_path": str(self.database_path)
        }
