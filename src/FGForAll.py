import os
import json
import shutil
import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QComboBox, QLineEdit, QPushButton, 
    QLabel, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class Operation(Enum):
    INSTALL = 1
    ROLLBACK = 2


class Game:
    def __init__(self, name: str, main_location: str, dll_location: Optional[str] = None):
        self.name = name
        self.main_location = main_location
        self.dll_location = dll_location


class GameLocatorThread(QThread):
    games_found = pyqtSignal(list)
    
    def run(self):
        game_locator = GameLocatorService()
        games = game_locator.locate_games()
        self.games_found.emit(games)


class GameLocatorService:
    def __init__(self):
        self.specific_steam_path_c = "C:/Program Files (x86)/Steam/steamapps/common"
        self.steam_base_path = "SteamLibrary/steamapps/common"
        self.ignore_paths = ["Steamworks Shared"]
        self.epic_games_database_path = Path(os.environ.get("PROGRAMDATA", "")) / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests"
        
    def locate_games(self) -> List[Game]:
        steam_games = []
        
        # Handle C drive specifically
        steam_path_c = Path(self.specific_steam_path_c)
        if steam_path_c.exists():
            self.search_games(steam_path_c, steam_games)
            
        # Handle other drives
        for drive in self.get_available_drives():
            steam_path = Path(f"{drive}/{self.steam_base_path}")
            if steam_path.exists():
                self.search_games(steam_path, steam_games)
                
        epic_games = self.read_epic_games_database(self.epic_games_database_path)
        
        # Filter games to only include those with DLL locations
        all_games = steam_games + epic_games
        return [game for game in all_games if game.dll_location]
    
    def search_games(self, path: Path, games: List[Game]):
        try:
            for directory in path.iterdir():
                if directory.is_dir() and directory.name not in self.ignore_paths:
                    game_name = directory.name
                    dll_location = self.find_dll_file(directory)
                    games.append(Game(game_name, str(directory.absolute()), dll_location))
        except Exception as e:
            print(f"Error searching games in {path}: {e}")
            
    def find_dll_file(self, directory: Path) -> Optional[str]:
        try:
            for file_path in directory.glob("**/*"):
                if file_path.is_file() and file_path.name.lower() == "nvngx_dlss.dll":
                    return str(file_path.parent)
        except Exception as e:
            print(f"Error finding DLL file in {directory}: {e}")
        return None
    
    def read_epic_games_database(self, database_path: Path) -> List[Game]:
        games = []
        if not database_path.exists() or not database_path.is_dir():
            return games
            
        try:
            for file_path in database_path.iterdir():
                if not file_path.is_dir():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            game_data = json.load(f)
                            install_location = game_data.get("InstallLocation", "")
                            if install_location:
                                dll_location = self.find_dll_file(Path(install_location))
                                games.append(Game(
                                    game_data.get("DisplayName", "Unknown Game"),
                                    install_location,
                                    dll_location
                                ))
                    except Exception as e:
                        print(f"Error reading Epic Games manifest {file_path}: {e}")
        except Exception as e:
            print(f"Error reading Epic Games database: {e}")
            
        return games
    
    def get_available_drives(self) -> List[str]:
        try:
            if sys.platform == "win32":
                import string
                drives = []
                for letter in string.ascii_uppercase:
                    if os.path.exists(f"{letter}:"):
                        drives.append(f"{letter}:")
                return drives
            else:
                # On non-Windows systems, return only common paths
                return ["C:", "D:", "E:", "F:"]
        except Exception as e:
            print(f"Error getting available drives: {e}")
            return ["C:", "D:", "E:", "F:"]


class FileService:
    FSR_FG_FILE = "dlssg_to_fsr3_amd_is_better.dll"
    DLSS_FG_PATH = "dlss-fg"
    READMES = ["READ ME.txt", "README.txt"]
    
    def perform_file_operations(self, game_folder_path: str, option: str, operation: Operation) -> str:
        if not game_folder_path or not Path(game_folder_path).exists():
            return "Game folder is not valid!"
            
        bak_folder_path = Path(game_folder_path) / "bak"
        sub_folder_path = Path(self.DLSS_FG_PATH) / option
        
        if not sub_folder_path.exists() or not any(sub_folder_path.iterdir()):
            return "Please add the dlss-fg folder!"
            
        if operation == Operation.ROLLBACK:
            if not bak_folder_path.exists():
                return "No backup folder found. Nothing to rollback."
                
            for file in sub_folder_path.iterdir():
                if file.name in self.READMES:
                    continue
                    
                dest_file_path = Path(game_folder_path) / file.name
                bak_file_path = bak_folder_path / file.name
                
                if file.name == self.FSR_FG_FILE:
                    dest_file_path.unlink(missing_ok=True)
                    
                if bak_file_path.exists():
                    if dest_file_path.exists():
                        dest_file_path.unlink()
                    shutil.move(str(bak_file_path), str(dest_file_path))
                    
            # Remove backup folder if empty
            if not any(bak_folder_path.iterdir()):
                shutil.rmtree(str(bak_folder_path))
                
            return "Files have been reverted to the original location, and the bak folder has been removed."
            
        elif operation == Operation.INSTALL:
            if bak_folder_path.exists():
                return "Another mod has already been installed, try rollback first."
                
            bak_folder_path.mkdir(exist_ok=True)
            
            for file in sub_folder_path.iterdir():
                if file.name in self.READMES:
                    continue
                    
                dest_file_path = Path(game_folder_path) / file.name
                bak_file_path = bak_folder_path / file.name
                
                if dest_file_path.exists():
                    shutil.copy2(str(dest_file_path), str(bak_file_path))
                    
                shutil.copy2(str(file), str(dest_file_path))
                
            return f"Files have been copied from {option} to the game folder."
            
        else:
            return "Unknown Operation"


class FileOperationUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.games = []
        self.init_ui()
        self.load_games()
        
    def init_ui(self):
        self.setWindowTitle("DLSS FG")
        self.setGeometry(100, 100, 600, 400)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Game selection section
        game_section_layout = QVBoxLayout()
        game_section_layout.addWidget(QLabel("Select a game:"))
        
        self.games_combo_box = QComboBox()
        self.games_combo_box.addItem("Select a game")
        self.games_combo_box.currentIndexChanged.connect(self.on_game_selected)
        game_section_layout.addWidget(self.games_combo_box)
        
        game_section_layout.addWidget(QLabel("Or select any file from the game folder:"))
        
        path_layout = QHBoxLayout()
        self.game_folder_path_field = QLineEdit()
        path_layout.addWidget(self.game_folder_path_field)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.on_browse_clicked)
        path_layout.addWidget(browse_button)
        
        game_section_layout.addLayout(path_layout)
        main_layout.addLayout(game_section_layout)
        
        # Options section
        options_layout = QVBoxLayout()
        options_layout.addWidget(QLabel("Select mod option:"))
        
        self.option_combo_box = QComboBox()
        self.option_combo_box.addItems([
            "dll_version", "dll_winhttp", "dll_dbghelp", 
            "plugin_asi_loader", "plugin_red4ext"
        ])
        options_layout.addWidget(self.option_combo_box)
        main_layout.addLayout(options_layout)
        
        # Button section
        button_layout = QHBoxLayout()
        self.install_button = QPushButton("Install")
        self.install_button.clicked.connect(self.on_install_clicked)
        button_layout.addWidget(self.install_button)
        
        self.rollback_button = QPushButton("Rollback")
        self.rollback_button.clicked.connect(self.on_rollback_clicked)
        button_layout.addWidget(self.rollback_button)
        main_layout.addLayout(button_layout)
        
        # Result section
        result_layout = QVBoxLayout()
        result_layout.addWidget(QLabel("Result:"))
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        result_layout.addWidget(self.result_label)
        main_layout.addLayout(result_layout)
        
        # Set the main layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
    def load_games(self):
        self.games_combo_box.clear()
        self.games_combo_box.addItem("Select a game")
        
        # Use a separate thread to locate games
        self.game_locator_thread = GameLocatorThread()
        self.game_locator_thread.games_found.connect(self.on_games_loaded)
        self.game_locator_thread.start()
        
    def on_games_loaded(self, games):
        self.games = games
        for game in games:
            self.games_combo_box.addItem(game.name)
            
    def on_game_selected(self, index):
        if index <= 0 or index > len(self.games):
            return
            
        selected_game = self.games[index - 1]
        self.game_folder_path_field.setText(selected_game.dll_location)
        
    def on_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select any file from the game folder")
        if file_path:
            # Set the parent directory
            self.game_folder_path_field.setText(str(Path(file_path).parent))
            # Reset game selection
            self.games_combo_box.setCurrentIndex(0)
            
    def on_install_clicked(self):
        game_folder_path = self.game_folder_path_field.text()
        option = self.option_combo_box.currentText()
        file_service = FileService()
        result = file_service.perform_file_operations(game_folder_path, option, Operation.INSTALL)
        self.result_label.setText(result)
        
    def on_rollback_clicked(self):
        game_folder_path = self.game_folder_path_field.text()
        option = self.option_combo_box.currentText()
        file_service = FileService()
        result = file_service.perform_file_operations(game_folder_path, option, Operation.ROLLBACK)
        self.result_label.setText(result)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileOperationUI()
    window.show()
    sys.exit(app.exec())
