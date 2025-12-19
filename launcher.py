#!/usr/bin/env python3
"""
Illama Launcher - Professional Minecraft Mod Sync Launcher
Synchronise automatiquement les mods depuis Google Drive et lance Minecraft
"""

import os
import sys
import json
import hashlib
import threading
import subprocess
import webbrowser
import base64
import io
import stat
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import urllib.request
import urllib.parse
import urllib.error
import re
import ssl
import time

# === VERSION DU LAUNCHER ===
LAUNCHER_VERSION = "1.0.0"
MIN_REQUIRED_VERSION = "1.0.0"  # Version minimale requise (force la mise à jour si inférieure)

def increment_version(version: str) -> str:
    """Incrémente la version automatiquement
    Format: X.Y.Z
    - Z incrémente jusqu'à 9, puis Y incrémente et Z revient à 0
    - Y incrémente jusqu'à 9, puis X incrémente et Y revient à 0
    Exemples: 1.0.2 -> 1.0.3, 1.0.9 -> 1.1.0, 1.9.9 -> 2.0.0
    """
    try:
        parts = version.split('.')
        if len(parts) != 3:
            return version
        
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])
        
        # Incrémenter le patch
        patch += 1
        
        # Si patch > 9, incrémenter minor et remettre patch à 0
        if patch > 9:
            patch = 0
            minor += 1
            
            # Si minor > 9, incrémenter major et remettre minor à 0
            if minor > 9:
                minor = 0
                major += 1
        
        return f"{major}.{minor}.{patch}"
    except:
        return version

# === CONFIGURATION GITHUB (Mises à jour) ===
GITHUB_REPO_OWNER = "illama"  # Remplace par ton username GitHub
GITHUB_REPO_NAME = "illama_minecraftlauncher"  # Remplace par le nom de ton repo
GITHUB_TOKEN = ""  # Chargée depuis secrets.json (voir load_secrets())
GITHUB_RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"

# === CONFIGURATION DU SERVEUR ===
SERVER_ADDRESS = "illama.duckdns.org"
SERVER_NAME = "Illama Server"

# === CONFIGURATION GOOGLE DRIVE ===
# ⚠️ SÉCURITÉ : Les clés API sont chargées depuis un fichier externe
# Ne mets JAMAIS tes vraies clés ici - elles seront visibles dans l'exécutable !
DRIVE_API_KEY = ""  # Chargée depuis secrets.json (voir SECRETS_TEMPLATE.json)
DRIVE_FOLDER_ID = "1O7Yo0AaC2pJ68bMEktbPMmz9OHhdCP_2"

# === MODE ADMIN ===
ADMIN_PASSWORD = ""  # Chargée depuis secrets.json (voir load_secrets())

# === MICROSOFT AZURE APP ===
MS_CLIENT_ID = "6a3728d6-27a3-4180-99bb-479895b8f88e"

# === COULEURS THEME MINECRAFT MODERNE ===
COLORS = {
    # Arrière-plans (dégradé sombre moderne)
    'bg_dark': '#0d1117',      # Fond principal très sombre
    'bg_medium': '#161b22',    # Cartes et sections
    'bg_light': '#21262d',     # Surfaces élevées
    'bg_hover': '#30363d',     # Survol
    
    # Accents (vert Minecraft moderne)
    'accent_green': '#3fb950',      # Vert principal brillant
    'accent_green_hover': '#56d364', # Vert au survol
    'accent_green_pressed': '#2ea043', # Vert pressé
    'accent_green_glow': '#238636',   # Lueur verte
    
    # Couleurs d'action
    'accent_red': '#f85149',         # Rouge moderne
    'accent_red_hover': '#ff6b6b',
    'accent_blue': '#58a6ff',        # Bleu moderne
    'accent_gold': '#d29922',        # Or moderne
    'accent_gold_hover': '#e3b341',
    
    # Texte
    'text_white': '#f0f6fc',         # Texte principal
    'text_gray': '#8b949e',          # Texte secondaire
    'text_muted': '#6e7681',         # Texte atténué
    
    # Minecraft spécifique
    'minecraft_green': '#3fb950',
    'minecraft_dirt': '#8B7355',
    'minecraft_grass': '#7CBA5F',
    'minecraft_stone': '#8B8B8B',
    
    # Bordures et séparateurs
    'border': '#30363d',
    'border_light': '#21262d',
}

# Versions Minecraft et Forge supportées
MINECRAFT_FORGE_VERSIONS = {
    "1.20.1": {
        "recommended": "47.4.1",
        "versions": ["47.4.1", "47.4.0", "47.3.12", "47.3.11", "47.3.10", "47.3.9", "47.3.8",
                     "47.3.7", "47.3.6", "47.3.5", "47.3.4", "47.3.3", "47.3.2", "47.3.1",
                     "47.3.0", "47.2.32", "47.2.31", "47.2.30", "47.2.29", "47.2.28"]
    },
    "1.21.4": {"recommended": "54.1.0", "versions": ["54.1.0", "54.0.34", "54.0.33", "54.0.32"]},
    "1.21.1": {"recommended": "52.0.38", "versions": ["52.0.38", "52.0.37", "52.0.36", "52.0.35"]},
    "1.20.4": {"recommended": "49.1.13", "versions": ["49.1.13", "49.1.12", "49.1.11", "49.1.10"]},
    "1.20.2": {"recommended": "48.1.0", "versions": ["48.1.0", "48.0.49", "48.0.48", "48.0.47"]},
    "1.19.4": {"recommended": "45.3.0", "versions": ["45.3.0", "45.2.11", "45.2.10", "45.2.9"]},
    "1.19.2": {"recommended": "43.4.4", "versions": ["43.4.4", "43.4.3", "43.4.2", "43.4.1"]},
    "1.18.2": {"recommended": "40.2.21", "versions": ["40.2.21", "40.2.20", "40.2.19", "40.2.18"]},
    "1.16.5": {"recommended": "36.2.42", "versions": ["36.2.42", "36.2.41", "36.2.40", "36.2.39"]},
    "1.12.2": {"recommended": "14.23.5.2860", "versions": ["14.23.5.2860", "14.23.5.2859"]}
}

def get_sorted_mc_versions():
    versions = list(MINECRAFT_FORGE_VERSIONS.keys())
    if "1.20.1" in versions:
        versions.remove("1.20.1")
        versions.insert(0, "1.20.1")
    return versions

def get_screen_resolution():
    """Détecte la résolution de l'écran principal"""
    try:
        if sys.platform == 'win32':
            import ctypes
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
            return width, height
        else:
            # Linux/Mac - fallback
            return 1920, 1080
    except:
        return 1920, 1080  # Fallback par défaut

# Fichiers de config
CONFIG_FILE = Path.home() / ".illama_launcher_config.json"
AUTH_FILE = Path.home() / ".illama_launcher_auth.json"
# Fichier de secrets (doit être dans le même dossier que launcher.py, NON inclus dans l'exe)
SECRETS_FILE = Path(__file__).parent / "secrets.json"

def load_secrets():
    """Charge les secrets depuis un fichier externe (sécurisé, non inclus dans l'exe)"""
    secrets = {
        "drive_api_key": "",
        "github_token": "",
        "admin_password": ""
    }
    
    # Essayer de charger depuis secrets.json
    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                secrets.update(loaded)
        except Exception as e:
            print(f"[WARNING] Impossible de charger secrets.json: {e}")
    else:
        # Si le fichier n'existe pas, créer un template
        try:
            template = {
                "drive_api_key": "COLLE_TA_CLE_API_GOOGLE_DRIVE_ICI",
                "github_token": "COLLE_TON_TOKEN_GITHUB_ICI_OU_LAISSE_VIDE",
                "admin_password": "COLLE_TON_MOT_DE_PASSE_ADMIN_ICI"
            }
            with open(SECRETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2)
            print(f"[INFO] Fichier secrets.json cree. Complete-le avec tes cles API.")
        except Exception as e:
            print(f"[WARNING] Impossible de creer secrets.json: {e}")
    
    return secrets

# Charger les secrets au démarrage
SECRETS = load_secrets()

# Utiliser les secrets chargés (ou les valeurs par défaut si vide)
_DRIVE_API_KEY_DEFAULT = ""
_GITHUB_TOKEN_DEFAULT = ""
_ADMIN_PASSWORD_DEFAULT = ""

# Charger la clé API depuis secrets.json
DRIVE_API_KEY = SECRETS.get("drive_api_key", "") or ""
# Si la clé est vide, afficher un avertissement
if not DRIVE_API_KEY:
    print("[WARNING] Clé API Google Drive non trouvée dans secrets.json")
    print("[WARNING] Le launcher utilisera le mode scraping (moins fiable)")
GITHUB_TOKEN = SECRETS.get("github_token", _GITHUB_TOKEN_DEFAULT) if SECRETS.get("github_token") else _GITHUB_TOKEN_DEFAULT
ADMIN_PASSWORD = SECRETS.get("admin_password", _ADMIN_PASSWORD_DEFAULT) if SECRETS.get("admin_password") else _ADMIN_PASSWORD_DEFAULT

# Détecter la résolution de l'écran pour les valeurs par défaut
SCREEN_WIDTH, SCREEN_HEIGHT = get_screen_resolution()

DEFAULT_CONFIG = {
    "google_drive_folder_id": DRIVE_FOLDER_ID,
    "minecraft_dir": "",
    "mods_subfolder": "mods",
    "launcher_type": "prism",
    "api_key": DRIVE_API_KEY,
    "last_sync": "",
    "minecraft_version": "1.20.1",
    "forge_version": "47.4.1",
    "setup_completed": False,
    "ms_access_token": "",
    "ms_refresh_token": "",
    "mc_access_token": "",
    "mc_uuid": "",
    "mc_username": "",
    "auth_expires": 0,
    "ram_min": 2048,
    "ram_max": 8500,
    "window_width": SCREEN_WIDTH,
    "window_height": SCREEN_HEIGHT,
    "fullscreen": False,
    "borderless": True,  # Activé par défaut
    "java_path": "java",
    "jvm_args": "",
    "show_console": False,
    "auto_connect": True,
    "keep_launcher_open": False,
    "is_admin": False,
    "prism_instance_created": False,
    "minimize_to_tray": True,
    "download_workers": 5,
    "download_retries": 3,
    "download_timeout": 180,
    "download_chunk_size": 32768,
    "update_check_interval": 60,  # Intervalle de vérification des mises à jour (en minutes)
    "minecraft_options": {}  # Stocke tous les paramètres Minecraft personnalisés
}


# ============================================================
# ICONES EN BASE64 (Minecraft style)
# ============================================================

# Icône Creeper simple 16x16 en base64
ICON_CREEPER_B64 = """
iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAXklEQVQ4y2NgGAWjYBQMBcAIxP8JYH0g
/g/E/wlgVSBmJGDQfygeD8R/gPgPlIZhRmBYMALxf5AcCAAxIykmILaHiMMwUIIBiP8S4XJGIPYHYn0S
wwJsDxQT5YJRMLQAAKU7FxXnfvRLAAAAAElFTkSuQmCC
"""

# Icône Play (triangle vert)
ICON_PLAY_B64 = """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAhklEQVRYw+2WwQ2AIBAEt0UrsAtLsFNr
oBU78vPjizEQQS4Ywr4JLLuzHARJyeXySNIxkjTVkjbthyRpPyXprSQAYGYnAHckdc6M+7MDeAJwk3T4
q8xvZhcnvJldANiccAOwO+EGYAByBmB3wgUA2J1wAbBb4QDAboULgB2IFgDsQLgA+G8CAPoLsQFdG+M0
qwAAAABJRU5ErkJggg==
"""

# Icône Settings (engrenage)
ICON_SETTINGS_B64 = """
iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAoklEQVRIie2UMQ6AIBAEt/Qx+Bp9ir7G
ytLS2NhYGUMBCCEHSExMnGQbIPdndwk4V0WS9lrSIklyxpgDSV9JOiS9Y4wBgLUWAO4ANpJWf+L4jJmd
JR0l7QHcJU0AzCTtJG0BPACcJM0kbSRtADwBnCXNJK0lrQE8AVwkzSUtJC0APAFcJc0lzSXNATwB3CTN
Jc0kTQE8JN0lTSVNANwk/QDeGx0fV7cIAF0AAAAASUVORK5CYII=
"""


# ============================================================
# CLASSES UTILITAIRES
# ============================================================

def create_modern_frame(parent, **kwargs):
    """Crée un frame moderne avec bordure et style uniforme"""
    frame = tk.Frame(parent, bg=COLORS['bg_medium'], 
                    relief='flat', bd=1, highlightbackground=COLORS['border'],
                    highlightthickness=1, **kwargs)
    return frame

class ScrollableFrame(ttk.Frame):
    """Frame avec scrollbar fonctionnel et animations fluides"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.canvas = tk.Canvas(self, bg=COLORS['bg_dark'], highlightthickness=0, 
                               borderwidth=0, relief='flat')
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._smooth_scroll)
        self.scrollable_frame = ttk.Frame(self.canvas, style='TFrame')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Animation de scroll
        self.scroll_target = 0
        self.scroll_current = 0
        self.scroll_animating = False
        
        # Bind mouse wheel avec animation
        self.canvas.bind('<Enter>', self._bind_mousewheel)
        self.canvas.bind('<Leave>', self._unbind_mousewheel)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Resize canvas frame width
        self.canvas.bind('<Configure>', self._on_canvas_configure)
    
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def _smooth_scroll(self, *args):
        """Scroll fluide avec animation"""
        self.canvas.yview(*args)
    
    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_smooth)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_smooth)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_smooth)
    
    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
    
    def _on_mousewheel_smooth(self, event):
        """Scroll fluide avec animation"""
        if event.num == 4:  # Linux scroll up
            delta = -3
        elif event.num == 5:  # Linux scroll down
            delta = 3
        else:  # Windows
            delta = int(-1 * (event.delta / 40))
        
        # Animation fluide
        self._animate_scroll(delta)
    
    def _animate_scroll(self, delta):
        """Anime le scroll de manière fluide"""
        steps = abs(delta)
        step_size = delta / steps if steps > 0 else 0
        
        def scroll_step(step=0):
            if step < steps:
                self.canvas.yview_scroll(int(step_size), "units")
                self.canvas.after(5, lambda: scroll_step(step + 1))
        
        scroll_step()


class AnimatedButton(tk.Canvas):
    """Bouton animé moderne avec transitions fluides"""
    def __init__(self, parent, text, command, color='green', width=200, height=50, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, 
                        bg=COLORS['bg_dark'], **kwargs)
        
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.animation_id = None
        self.is_hovered = False
        self.is_pressed = False
        self.enabled = True
        
        # Animation state
        self.anim_progress = 0.0  # 0.0 à 1.0
        self.anim_direction = 0  # -1, 0, 1
        self.anim_speed = 0.15
        
        # Couleurs selon le type (thème moderne)
        if color == 'green':
            self.color_normal = COLORS['accent_green']
            self.color_hover = COLORS['accent_green_hover']
            self.color_pressed = COLORS['accent_green_pressed']
            self.color_glow = COLORS['accent_green_glow']
        elif color == 'red':
            self.color_normal = COLORS['accent_red']
            self.color_hover = COLORS['accent_red_hover']
            self.color_pressed = '#d32f2f'
            self.color_glow = '#c62828'
        elif color == 'gold':
            self.color_normal = COLORS['accent_gold']
            self.color_hover = COLORS['accent_gold_hover']
            self.color_pressed = '#b8860b'
            self.color_glow = '#9a7209'
        else:  # gray
            self.color_normal = COLORS['bg_light']
            self.color_hover = COLORS['bg_hover']
            self.color_pressed = COLORS['bg_medium']
            self.color_glow = COLORS['border']
        
        self.current_color = self.color_normal
        self.target_color = self.color_normal
        
        self.draw()
        self._animate()
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<ButtonPress-1>', self.on_press)
        self.bind('<ButtonRelease-1>', self.on_release)
    
    def _interpolate_color(self, color1, color2, factor):
        """Interpole entre deux couleurs hex"""
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        rgb = tuple(rgb1[i] + (rgb2[i] - rgb1[i]) * factor for i in range(3))
        return rgb_to_hex(rgb)
    
    def _animate(self):
        """Animation continue pour transitions fluides"""
        if self.anim_direction != 0:
            self.anim_progress += self.anim_direction * self.anim_speed
            if self.anim_progress <= 0:
                self.anim_progress = 0
                self.anim_direction = 0
            elif self.anim_progress >= 1:
                self.anim_progress = 1
                self.anim_direction = 0
            
            self.draw()
        
        self.animation_id = self.after(16, self._animate)  # ~60 FPS
    
    def draw(self):
        self.delete("all")
        
        if not self.enabled:
            color = COLORS['bg_light']
            border = COLORS['bg_medium']
            glow_opacity = 0
        elif self.is_pressed:
            color = self.color_pressed
            border = self.color_glow
            glow_opacity = 0.3
        elif self.is_hovered:
            # Interpolation fluide pour le hover
            color = self._interpolate_color(self.color_normal, self.color_hover, self.anim_progress)
            border = self.color_glow
            glow_opacity = self.anim_progress * 0.2
        else:
            color = self._interpolate_color(self.color_hover, self.color_normal, 1 - self.anim_progress)
            border = COLORS['border']
            glow_opacity = 0
        
        # Ombre portée moderne
        shadow_offset = 3
        shadow_blur = 2
        for i in range(shadow_blur):
            alpha = 0.1 - (i * 0.03)
            shadow_color = self._interpolate_color(COLORS['bg_dark'], '#000000', alpha)
            self.create_rectangle(
                shadow_offset + i, shadow_offset + i,
                self.width - shadow_offset + i, self.height - shadow_offset + i,
                fill=shadow_color, outline='', width=0
            )
        
        # Glow effect
        if glow_opacity > 0:
            glow_color = self._interpolate_color(COLORS['bg_dark'], self.color_glow, glow_opacity)
            self.create_rectangle(-2, -2, self.width+2, self.height+2,
                                fill=glow_color, outline='', width=0)
        
        # Bouton principal avec coins arrondis (simulés)
        offset = 2 if self.is_pressed else 0
        radius = 6
        
        # Rectangle principal
        self.create_rectangle(
            2+offset, 2+offset,
            self.width-2+offset, self.height-2+offset,
            fill=color, outline=border, width=2
        )
        
        # Texte avec ombre légère
        text_color = COLORS['text_white'] if self.enabled else COLORS['text_muted']
        # Ombre du texte
        self.create_text(
            self.width//2 + offset + 1, self.height//2 + offset + 1,
            text=self.text, fill='#000000', font=('Segoe UI', 12, 'bold'),
            state='disabled'
        )
        # Texte principal
        self.create_text(
            self.width//2 + offset, self.height//2 + offset,
            text=self.text, fill=text_color, font=('Segoe UI', 12, 'bold')
        )
    
    def on_enter(self, event):
        if self.enabled:
            self.is_hovered = True
            self.anim_direction = 1
            self.target_color = self.color_hover
    
    def on_leave(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self.anim_direction = -1
        self.target_color = self.color_normal
    
    def on_press(self, event):
        if self.enabled:
            self.is_pressed = True
            self.draw()
    
    def on_release(self, event):
        if self.enabled and self.is_pressed:
            self.is_pressed = False
            self.draw()
            if self.command:
                self.command()
    
    def set_enabled(self, enabled):
        self.enabled = enabled
        self.draw()
    
    def set_text(self, text):
        self.text = text
        self.draw()


class ProgressBarMC(tk.Canvas):
    """Barre de progression moderne avec animations fluides"""
    def __init__(self, parent, width=300, height=20, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0,
                        bg=COLORS['bg_dark'], **kwargs)
        self.width = width
        self.height = height
        self.progress = 0
        self.target_progress = 0
        self.animating = False
        self.draw()
        self._animate()
    
    def _animate(self):
        """Animation fluide de la barre de progression"""
        if abs(self.progress - self.target_progress) > 0.5:
            diff = self.target_progress - self.progress
            self.progress += diff * 0.1  # Interpolation fluide
            self.draw()
        else:
            self.progress = self.target_progress
            self.animating = False
        
        self.after(16, self._animate)  # ~60 FPS
    
    def draw(self):
        self.delete("all")
        
        # Ombre de la barre
        self.create_rectangle(2, 2, self.width, self.height + 2, 
                            fill=COLORS['bg_dark'], outline='', width=0)
        
        # Fond de la barre avec bordure moderne
        self.create_rectangle(0, 0, self.width, self.height, 
                            fill=COLORS['bg_medium'], outline=COLORS['border'], width=1)
        
        # Barre de progression avec dégradé simulé
        if self.progress > 0:
            pw = int((self.width - 4) * (self.progress / 100))
            
            # Dégradé (simulé avec plusieurs rectangles)
            gradient_steps = 3
            step_width = pw // gradient_steps
            for i in range(gradient_steps):
                x1 = 2 + (i * step_width)
                x2 = 2 + ((i + 1) * step_width) if i < gradient_steps - 1 else 2 + pw
                
                # Interpolation de couleur pour dégradé
                factor = i / gradient_steps
                color = self._interpolate_color(
                    COLORS['accent_green_pressed'],
                    COLORS['accent_green'],
                    factor
                )
                
                self.create_rectangle(x1, 2, x2, self.height - 2,
                                    fill=color, outline='', width=0)
            
            # Lueur en haut de la barre
            self.create_line(2, 2, 2 + pw, 2,
                           fill=COLORS['accent_green_hover'], width=1)
        
        # Texte avec ombre
        text = f"{int(self.progress)}%"
        self.create_text(self.width//2 + 1, self.height//2 + 1, 
                        text=text, fill='#000000', 
                        font=('Segoe UI', 9, 'bold'), state='disabled')
        self.create_text(self.width//2, self.height//2, 
                        text=text, fill=COLORS['text_white'], 
                        font=('Segoe UI', 9, 'bold'))
    
    def _interpolate_color(self, color1, color2, factor):
        """Interpole entre deux couleurs hex"""
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        rgb = tuple(rgb1[i] + (rgb2[i] - rgb1[i]) * factor for i in range(3))
        return rgb_to_hex(rgb)
    
    def set_progress(self, value):
        self.target_progress = max(0, min(100, value))
        self.animating = True


# ============================================================
# SYSTEM TRAY (Windows)
# ============================================================

class SystemTray:
    """Gestion de l'icône dans la barre des tâches"""
    def __init__(self, root, on_quit, on_show):
        self.root = root
        self.on_quit = on_quit
        self.on_show = on_show
        self.icon = None
        self.tray_available = False
        
        try:
            import pystray
            from PIL import Image
            self.pystray = pystray
            self.PIL_Image = Image
            self.tray_available = True
        except ImportError:
            print("[Tray] pystray ou PIL non disponible")
    
    def create_image(self):
        """Crée l'icône pour le tray"""
        # Créer une image simple 64x64 (Creeper face)
        img = self.PIL_Image.new('RGB', (64, 64), '#4CAF50')
        pixels = img.load()
        
        # Dessiner un visage de Creeper simplifié
        for x in range(64):
            for y in range(64):
                # Yeux (deux carrés noirs)
                if (8 <= x <= 20 and 16 <= y <= 28) or (44 <= x <= 56 and 16 <= y <= 28):
                    pixels[x, y] = (0, 0, 0)
                # Bouche
                elif (24 <= x <= 40 and 32 <= y <= 40):
                    pixels[x, y] = (0, 0, 0)
                elif (20 <= x <= 28 and 40 <= y <= 52):
                    pixels[x, y] = (0, 0, 0)
                elif (36 <= x <= 44 and 40 <= y <= 52):
                    pixels[x, y] = (0, 0, 0)
        
        return img
    
    def setup(self):
        """Configure l'icône tray"""
        if not self.tray_available:
            return False
        
        try:
            image = self.create_image()
            menu = self.pystray.Menu(
                self.pystray.MenuItem("Ouvrir Illama Launcher", self._on_show, default=True),
                self.pystray.MenuItem("Quitter", self._on_quit)
            )
            self.icon = self.pystray.Icon("illama_launcher", image, "Illama Launcher", menu)
            return True
        except Exception as e:
            print(f"[Tray] Erreur setup: {e}")
            return False
    
    def _on_show(self, icon=None, item=None):
        if self.on_show:
            self.root.after(0, self.on_show)
    
    def _on_quit(self, icon=None, item=None):
        if self.icon:
            self.icon.stop()
        if self.on_quit:
            self.root.after(0, self.on_quit)
    
    def run(self):
        """Lance l'icône tray dans un thread séparé"""
        if self.icon:
            threading.Thread(target=self.icon.run, daemon=True).start()
    
    def stop(self):
        """Arrête l'icône tray"""
        if self.icon:
            try:
                self.icon.stop()
            except:
                pass


# ============================================================
# GOOGLE DRIVE SYNC
# ============================================================

class GoogleDriveSync:
    def __init__(self, folder_id: str, local_mods_path: Path, api_key: str = ""):
        self.folder_id = folder_id
        self.local_mods_path = local_mods_path
        self.api_key = api_key
        self.ssl_context = ssl.create_default_context()
        
    def _make_request(self, url: str) -> bytes:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=30) as response:
            return response.read()
    
    def get_folder_files(self) -> list:
        files = []
        
        # Methode API
        if self.api_key:
            try:
                url = f"https://www.googleapis.com/drive/v3/files?q='{self.folder_id}'+in+parents&key={self.api_key}&fields=files(id,name,size,md5Checksum)&pageSize=1000"
                data = json.loads(self._make_request(url))
                for f in data.get('files', []):
                    if f['name'].endswith('.jar'):
                        files.append({'id': f['id'], 'name': f['name'], 'md5': f.get('md5Checksum', '')})
                print(f"[API] {len(files)} mods trouves")
                return files
            except Exception as e:
                print(f"[API] Erreur: {e}")
        
        # Methode scraping fallback
        try:
            url = f"https://drive.google.com/drive/folders/{self.folder_id}"
            html = self._make_request(url).decode('utf-8', errors='ignore')
            
            jar_names = set(re.findall(r'"([^"]+\.jar)"', html, re.IGNORECASE))
            pattern_pairs = r'"(1[a-zA-Z0-9_-]{25,45})","([^"]+\.jar)"'
            pairs = re.findall(pattern_pairs, html, re.IGNORECASE)
            
            seen_names = set()
            for file_id, file_name in pairs:
                if file_name not in seen_names and len(file_id) >= 25:
                    files.append({'id': file_id, 'name': file_name, 'md5': ''})
                    seen_names.add(file_name)
            
            print(f"[Scraping] {len(files)} mods trouves")
        except Exception as e:
            print(f"[Scraping] Erreur: {e}")
            
        return files
    
    def _calculate_md5(self, file_path: Path) -> str:
        """Calcule le MD5 d'un fichier local"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"[MD5] Erreur pour {file_path}: {e}")
            return ''
    
    def download_file(self, file_id: str, file_name: str, overwrite: bool = True, progress_callback: Optional[Callable] = None, config: Optional[dict] = None) -> bool:
        """Télécharge un fichier avec optimisations pour la vitesse"""
        if config is None:
            config = {}
        
        file_path = self.local_mods_path / file_name
        
        # Supprimer l'ancien fichier s'il existe
        if file_path.exists() and overwrite:
            try:
                file_path.unlink()
            except:
                pass
        
        # URLs optimisées pour Google Drive (ordre par vitesse)
        urls = [
            f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t&uuid=",
            f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t",
            f"https://drive.google.com/uc?export=download&id={file_id}"
        ]
        
        max_retries = config.get('download_retries', 3)
        chunk_size = config.get('download_chunk_size', 32768)  # 32KB par défaut
        timeout = config.get('download_timeout', 180)
        
        for attempt in range(max_retries):
            for url in urls:
                try:
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    req.add_header('Accept', '*/*')
                    req.add_header('Accept-Language', 'en-US,en;q=0.9')
                    
                    with urllib.request.urlopen(req, context=self.ssl_context, timeout=timeout) as response:
                        # Vérifier le Content-Type pour éviter les pages HTML
                        content_type = response.headers.get('Content-Type', '').lower()
                        if 'text/html' in content_type or 'text/plain' in content_type:
                            # Probablement une page HTML, essayer l'URL suivante
                            continue
                        
                        # Télécharger avec buffer optimisé
                        total_size = int(response.headers.get('Content-Length', 0))
                        downloaded = 0
                        
                        with open(file_path, 'wb') as f:
                            while True:
                                chunk = response.read(chunk_size)
                                if not chunk:
                                    break
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Callback de progression si disponible
                                if progress_callback and total_size > 0:
                                    progress_callback(file_name, downloaded, total_size)
                        
                        # Vérifier que le fichier est valide (au moins 100 bytes et commence par PK)
                        if file_path.stat().st_size > 100:
                            with open(file_path, 'rb') as f:
                                header = f.read(2)
                                if header == b'PK':
                                    file_size_mb = file_path.stat().st_size / 1024 / 1024
                                    print(f"[Download] {file_name} telecharge ({file_size_mb:.2f} MB)")
                                    return True
                        
                        # Si le fichier n'est pas valide, le supprimer et réessayer
                        try:
                            file_path.unlink()
                        except:
                            pass
                        
                except urllib.error.HTTPError as e:
                    if e.code == 429:  # Too Many Requests
                        time.sleep(2 ** attempt)  # Backoff exponentiel
                    continue
                except (urllib.error.URLError, TimeoutError, OSError) as e:
                    if attempt < max_retries - 1:
                        time.sleep(0.5 * (attempt + 1))  # Petit délai avant retry
                    continue
                except Exception as e:
                    print(f"[Download] Erreur {file_name} (tentative {attempt + 1}): {e}")
                    continue
        
        # Si tous les essais ont échoué
        print(f"[Download] Echec apres {max_retries} tentatives: {file_name}")
        return False
    
    def sync(self, progress_callback: Optional[Callable] = None, force_replace: bool = False, config: Optional[dict] = None) -> dict:
        stats = {'added': [], 'removed': [], 'unchanged': [], 'updated': [], 'errors': []}
        self.local_mods_path.mkdir(parents=True, exist_ok=True)
        
        if progress_callback:
            progress_callback("Recuperation de la liste...", 0, 100)
            
        remote_files = self.get_folder_files()
        remote_dict = {f['name']: f for f in remote_files}
        remote_names = {f['name'] for f in remote_files}
        
        local_files = {f.name for f in self.local_mods_path.iterdir() if f.suffix == '.jar'}
        
        # Fichiers à télécharger (nouveaux)
        to_download = [f for f in remote_files if f['name'] not in local_files]
        
        # Fichiers à remplacer (existants mais différents)
        to_replace = []
        if force_replace:
            # Si force_replace est True, on remplace tous les fichiers existants
            for f in remote_files:
                if f['name'] in local_files:
                    to_replace.append(f)
        else:
            # Sinon, on compare les MD5
            if progress_callback:
                progress_callback("Verification des fichiers...", 10, 100)
            
            for f in remote_files:
                if f['name'] in local_files:
                    local_path = self.local_mods_path / f['name']
                    local_md5 = self._calculate_md5(local_path)
                    remote_md5 = f.get('md5', '')
                    
                    # Si les MD5 sont différents ou si le MD5 distant n'est pas disponible, on marque pour remplacement
                    if remote_md5 and local_md5 and remote_md5 != local_md5:
                        to_replace.append(f)
                    elif not remote_md5:
                        # Si pas de MD5 distant, on considère comme inchangé (fallback)
                        stats['unchanged'].append(f['name'])
                    elif local_md5 == remote_md5:
                        stats['unchanged'].append(f['name'])
                    else:
                        # Si pas de MD5 local, on remplace
                        to_replace.append(f)
        
        # Fichiers à supprimer
        to_remove = local_files - remote_names
        
        # Télécharger les fichiers en parallèle pour accélérer
        total = len(to_download) + len(to_replace)
        all_files = [(f, 'add') for f in to_download] + [(f, 'replace') for f in to_replace]
        
        if total == 0:
            if progress_callback:
                progress_callback("Synchronisation terminee!", 100, 100)
            return stats
        
        # Téléchargement parallèle avec ThreadPoolExecutor
        if config is None:
            config = {}
        max_workers_config = config.get('download_workers', 5)
        max_workers = min(max_workers_config, total)  # Nombre de téléchargements simultanés (configurable)
        
        completed = [0]  # Utiliser une liste pour pouvoir modifier depuis les fonctions imbriquées
        lock = threading.Lock()
        
        def download_with_callback(file_info, action):
            """Wrapper pour télécharger avec callback de progression"""
            file_name = file_info['name']
            
            def file_progress_callback(name, downloaded, total_size):
                """Callback pour la progression d'un fichier individuel"""
                if progress_callback:
                    # Afficher le fichier en cours
                    with lock:
                        current_completed = completed[0]
                    # Estimation basée sur le fichier en cours
                    base_pct = (current_completed / total * 90) if total > 0 else 0
                    file_pct = (downloaded / total_size * 10 / total) if total_size > 0 and total > 0 else 0
                    pct_global = min(100, base_pct + file_pct)
                    
                    size_mb = downloaded / 1024 / 1024
                    total_mb = total_size / 1024 / 1024 if total_size > 0 else 0
                    if total_size > 0:
                        msg = f"{name[:30]}... ({size_mb:.1f}/{total_mb:.1f} MB)"
                    else:
                        msg = f"{name[:30]}... ({size_mb:.1f} MB)"
                    progress_callback(msg, pct_global, 100)
            
            result = self.download_file(file_info['id'], file_name, overwrite=(action == 'replace'), 
                                       progress_callback=file_progress_callback, config=config)
            
            with lock:
                completed[0] += 1
                current = completed[0]
                if progress_callback:
                    pct = (current / total * 100) if total > 0 else 100
                    progress_callback(f"Telechargement {current}/{total} fichiers...", pct, 100)
            
            return (file_info, action, result)
        
        # Lancer les téléchargements en parallèle
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(download_with_callback, file_info, action): (file_info, action) 
                      for file_info, action in all_files}
            
            for future in as_completed(futures):
                try:
                    file_info, action, success = future.result()
                    file_name = file_info['name']
                    
                    if success:
                        if action == 'add':
                            stats['added'].append(file_name)
                        else:
                            stats['updated'].append(file_name)
                    else:
                        stats['errors'].append(file_name)
                except Exception as e:
                    file_info, action = futures[future]
                    stats['errors'].append(file_info['name'])
                    print(f"[Sync] Erreur telechargement {file_info['name']}: {e}")
        
        # Supprimer les fichiers obsolètes
        for file_name in to_remove:
            try:
                (self.local_mods_path / file_name).unlink()
                stats['removed'].append(file_name)
            except:
                pass
        
        if progress_callback:
            progress_callback("Synchronisation terminee!", 100, 100)
        return stats


# ============================================================
# MINECRAFT LAUNCHER
# ============================================================

class MinecraftLauncher:
    def __init__(self, config: dict):
        self.config = config
        self.instance_name = "IllamaServer"
        
    def get_prism_data_dir(self) -> Path:
        """Trouve le dossier data de Prism Launcher"""
        if sys.platform == 'win32':
            # Prism stocke ses données dans AppData/Roaming/PrismLauncher
            prism_dir = Path(os.environ.get('APPDATA', '')) / 'PrismLauncher'
            if prism_dir.exists():
                return prism_dir
            # Alternative: dossier portable
            prism_exe = self.find_prism_launcher()
            if prism_exe:
                portable = Path(prism_exe).parent / 'instances'
                if portable.exists():
                    return Path(prism_exe).parent
        return Path(os.environ.get('APPDATA', '')) / 'PrismLauncher'
    
    def get_instances_dir(self) -> Path:
        """Trouve le dossier des instances Prism"""
        return self.get_prism_data_dir() / 'instances'
    
    def get_instance_dir(self) -> Path:
        """Retourne le dossier de notre instance"""
        return self.get_instances_dir() / self.instance_name
    
    def get_minecraft_dir(self) -> Path:
        """Retourne le dossier .minecraft de l'instance"""
        instance_dir = self.get_instance_dir()
        mc_dir = instance_dir / '.minecraft'
        if not mc_dir.exists():
            mc_dir = instance_dir / 'minecraft'
        return mc_dir
    
    def get_mods_dir(self) -> Path:
        """Retourne le dossier mods de l'instance"""
        return self.get_minecraft_dir() / 'mods'
    
    def get_resourcepacks_dir(self) -> Path:
        """Retourne le dossier resourcepacks de l'instance"""
        return self.get_minecraft_dir() / 'resourcepacks'
    
    def get_shaderpacks_dir(self) -> Path:
        """Retourne le dossier shaderpacks de l'instance"""
        return self.get_minecraft_dir() / 'shaderpacks'
    
    def instance_exists(self) -> bool:
        """Vérifie si l'instance existe"""
        instance_dir = self.get_instance_dir()
        return (instance_dir / 'instance.cfg').exists()
    
    def create_instance(self) -> bool:
        """Crée l'instance Prism avec Forge"""
        instance_dir = self.get_instance_dir()
        instance_dir.mkdir(parents=True, exist_ok=True)
        
        mc_version = self.config.get('minecraft_version', '1.20.1')
        forge_version = self.config.get('forge_version', '47.4.1')
        
        # Créer instance.cfg
        instance_cfg = f"""[General]
ConfigVersion=1.2
iconKey=default
name={SERVER_NAME}
InstanceType=OneSix
"""
        with open(instance_dir / 'instance.cfg', 'w') as f:
            f.write(instance_cfg)
        
        # Créer mmc-pack.json (définit MC + Forge)
        mmc_pack = {
            "components": [
                {
                    "cachedName": "LWJGL 3",
                    "cachedVersion": "3.3.1",
                    "dependencyOnly": True,
                    "uid": "org.lwjgl3",
                    "version": "3.3.1"
                },
                {
                    "cachedName": "Minecraft",
                    "cachedRequires": [
                        {"suggests": "3.3.1", "uid": "org.lwjgl3"}
                    ],
                    "cachedVersion": mc_version,
                    "important": True,
                    "uid": "net.minecraft",
                    "version": mc_version
                },
                {
                    "cachedName": "Forge",
                    "cachedRequires": [
                        {"equals": mc_version, "uid": "net.minecraft"}
                    ],
                    "cachedVersion": forge_version,
                    "uid": "net.minecraftforge",
                    "version": forge_version
                }
            ],
            "formatVersion": 1
        }
        
        with open(instance_dir / 'mmc-pack.json', 'w') as f:
            json.dump(mmc_pack, f, indent=4)
        
        # Créer le dossier .minecraft
        mc_dir = instance_dir / '.minecraft'
        mc_dir.mkdir(exist_ok=True)
        (mc_dir / 'mods').mkdir(exist_ok=True)
        (mc_dir / 'resourcepacks').mkdir(exist_ok=True)
        (mc_dir / 'shaderpacks').mkdir(exist_ok=True)
        
        # Créer servers.dat dans l'instance
        self.create_server_dat()
        
        # Créer options.txt dans l'instance  
        self.create_options_txt()
        
        print(f"[Instance] Creee: {instance_dir}")
        return True
    
    def create_server_dat(self):
        """Crée servers.dat avec UNIQUEMENT le serveur Illama (force le serveur)"""
        mc_dir = self.get_minecraft_dir()
        mc_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            import struct
            
            def write_string(s):
                encoded = s.encode('utf-8')
                return struct.pack('>H', len(encoded)) + encoded
            
            def write_compound_header(name):
                return b'\x0a' + write_string(name)
            
            def write_string_tag(name, value):
                return b'\x08' + write_string(name) + write_string(value)
            
            def write_byte_tag(name, value):
                return b'\x01' + write_string(name) + struct.pack('b', value)
            
            # Créer servers.dat avec UNIQUEMENT le serveur Illama
            # Cela écrase toute modification de l'utilisateur
            nbt_data = write_compound_header('')
            nbt_data += b'\x09' + write_string('servers')
            nbt_data += b'\x0a'  # TAG_Compound pour la liste
            nbt_data += struct.pack('>I', 1)  # Un seul serveur
            
            # Serveur Illama uniquement
            nbt_data += write_string_tag('name', SERVER_NAME)
            nbt_data += write_string_tag('ip', SERVER_ADDRESS)
            nbt_data += write_byte_tag('hideAddress', 0)
            nbt_data += b'\x00'  # Fin du compound
            nbt_data += b'\x00'  # Fin du root compound
            
            # Écrire en mode binaire pour écraser toute modification
            server_file = mc_dir / 'servers.dat'
            
            # Supprimer le fichier s'il existe pour forcer la réécriture
            if server_file.exists():
                try:
                    # Retirer les attributs en lecture seule si présents
                    if sys.platform == 'win32':
                        try:
                            import win32api
                            win32api.SetFileAttributes(str(server_file), 128)  # FILE_ATTRIBUTE_NORMAL
                        except (ImportError, AttributeError):
                            # Fallback: utiliser stat pour retirer la lecture seule
                            import stat
                            current_mode = server_file.stat().st_mode
                            os.chmod(server_file, current_mode | stat.S_IWRITE)
                    else:
                        os.chmod(server_file, 0o644)
                except:
                    pass
                server_file.unlink()
            
            # Créer le nouveau fichier
            with open(server_file, 'wb') as f:
                f.write(nbt_data)
            
            # Rendre le fichier en lecture seule pour empêcher les modifications
            try:
                if sys.platform == 'win32':
                    try:
                        import win32api
                        win32api.SetFileAttributes(str(server_file), 1)  # FILE_ATTRIBUTE_READONLY
                    except ImportError:
                        # Fallback sans win32api
                        import stat
                        os.chmod(server_file, stat.S_IREAD)  # Lecture seule uniquement
                else:
                    os.chmod(server_file, 0o444)  # Lecture seule
            except:
                # Ignorer si on ne peut pas changer les permissions
                pass
            
            print(f"[Server] servers.dat force avec {SERVER_ADDRESS} uniquement (lecture seule)")
        except Exception as e:
            print(f"[Server] Erreur: {e}")
    
    def create_options_txt(self):
        """Crée options.txt avec nos paramètres dans l'instance - FORCE la connexion auto"""
        mc_dir = self.get_minecraft_dir()
        mc_dir.mkdir(parents=True, exist_ok=True)
        options_file = mc_dir / "options.txt"
        
        options = {}
        if options_file.exists():
            try:
                with open(options_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if ':' in line:
                            key, value = line.strip().split(':', 1)
                            options[key] = value
            except:
                pass
        
        # Appliquer nos paramètres
        fullscreen = self.config.get('fullscreen', False)
        borderless = self.config.get('borderless', False)
        
        # Si borderless est activé, utiliser la résolution de l'écran
        if borderless:
            try:
                # Obtenir la résolution de l'écran selon l'OS
                if sys.platform == 'win32':
                    import ctypes
                    user32 = ctypes.windll.user32
                    width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
                    height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
                else:
                    # Linux/Mac - fallback
                    width = 1920
                    height = 1080
                
                # Borderless = plein écran mais en mode fenêtré (sans bordure)
                options['fullscreen'] = 'false'
                options['overrideWidth'] = str(width)
                options['overrideHeight'] = str(height)
                print(f"[Options] Mode Borderless: {width}x{height} (plein ecran fenetre)")
            except Exception as e:
                # Fallback si erreur
                print(f"[Options] Erreur detection resolution: {e}")
                width = self.config.get('window_width', 1920)
                height = self.config.get('window_height', 1080)
                options['overrideWidth'] = str(width)
                options['overrideHeight'] = str(height)
                options['fullscreen'] = 'false'
        else:
            width = self.config.get('window_width', 854)
            height = self.config.get('window_height', 480)
            options['overrideWidth'] = str(width)
            options['overrideHeight'] = str(height)
            options['fullscreen'] = 'true' if fullscreen else 'false'
        
        # FORCER la connexion automatique au serveur Illama (toujours)
        options['lastServer'] = SERVER_ADDRESS
        options['lastServerName'] = SERVER_NAME
        
        # Appliquer les paramètres Minecraft personnalisés
        minecraft_options = self.config.get('minecraft_options', {})
        if minecraft_options:
            # Graphiques
            if 'graphics' in minecraft_options:
                options['graphics'] = minecraft_options['graphics']
            if 'renderDistance' in minecraft_options:
                options['renderDistance'] = str(minecraft_options['renderDistance'])
            if 'entityDistanceScaling' in minecraft_options:
                options['entityDistanceScaling'] = str(minecraft_options['entityDistanceScaling'])
            if 'particles' in minecraft_options:
                options['particles'] = minecraft_options['particles']
            if 'maxFps' in minecraft_options:
                options['maxFps'] = str(minecraft_options['maxFps'])
            if 'vsync' in minecraft_options:
                options['vsync'] = 'true' if minecraft_options['vsync'] else 'false'
            if 'entityShadows' in minecraft_options:
                options['entityShadows'] = 'true' if minecraft_options['entityShadows'] else 'false'
            if 'useVbo' in minecraft_options:
                options['useVbo'] = 'true' if minecraft_options['useVbo'] else 'false'
            
            # Rendu Avancé
            if 'ao' in minecraft_options:
                options['ao'] = minecraft_options['ao']
            if 'smoothLighting' in minecraft_options:
                options['smoothLighting'] = minecraft_options['smoothLighting']
            if 'gamma' in minecraft_options:
                options['gamma'] = str(minecraft_options['gamma'])
            if 'mipmapLevels' in minecraft_options:
                options['mipmapLevels'] = str(minecraft_options['mipmapLevels'])
            if 'anisotropicFiltering' in minecraft_options:
                options['anisotropicFiltering'] = str(minecraft_options['anisotropicFiltering'])
            if 'biomeBlendRadius' in minecraft_options:
                options['biomeBlendRadius'] = str(minecraft_options['biomeBlendRadius'])
            if 'renderClouds' in minecraft_options:
                options['renderClouds'] = minecraft_options['renderClouds']
            if 'renderSky' in minecraft_options:
                options['renderSky'] = 'true' if minecraft_options['renderSky'] else 'false'
            if 'renderStars' in minecraft_options:
                options['renderStars'] = 'true' if minecraft_options['renderStars'] else 'false'
            if 'renderSunMoon' in minecraft_options:
                options['renderSunMoon'] = 'true' if minecraft_options['renderSunMoon'] else 'false'
            
            # Performance
            if 'chunkUpdateThreads' in minecraft_options:
                options['chunkUpdateThreads'] = str(minecraft_options['chunkUpdateThreads'])
            if 'prioritizeChunkUpdates' in minecraft_options:
                options['prioritizeChunkUpdates'] = 'true' if minecraft_options['prioritizeChunkUpdates'] else 'false'
            if 'animateOnlyVisibleTextures' in minecraft_options:
                options['animateOnlyVisibleTextures'] = 'true' if minecraft_options['animateOnlyVisibleTextures'] else 'false'
            
            # Audio
            if 'sound' in minecraft_options:
                options['sound'] = str(minecraft_options['sound'])
            if 'music' in minecraft_options:
                options['music'] = str(minecraft_options['music'])
            
            # Contrôles
            if 'sensitivity' in minecraft_options:
                options['sensitivity'] = str(minecraft_options['sensitivity'])
            if 'invertYMouse' in minecraft_options:
                options['invertYMouse'] = 'true' if minecraft_options['invertYMouse'] else 'false'
            if 'autoJump' in minecraft_options:
                options['autoJump'] = 'true' if minecraft_options['autoJump'] else 'false'
            
            # Interface
            if 'guiScale' in minecraft_options:
                options['guiScale'] = str(minecraft_options['guiScale'])
            if 'fov' in minecraft_options:
                options['fov'] = str(minecraft_options['fov'])
            if 'bobbing' in minecraft_options:
                options['bobbing'] = 'true' if minecraft_options['bobbing'] else 'false'
            
            # Chat
            if 'chatOpacity' in minecraft_options:
                options['chatOpacity'] = str(minecraft_options['chatOpacity'])
            if 'chatColors' in minecraft_options:
                options['chatColors'] = 'true' if minecraft_options['chatColors'] else 'false'
            
            # Autres
            if 'difficulty' in minecraft_options:
                options['difficulty'] = minecraft_options['difficulty']
            if 'showSubtitles' in minecraft_options:
                options['showSubtitles'] = 'true' if minecraft_options['showSubtitles'] else 'false'
            if 'reducedDebugInfo' in minecraft_options:
                options['reducedDebugInfo'] = 'true' if minecraft_options['reducedDebugInfo'] else 'false'
        
        with open(options_file, 'w', encoding='utf-8') as f:
            for key, value in options.items():
                f.write(f"{key}:{value}\n")
        
        if borderless:
            print(f"[Options] Mode Borderless active, connexion auto forcee vers {SERVER_ADDRESS}")
        else:
            print(f"[Options] Resolution {width}x{height}, connexion auto forcee vers {SERVER_ADDRESS}")
    
    def update_instance_settings(self):
        """Met à jour les paramètres de l'instance (RAM, etc.)"""
        instance_dir = self.get_instance_dir()
        
        ram_min = self.config.get('ram_min', 2048)  # En MB
        ram_max = self.config.get('ram_max', 4096)  # En MB
        
        # Créer/modifier instance.cfg avec les JVM args
        instance_cfg_path = instance_dir / 'instance.cfg'
        
        cfg_content = {}
        if instance_cfg_path.exists():
            with open(instance_cfg_path, 'r') as f:
                current_section = 'General'
                for line in f:
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                    elif '=' in line:
                        key, value = line.split('=', 1)
                        cfg_content[key] = value
        
        # Mettre à jour les paramètres (déjà en MB, pas besoin de conversion)
        cfg_content['MinMemAlloc'] = str(ram_min)
        cfg_content['MaxMemAlloc'] = str(ram_max)
        cfg_content['OverrideMemory'] = 'true'
        cfg_content['name'] = SERVER_NAME
        
        # JVM args personnalisés
        jvm_args = self.config.get('jvm_args', '')
        if jvm_args:
            cfg_content['JvmArgs'] = jvm_args
            cfg_content['OverrideJavaArgs'] = 'true'
        
        # Écrire le fichier
        with open(instance_cfg_path, 'w') as f:
            f.write('[General]\n')
            for key, value in cfg_content.items():
                f.write(f'{key}={value}\n')
        
        ram_min_gb = ram_min / 1024
        ram_max_gb = ram_max / 1024
        print(f"[Instance] RAM: {ram_min}MB ({ram_min_gb:.1f}GB) - {ram_max}MB ({ram_max_gb:.1f}GB)")
    
    def find_prism_launcher(self) -> str:
        """Trouve l'exécutable Prism Launcher"""
        if sys.platform == 'win32':
            possible_paths = [
                Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'PrismLauncher' / 'prismlauncher.exe',
                Path(os.environ.get('PROGRAMFILES', '')) / 'PrismLauncher' / 'prismlauncher.exe',
                Path(os.environ.get('PROGRAMFILES(X86)', '')) / 'PrismLauncher' / 'prismlauncher.exe',
            ]
            for path in possible_paths:
                if path.exists():
                    return str(path)
        else:
            import shutil
            if shutil.which('prismlauncher'):
                return 'prismlauncher'
        return None
    
    def launch(self) -> bool:
        """Lance l'instance directement - FORCE le serveur Illama uniquement"""
        prism_path = self.find_prism_launcher()
        
        if not prism_path:
            print("[Launch] Prism Launcher non trouve!")
            return False
        
        # Créer l'instance si elle n'existe pas
        if not self.instance_exists():
            print("[Launch] Creation de l'instance...")
            self.create_instance()
        
        # Mettre à jour les paramètres
        self.update_instance_settings()
        
        # FORCER le serveur Illama à chaque lancement (écrase toute modification)
        # Faire cela JUSTE AVANT le lancement pour éviter toute modification
        print("[Launch] Verification et enforcement du serveur Illama...")
        self._enforce_server_only()
        self.create_options_txt()
        
        # Réécrire servers.dat une dernière fois juste avant le lancement
        self.create_server_dat()
        
        try:
            # Lancer Prism avec l'instance directement
            # -l <instance> lance l'instance directement
            print(f"[Launch] Lancement de l'instance {self.instance_name}...")
            process = subprocess.Popen([prism_path, '-l', self.instance_name])
            
            # Attendre un peu puis réécrire servers.dat pour s'assurer qu'il n'a pas été modifié
            def recheck_server():
                time.sleep(2)  # Attendre 2 secondes
                self._enforce_server_only()
                self.create_server_dat()
            
            threading.Thread(target=recheck_server, daemon=True).start()
            
            return True
        except Exception as e:
            print(f"[Launch] Erreur: {e}")
            # Fallback: lancer Prism sans argument
            try:
                subprocess.Popen([prism_path])
                return True
            except:
                return False
    
    def _enforce_server_only(self):
        """S'assure que servers.dat contient UNIQUEMENT le serveur Illama"""
        mc_dir = self.get_minecraft_dir()
        server_file = mc_dir / 'servers.dat'
        
        # Toujours réécrire le fichier pour forcer notre serveur
        # Cela écrase toute modification de l'utilisateur ou de Prism
        try:
            self.create_server_dat()
            
            # Vérifier que le fichier existe et est en lecture seule
            if server_file.exists():
                try:
                    if sys.platform == 'win32':
                        try:
                            import win32api
                            attrs = win32api.GetFileAttributes(str(server_file))
                            if not (attrs & 1):  # Si pas en lecture seule
                                win32api.SetFileAttributes(str(server_file), 1)  # FILE_ATTRIBUTE_READONLY
                        except (ImportError, AttributeError):
                            # Fallback sans win32api
                            import stat
                            os.chmod(server_file, stat.S_IREAD)
                    else:
                        os.chmod(server_file, 0o444)  # Lecture seule
                except:
                    pass
            
            print("[Server] Enforcement: serveur Illama force et verrouille")
        except Exception as e:
            print(f"[Server] Erreur enforcement: {e}")


# ============================================================
# MICROSOFT AUTH
# ============================================================

class MicrosoftAuth:
    """Authentification Microsoft pour Minecraft"""
    
    def __init__(self):
        self.ssl_context = ssl.create_default_context()
    
    def _request(self, url: str, data: dict = None, headers: dict = None) -> dict:
        if headers is None:
            headers = {}
        
        if data:
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            data_encoded = None
        
        req = urllib.request.Request(url, data=data_encoded, headers=headers)
        
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    
    def get_device_code(self) -> dict:
        """Obtient un device code pour l'auth"""
        url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode"
        data = {
            'client_id': MS_CLIENT_ID,
            'scope': 'XboxLive.signin offline_access'
        }
        return self._request(url, data)
    
    def poll_for_token(self, device_code: str, interval: int = 5, timeout: int = 300) -> dict:
        """Poll pour obtenir le token"""
        url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
        data = {
            'client_id': MS_CLIENT_ID,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            'device_code': device_code
        }
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return self._request(url, data)
            except urllib.error.HTTPError as e:
                if e.code == 400:
                    error_data = json.loads(e.read().decode('utf-8'))
                    if error_data.get('error') == 'authorization_pending':
                        time.sleep(interval)
                        continue
                    elif error_data.get('error') == 'slow_down':
                        time.sleep(interval + 5)
                        continue
                raise
        raise TimeoutError("Auth timeout")
    
    def get_xbox_token(self, access_token: str) -> dict:
        """Obtient le token Xbox Live"""
        url = "https://user.auth.xboxlive.com/user/authenticate"
        data = {
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={access_token}"
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT"
        }
        
        req = urllib.request.Request(url, 
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    
    def get_xsts_token(self, xbox_token: str) -> dict:
        """Obtient le token XSTS"""
        url = "https://xsts.auth.xboxlive.com/xsts/authorize"
        data = {
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [xbox_token]
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT"
        }
        
        req = urllib.request.Request(url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    
    def get_minecraft_token(self, xsts_token: str, user_hash: str) -> dict:
        """Obtient le token Minecraft"""
        url = "https://api.minecraftservices.com/authentication/login_with_xbox"
        data = {"identityToken": f"XBL3.0 x={user_hash};{xsts_token}"}
        
        req = urllib.request.Request(url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    
    def check_game_ownership(self, mc_token: str) -> bool:
        """Verifie la possession du jeu"""
        url = "https://api.minecraftservices.com/entitlements/mcstore"
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {mc_token}'})
        
        try:
            with urllib.request.urlopen(req, context=self.ssl_context, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                items = data.get('items', [])
                return any(item.get('name') in ['game_minecraft', 'product_minecraft'] for item in items)
        except:
            return False
    
    def get_profile(self, mc_token: str) -> dict:
        """Obtient le profil Minecraft"""
        url = "https://api.minecraftservices.com/minecraft/profile"
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {mc_token}'})
        
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))


# ============================================================
# ECRAN DE LOGIN
# ============================================================

class LoginScreen:
    """Ecran de connexion Microsoft"""
    
    def __init__(self, on_success: Callable):
        self.on_success = on_success
        self.auth = MicrosoftAuth()
        self.root = tk.Tk()
        self.root.title("Illama Launcher - Connexion")
        self.root.geometry("500x450")
        self.root.minsize(450, 400)
        self.root.configure(bg=COLORS['bg_dark'])
        
        self.create_widgets()
    
    def create_widgets(self):
        main = tk.Frame(self.root, bg=COLORS['bg_dark'])
        main.pack(fill='both', expand=True, padx=40, pady=30)
        
        # Logo / Titre
        title = tk.Label(main, text="ILLAMA", font=('Segoe UI', 36, 'bold'),
                        bg=COLORS['bg_dark'], fg=COLORS['minecraft_green'])
        title.pack(pady=(0, 5))
        
        subtitle = tk.Label(main, text="LAUNCHER", font=('Segoe UI', 14),
                           bg=COLORS['bg_dark'], fg=COLORS['text_gray'])
        subtitle.pack(pady=(0, 30))
        
        # Message
        self.message = tk.Label(main, text="Connexion avec ton compte Microsoft",
                               font=('Segoe UI', 11), bg=COLORS['bg_dark'], fg=COLORS['text_white'])
        self.message.pack(pady=(0, 20))
        
        # Code frame
        self.code_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        self.code_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(self.code_frame, text="Va sur microsoft.com/link et entre ce code:",
                font=('Segoe UI', 10), bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack()
        
        self.code_label = tk.Label(self.code_frame, text="Clique sur Connexion",
                                  font=('Consolas', 20, 'bold'), bg=COLORS['bg_medium'], 
                                  fg=COLORS['accent_gold'])
        self.code_label.pack(pady=10)
        
        self.copy_btn = AnimatedButton(self.code_frame, "Copier le code", self.copy_code, 
                                       color='gray', width=150, height=35)
        self.copy_btn.pack()
        
        # Status
        self.status = tk.Label(main, text="Clique sur le bouton pour commencer", font=('Segoe UI', 10),
                              bg=COLORS['bg_dark'], fg=COLORS['text_gray'])
        self.status.pack(pady=10)
        
        # Progress
        self.progress = ProgressBarMC(main, width=350, height=20)
        self.progress.pack(pady=(0, 20))
        
        # Bouton connexion
        self.login_btn = AnimatedButton(main, "Connexion Microsoft", self.start_login,
                                       color='green', width=250, height=45)
        self.login_btn.pack()
        
        # Bouton mode hors-ligne (pour debug/dev)
        offline_btn = tk.Button(main, text="Mode hors-ligne (dev)", font=('Segoe UI', 8),
                               bg=COLORS['bg_dark'], fg=COLORS['text_gray'], relief='flat',
                               command=self.offline_mode)
        offline_btn.pack(pady=(15, 0))
    
    def copy_code(self):
        code = self.code_label.cget('text')
        if code and code not in ['--------', 'Clique sur Connexion']:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.status.config(text="Code copie!", fg=COLORS['minecraft_green'])
    
    def offline_mode(self):
        """Mode hors-ligne pour dev/debug"""
        username = simpledialog.askstring("Mode hors-ligne", "Entre ton pseudo Minecraft:")
        if username:
            auth_data = {
                'mc_username': username,
                'mc_uuid': 'offline-' + username.lower(),
                'mc_access_token': 'offline',
                'offline_mode': True
            }
            with open(AUTH_FILE, 'w') as f:
                json.dump(auth_data, f)
            self.root.destroy()
            self.on_success(auth_data)
    
    def start_login(self):
        self.login_btn.set_enabled(False)
        self.status.config(text="Obtention du code...", fg=COLORS['text_gray'])
        self.code_label.config(text="Chargement...")
        threading.Thread(target=self._login_thread, daemon=True).start()
    
    def _login_thread(self):
        try:
            # Obtenir device code
            device_data = self.auth.get_device_code()
            user_code = device_data['user_code']
            device_code = device_data['device_code']
            
            self.root.after(0, lambda c=user_code: self.code_label.config(text=c))
            self.root.after(0, lambda: self.status.config(text="Entre le code sur microsoft.com/link", 
                                                         fg=COLORS['accent_gold']))
            self.root.after(0, lambda: self.progress.set_progress(10))
            
            # Ouvrir le navigateur
            webbrowser.open('https://microsoft.com/link')
            
            # Poll pour le token
            self.root.after(0, lambda: self.status.config(text="En attente de connexion..."))
            token_data = self.auth.poll_for_token(device_code)
            
            self.root.after(0, lambda: self.progress.set_progress(30))
            self.root.after(0, lambda: self.status.config(text="Connexion Xbox Live..."))
            
            # Xbox Live
            xbox_data = self.auth.get_xbox_token(token_data['access_token'])
            xbox_token = xbox_data['Token']
            user_hash = xbox_data['DisplayClaims']['xui'][0]['uhs']
            
            self.root.after(0, lambda: self.progress.set_progress(50))
            self.root.after(0, lambda: self.status.config(text="Verification XSTS..."))
            
            # XSTS
            xsts_data = self.auth.get_xsts_token(xbox_token)
            xsts_token = xsts_data['Token']
            
            self.root.after(0, lambda: self.progress.set_progress(70))
            self.root.after(0, lambda: self.status.config(text="Connexion Minecraft..."))
            
            # Minecraft token
            mc_data = self.auth.get_minecraft_token(xsts_token, user_hash)
            mc_token = mc_data['access_token']
            
            self.root.after(0, lambda: self.progress.set_progress(85))
            self.root.after(0, lambda: self.status.config(text="Verification licence..."))
            
            # Verifier possession
            if not self.auth.check_game_ownership(mc_token):
                raise Exception("Tu ne possedes pas Minecraft!")
            
            # Profil
            profile = self.auth.get_profile(mc_token)
            
            self.root.after(0, lambda: self.progress.set_progress(100))
            
            # Sauvegarder
            auth_data = {
                'ms_access_token': token_data['access_token'],
                'ms_refresh_token': token_data.get('refresh_token', ''),
                'mc_access_token': mc_token,
                'mc_uuid': profile['id'],
                'mc_username': profile['name'],
                'auth_time': time.time()
            }
            
            with open(AUTH_FILE, 'w') as f:
                json.dump(auth_data, f)
            
            username = profile['name']
            self.root.after(0, lambda u=username: self._on_success(u, auth_data))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda m=error_msg: self._on_error(m))
    
    def _on_success(self, username, auth_data):
        self.status.config(text=f"Bienvenue {username}!", fg=COLORS['minecraft_green'])
        self.root.after(1500, lambda: self._finish(auth_data))
    
    def _finish(self, auth_data):
        self.root.destroy()
        self.on_success(auth_data)
    
    def _on_error(self, message):
        self.status.config(text=f"Erreur: {message}", fg=COLORS['accent_red'])
        self.login_btn.set_enabled(True)
        self.progress.set_progress(0)
    
    def run(self):
        self.root.mainloop()


# ============================================================
# SETUP WIZARD
# ============================================================

class SetupWizard:
    """Assistant de configuration initiale"""
    
    def __init__(self, on_complete: Callable):
        self.on_complete = on_complete
        self.config = DEFAULT_CONFIG.copy()
        
        self.root = tk.Tk()
        self.root.title("Illama Launcher - Configuration")
        self.root.geometry("550x550")
        self.root.minsize(500, 500)
        self.root.configure(bg=COLORS['bg_dark'])
        
        self.create_widgets()
    
    def create_widgets(self):
        main = tk.Frame(self.root, bg=COLORS['bg_dark'])
        main.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Titre
        tk.Label(main, text="Configuration", font=('Segoe UI', 24, 'bold'),
                bg=COLORS['bg_dark'], fg=COLORS['text_white']).pack(anchor='w')
        tk.Label(main, text=f"Serveur: {SERVER_ADDRESS}", font=('Segoe UI', 11),
                bg=COLORS['bg_dark'], fg=COLORS['minecraft_green']).pack(anchor='w', pady=(0, 20))
        
        # Version Minecraft
        frame1 = tk.Frame(main, bg=COLORS['bg_medium'], padx=15, pady=12)
        frame1.pack(fill='x', pady=(0, 10))
        
        tk.Label(frame1, text="Version Minecraft", font=('Segoe UI', 11, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        self.mc_var = tk.StringVar(value="1.20.1")
        mc_combo = ttk.Combobox(frame1, textvariable=self.mc_var, values=get_sorted_mc_versions(),
                               state='readonly', font=('Segoe UI', 11))
        mc_combo.pack(fill='x', pady=(5, 0))
        mc_combo.bind('<<ComboboxSelected>>', self.on_mc_change)
        
        # Version Forge
        frame2 = tk.Frame(main, bg=COLORS['bg_medium'], padx=15, pady=12)
        frame2.pack(fill='x', pady=(0, 10))
        
        tk.Label(frame2, text="Version Forge", font=('Segoe UI', 11, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        self.forge_info = tk.Label(frame2, text="Recommande: 47.4.1", font=('Segoe UI', 9),
                                  bg=COLORS['bg_medium'], fg=COLORS['minecraft_green'])
        self.forge_info.pack(anchor='w')
        
        self.forge_var = tk.StringVar(value="47.4.1")
        self.forge_combo = ttk.Combobox(frame2, textvariable=self.forge_var, state='readonly',
                                       font=('Segoe UI', 11))
        self.forge_combo.pack(fill='x', pady=(5, 0))
        self.update_forge()
        
        # RAM
        frame3 = tk.Frame(main, bg=COLORS['bg_medium'], padx=15, pady=12)
        frame3.pack(fill='x', pady=(0, 10))
        
        tk.Label(frame3, text="Memoire RAM", font=('Segoe UI', 11, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        ram_frame = tk.Frame(frame3, bg=COLORS['bg_medium'])
        ram_frame.pack(fill='x', pady=(5, 0))
        
        tk.Label(ram_frame, text="Min:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(side='left')
        self.ram_min = tk.Spinbox(ram_frame, from_=512, to=16384, increment=256, width=7, font=('Segoe UI', 10))
        self.ram_min.delete(0, 'end')
        # Convertir de MB à MB (déjà en MB maintenant)
        ram_min_default = self.config.get('ram_min', 2048)
        self.ram_min.insert(0, str(ram_min_default))
        self.ram_min.pack(side='left', padx=(5, 15))
        
        tk.Label(ram_frame, text="Max:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(side='left')
        self.ram_max = tk.Spinbox(ram_frame, from_=1024, to=32768, increment=256, width=7, font=('Segoe UI', 10))
        self.ram_max.delete(0, 'end')
        # Convertir de MB à MB (déjà en MB maintenant)
        ram_max_default = self.config.get('ram_max', 4096)
        self.ram_max.insert(0, str(ram_max_default))
        self.ram_max.pack(side='left', padx=5)
        
        tk.Label(ram_frame, text="MB", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(side='left')
        
        # Info
        info_frame = tk.Frame(main, bg=COLORS['bg_dark'])
        info_frame.pack(fill='x', pady=15)
        
        tk.Label(info_frame, text="Les mods seront synchronises automatiquement",
                font=('Segoe UI', 10), bg=COLORS['bg_dark'], fg=COLORS['text_gray']).pack()
        tk.Label(info_frame, text="Prism Launcher sera utilise pour lancer le jeu",
                font=('Segoe UI', 10), bg=COLORS['bg_dark'], fg=COLORS['text_gray']).pack()
        
        # Bouton
        self.start_btn = AnimatedButton(main, "COMMENCER", self.on_start,
                                       color='green', width=200, height=50)
        self.start_btn.pack(pady=20)
    
    def on_mc_change(self, event=None):
        self.update_forge()
    
    def update_forge(self):
        mc = self.mc_var.get()
        if mc in MINECRAFT_FORGE_VERSIONS:
            data = MINECRAFT_FORGE_VERSIONS[mc]
            self.forge_combo['values'] = data['versions']
            self.forge_var.set(data['recommended'])
            self.forge_info.config(text=f"Recommande: {data['recommended']}")
    
    def on_start(self):
        self.config['minecraft_version'] = self.mc_var.get()
        self.config['forge_version'] = self.forge_var.get()
        self.config['ram_min'] = int(self.ram_min.get())
        self.config['ram_max'] = int(self.ram_max.get())
        self.config['setup_completed'] = True
        
        self.root.destroy()
        self.on_complete(self.config)
    
    def run(self):
        self.root.mainloop()


# ============================================================
# LAUNCHER GUI PRINCIPAL
# ============================================================

class LauncherGUI:
    """Interface principale du launcher"""
    
    def __init__(self, config: dict = None):
        self.config = config if config else self.load_config()
        
        self.root = tk.Tk()
        self.root.title("Illama Launcher")
        
        # Restaurer la position et taille de la fenêtre
        window_geometry = self.config.get('window_geometry', None)
        if window_geometry:
            self.root.geometry(window_geometry)
        else:
            self.root.geometry("800x600")
        
        self.root.minsize(700, 500)
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Sauvegarder la position de la fenêtre quand elle bouge
        self.root.bind('<Configure>', self._on_window_configure)
        
        # Variables
        self.is_syncing = False
        self.sync_thread = None
        self.update_check_job = None  # Job de vérification périodique
        
        # System Tray
        self.tray = SystemTray(self.root, self.quit_app, self.show_window)
        if self.config.get('minimize_to_tray', True):
            self.tray.setup()
            self.tray.run()
        
        # Intercepter la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Style
        self.setup_style()
        
        # UI
        self.create_widgets()
        
        # Verifier les mises à jour EN PREMIER (avant tout)
        self.root.after(100, self.check_for_updates)
        
        # Démarrer la vérification périodique des mises à jour
        self.start_periodic_update_check()
        
        # Verifier Prism au demarrage (après la vérification de mise à jour)
        self.root.after(500, self.check_prism_status)
    
    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frames
        style.configure('TFrame', background=COLORS['bg_dark'])
        style.configure('Card.TFrame', background=COLORS['bg_medium'], relief='flat', borderwidth=1)
        style.configure('TLabel', background=COLORS['bg_dark'], foreground=COLORS['text_white'])
        
        # Notebook (onglets) avec style moderne
        style.configure('TNotebook', background=COLORS['bg_dark'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=COLORS['bg_medium'], 
                       foreground=COLORS['text_gray'],
                       padding=[20, 10], 
                       font=('Segoe UI', 11, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        style.map('TNotebook.Tab', 
                 background=[('selected', COLORS['accent_green']), ('active', COLORS['bg_hover'])],
                 foreground=[('selected', COLORS['text_white']), ('active', COLORS['text_white'])],
                 expand=[('selected', [1, 1, 1, 0])])
        
        # Combobox moderne
        style.configure('TCombobox', 
                       fieldbackground=COLORS['bg_light'], 
                       foreground=COLORS['text_white'], 
                       background=COLORS['bg_light'],
                       borderwidth=1,
                       relief='flat')
        style.map('TCombobox',
                 fieldbackground=[('readonly', COLORS['bg_light'])],
                 selectbackground=[('readonly', COLORS['accent_green'])],
                 selectforeground=[('readonly', COLORS['text_white'])])
        
        # Scrollbar moderne
        style.configure('TScrollbar',
                       background=COLORS['bg_medium'],
                       troughcolor=COLORS['bg_dark'],
                       borderwidth=0,
                       arrowcolor=COLORS['text_gray'],
                       darkcolor=COLORS['bg_medium'],
                       lightcolor=COLORS['bg_medium'])
        style.map('TScrollbar',
                 background=[('active', COLORS['accent_green'])],
                 arrowcolor=[('active', COLORS['text_white'])])
    
    def create_widgets(self):
        # Header avec dégradé moderne
        header = tk.Frame(self.root, bg=COLORS['bg_medium'], height=80, relief='flat')
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Ligne d'accent en haut
        accent_line = tk.Frame(self.root, bg=COLORS['accent_green'], height=3)
        accent_line.pack(fill='x', before=header)
        
        header_content = tk.Frame(header, bg=COLORS['bg_medium'])
        header_content.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Logo et titre avec effet moderne
        title_frame = tk.Frame(header_content, bg=COLORS['bg_medium'])
        title_frame.pack(side='left')
        
        # Titre avec ombre
        title_label = tk.Label(title_frame, text="ILLAMA", font=('Segoe UI', 28, 'bold'),
                              bg=COLORS['bg_medium'], fg=COLORS['accent_green'])
        title_label.pack(side='left')
        
        subtitle_label = tk.Label(title_frame, text="LAUNCHER", font=('Segoe UI', 13, 'bold'),
                                 bg=COLORS['bg_medium'], fg=COLORS['text_gray'])
        subtitle_label.pack(side='left', padx=(12, 0), pady=(10, 0))
        
        # Info user
        user_frame = tk.Frame(header_content, bg=COLORS['bg_medium'])
        user_frame.pack(side='right')
        
        username = self.config.get('mc_username', 'Joueur')
        tk.Label(user_frame, text=f"Connecte: {username}", font=('Segoe UI', 11),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='e')
        tk.Label(user_frame, text=f"Serveur: {SERVER_ADDRESS}", font=('Segoe UI', 9),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(anchor='e')
        
        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Onglets
        self.play_tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.settings_tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.minecraft_tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.advanced_tab = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        
        self.notebook.add(self.play_tab, text="  Jouer  ")
        self.notebook.add(self.settings_tab, text="  Parametres  ")
        self.notebook.add(self.minecraft_tab, text="  Minecraft  ")
        self.notebook.add(self.advanced_tab, text="  Avance  ")
        
        self.create_play_tab()
        self.create_settings_tab()
        self.create_minecraft_tab()
        self.create_advanced_tab()
    
    def create_play_tab(self):
        """Onglet principal pour jouer"""
        main = tk.Frame(self.play_tab, bg=COLORS['bg_dark'])
        main.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Info serveur
        server_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        server_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(server_frame, text=SERVER_NAME, font=('Segoe UI', 16, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        info_text = f"Minecraft {self.config.get('minecraft_version', '1.20.1')} + Forge {self.config.get('forge_version', '47.4.1')}"
        tk.Label(server_frame, text=info_text, font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(anchor='w')
        
        ram_mb = self.config.get('ram_max', 4096)
        ram_gb = ram_mb / 1024
        tk.Label(server_frame, text=f"RAM: {ram_mb} MB ({ram_gb:.1f} Go)", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(anchor='w')
        
        # Status Prism
        self.prism_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=10)
        self.prism_frame.pack(fill='x', pady=(0, 15))
        
        self.prism_status = tk.Label(self.prism_frame, text="Verification Prism Launcher...",
                                    font=('Segoe UI', 10), bg=COLORS['bg_medium'], fg=COLORS['text_gray'])
        self.prism_status.pack(side='left')
        
        self.install_prism_btn = AnimatedButton(self.prism_frame, "Installer Prism", 
                                                self.install_prism, color='gold', width=140, height=32)
        self.install_prism_btn.pack(side='right')
        self.install_prism_btn.pack_forget()  # Cache par defaut
        
        # Bouton JOUER
        play_frame = tk.Frame(main, bg=COLORS['bg_dark'])
        play_frame.pack(fill='x', pady=20)
        
        self.play_btn = AnimatedButton(play_frame, "JOUER", self.play_game,
                                       color='green', width=300, height=70)
        self.play_btn.pack()
        
        # Progress
        self.progress_frame = tk.Frame(main, bg=COLORS['bg_dark'])
        self.progress_frame.pack(fill='x', pady=(0, 10))
        
        self.status_label = tk.Label(self.progress_frame, text="Pret a jouer",
                                    font=('Segoe UI', 10), bg=COLORS['bg_dark'], fg=COLORS['text_gray'])
        self.status_label.pack()
        
        self.progress_bar = ProgressBarMC(self.progress_frame, width=400, height=20)
        self.progress_bar.pack(pady=5)
        
        # Log
        log_frame = tk.Frame(main, bg=COLORS['bg_medium'])
        log_frame.pack(fill='both', expand=True)
        
        tk.Label(log_frame, text="Journal", font=('Segoe UI', 10, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w', padx=10, pady=(10, 5))
        
        self.log_text = tk.Text(log_frame, height=8, bg=COLORS['bg_dark'], fg=COLORS['text_gray'],
                               font=('Consolas', 9), relief='flat', padx=10, pady=5)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Scrollbar pour le log
        scrollbar = ttk.Scrollbar(self.log_text, orient='vertical', command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log("Illama Launcher demarre")
    
    def create_settings_tab(self):
        """Onglet parametres"""
        scroll = ScrollableFrame(self.settings_tab)
        scroll.pack(fill='both', expand=True)
        
        main = scroll.scrollable_frame
        main.configure(style='TFrame')
        
        # RAM
        ram_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        ram_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        tk.Label(ram_frame, text="Memoire RAM", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        tk.Label(ram_frame, text="Recommande: 4096-8192 MB (4-8 Go)", font=('Segoe UI', 9),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(anchor='w')
        
        ram_controls = tk.Frame(ram_frame, bg=COLORS['bg_medium'])
        ram_controls.pack(fill='x', pady=(10, 0))
        
        tk.Label(ram_controls, text="Min:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        self.ram_min_spin = tk.Spinbox(ram_controls, from_=512, to=16384, increment=256, width=7, font=('Segoe UI', 10))
        self.ram_min_spin.delete(0, 'end')
        self.ram_min_spin.insert(0, str(self.config.get('ram_min', 2048)))
        self.ram_min_spin.pack(side='left', padx=(5, 20))
        
        tk.Label(ram_controls, text="Max:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        self.ram_max_spin = tk.Spinbox(ram_controls, from_=1024, to=32768, increment=256, width=7, font=('Segoe UI', 10))
        self.ram_max_spin.delete(0, 'end')
        self.ram_max_spin.insert(0, str(self.config.get('ram_max', 4096)))
        self.ram_max_spin.pack(side='left', padx=(5, 5))
        
        tk.Label(ram_controls, text="MB", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        # Resolution
        res_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        res_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(res_frame, text="Resolution", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        res_controls = tk.Frame(res_frame, bg=COLORS['bg_medium'])
        res_controls.pack(fill='x', pady=(10, 0))
        
        self.width_spin = tk.Spinbox(res_controls, from_=800, to=3840, width=6, font=('Segoe UI', 10))
        self.width_spin.delete(0, 'end')
        self.width_spin.insert(0, str(self.config.get('window_width', 854)))
        self.width_spin.pack(side='left')
        
        tk.Label(res_controls, text="x", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left', padx=5)
        
        self.height_spin = tk.Spinbox(res_controls, from_=600, to=2160, width=6, font=('Segoe UI', 10))
        self.height_spin.delete(0, 'end')
        self.height_spin.insert(0, str(self.config.get('window_height', 480)))
        self.height_spin.pack(side='left')
        
        # Presets
        presets_frame = tk.Frame(res_frame, bg=COLORS['bg_medium'])
        presets_frame.pack(fill='x', pady=(10, 0))
        
        presets = [("854x480", 854, 480), ("1280x720", 1280, 720), 
                   ("1920x1080", 1920, 1080), ("2560x1440", 2560, 1440)]
        
        for name, w, h in presets:
            btn = tk.Button(presets_frame, text=name, font=('Segoe UI', 9),
                           bg=COLORS['bg_light'], fg=COLORS['text_white'], relief='flat',
                           command=lambda w=w, h=h: self.set_resolution(w, h))
            btn.pack(side='left', padx=(0, 5))
        
        # Fullscreen
        self.fullscreen_var = tk.BooleanVar(value=self.config.get('fullscreen', False))
        fs_check = tk.Checkbutton(res_frame, text="Plein ecran", variable=self.fullscreen_var,
                                 bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                 selectcolor=COLORS['bg_dark'], activebackground=COLORS['bg_medium'],
                                 font=('Segoe UI', 10))
        fs_check.pack(anchor='w', pady=(10, 0))
        
        # Borderless (plein écran fenêtré)
        self.borderless_var = tk.BooleanVar(value=self.config.get('borderless', False))
        borderless_check = tk.Checkbutton(res_frame, text="Plein ecran fenetre (Borderless)", variable=self.borderless_var,
                                         bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                         selectcolor=COLORS['bg_dark'], activebackground=COLORS['bg_medium'],
                                         font=('Segoe UI', 10))
        borderless_check.pack(anchor='w', pady=(5, 0))
        
        # Info sur borderless
        borderless_info = tk.Label(res_frame, text="(Plein ecran sans bordure, permet Alt+Tab facile)", 
                                  font=('Segoe UI', 8), bg=COLORS['bg_medium'], fg=COLORS['text_gray'])
        borderless_info.pack(anchor='w', padx=(25, 0))
        
        # Désactiver fullscreen si borderless est activé et vice versa
        def on_fullscreen_change():
            if self.fullscreen_var.get():
                self.borderless_var.set(False)
        def on_borderless_change():
            if self.borderless_var.get():
                self.fullscreen_var.set(False)
        
        fs_check.config(command=on_fullscreen_change)
        borderless_check.config(command=on_borderless_change)
        
        # Options
        opt_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        opt_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(opt_frame, text="Options", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        self.auto_connect_var = tk.BooleanVar(value=self.config.get('auto_connect', True))
        tk.Checkbutton(opt_frame, text="Connexion auto au serveur", variable=self.auto_connect_var,
                      bg=COLORS['bg_medium'], fg=COLORS['text_white'], selectcolor=COLORS['bg_dark'],
                      font=('Segoe UI', 10)).pack(anchor='w', pady=(10, 0))
        
        self.minimize_tray_var = tk.BooleanVar(value=self.config.get('minimize_to_tray', True))
        tk.Checkbutton(opt_frame, text="Minimiser dans la barre des taches", variable=self.minimize_tray_var,
                      bg=COLORS['bg_medium'], fg=COLORS['text_white'], selectcolor=COLORS['bg_dark'],
                      font=('Segoe UI', 10)).pack(anchor='w')
        
        # Bouton sauvegarder
        save_btn = AnimatedButton(main, "Sauvegarder", self.save_settings,
                                 color='green', width=150, height=40)
        save_btn.pack(pady=20)
    
    def create_minecraft_tab(self):
        """Onglet pour gérer tous les paramètres Minecraft"""
        scroll = ScrollableFrame(self.minecraft_tab)
        scroll.pack(fill='both', expand=True)
        
        main = scroll.scrollable_frame
        
        # Charger les options Minecraft existantes
        minecraft_options = self.config.get('minecraft_options', {})
        
        # Section Graphiques
        graphics_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        graphics_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        tk.Label(graphics_frame, text="Graphiques", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        # Qualité graphique
        quality_frame = tk.Frame(graphics_frame, bg=COLORS['bg_medium'])
        quality_frame.pack(fill='x', pady=(10, 5))
        
        tk.Label(quality_frame, text="Qualite graphique:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.graphics_var = tk.StringVar(value=minecraft_options.get('graphics', 'fancy'))
        graphics_combo = ttk.Combobox(quality_frame, textvariable=self.graphics_var,
                                     values=['fast', 'fancy'], state='readonly', width=10)
        graphics_combo.pack(side='left', padx=(10, 0))
        
        # Distance de rendu
        render_frame = tk.Frame(graphics_frame, bg=COLORS['bg_medium'])
        render_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(render_frame, text="Distance de rendu:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.render_distance_var = tk.StringVar(value=str(minecraft_options.get('renderDistance', '12')))
        render_spin = tk.Spinbox(render_frame, from_=2, to=32, width=5, textvariable=self.render_distance_var)
        render_spin.pack(side='left', padx=(10, 0))
        
        tk.Label(render_frame, text="chunks", font=('Segoe UI', 9),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(side='left', padx=(5, 0))
        
        # Distance d'entités
        entity_dist_frame = tk.Frame(graphics_frame, bg=COLORS['bg_medium'])
        entity_dist_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(entity_dist_frame, text="Distance entites:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.entity_distance_var = tk.DoubleVar(value=float(minecraft_options.get('entityDistanceScaling', 1.0)))
        entity_dist_scale = tk.Scale(entity_dist_frame, from_=0.5, to=5.0, resolution=0.1,
                                     orient='horizontal', variable=self.entity_distance_var,
                                     bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                     length=200, showvalue=True)
        entity_dist_scale.pack(side='left', padx=(10, 0))
        
        # Particules
        particles_frame = tk.Frame(graphics_frame, bg=COLORS['bg_medium'])
        particles_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(particles_frame, text="Particules:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.particles_var = tk.StringVar(value=minecraft_options.get('particles', 'all'))
        particles_combo = ttk.Combobox(particles_frame, textvariable=self.particles_var,
                                      values=['all', 'decreased', 'minimal'], state='readonly', width=12)
        particles_combo.pack(side='left', padx=(10, 0))
        
        # FPS Max
        fps_frame = tk.Frame(graphics_frame, bg=COLORS['bg_medium'])
        fps_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(fps_frame, text="FPS Maximum:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.max_fps_var = tk.StringVar(value=str(minecraft_options.get('maxFps', '120')))
        fps_spin = tk.Spinbox(fps_frame, from_=10, to=260, increment=10, width=5, textvariable=self.max_fps_var)
        fps_spin.pack(side='left', padx=(10, 0))
        
        # VSync
        self.vsync_var = tk.BooleanVar(value=minecraft_options.get('vsync', False))
        vsync_check = tk.Checkbutton(graphics_frame, text="VSync", variable=self.vsync_var,
                                    bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                    selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        vsync_check.pack(anchor='w', pady=(5, 0))
        
        # Ombres d'entités
        self.entity_shadows_var = tk.BooleanVar(value=minecraft_options.get('entityShadows', True))
        entity_shadows_check = tk.Checkbutton(graphics_frame, text="Ombres des entites", variable=self.entity_shadows_var,
                                             bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                             selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        entity_shadows_check.pack(anchor='w', pady=(5, 0))
        
        # VBO
        self.use_vbo_var = tk.BooleanVar(value=minecraft_options.get('useVbo', True))
        vbo_check = tk.Checkbutton(graphics_frame, text="Utiliser VBO (amelioration performance)", variable=self.use_vbo_var,
                                  bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                  selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        vbo_check.pack(anchor='w', pady=(5, 0))
        
        # Section Rendu Avancé
        render_adv_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        render_adv_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(render_adv_frame, text="Rendu Avance", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        # Ombrage ambiant (AO)
        ao_frame = tk.Frame(render_adv_frame, bg=COLORS['bg_medium'])
        ao_frame.pack(fill='x', pady=(10, 5))
        
        tk.Label(ao_frame, text="Ombrage ambiant (AO):", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.ao_var = tk.StringVar(value=minecraft_options.get('ao', 'max'))
        ao_combo = ttk.Combobox(ao_frame, textvariable=self.ao_var,
                               values=['off', 'min', 'max'], state='readonly', width=10)
        ao_combo.pack(side='left', padx=(10, 0))
        
        # Éclairage lisse
        self.smooth_lighting_var = tk.StringVar(value=minecraft_options.get('smoothLighting', 'maximum'))
        smooth_light_frame = tk.Frame(render_adv_frame, bg=COLORS['bg_medium'])
        smooth_light_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(smooth_light_frame, text="Eclairage lisse:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        smooth_light_combo = ttk.Combobox(smooth_light_frame, textvariable=self.smooth_lighting_var,
                                         values=['off', 'minimum', 'maximum'], state='readonly', width=12)
        smooth_light_combo.pack(side='left', padx=(10, 0))
        
        # Luminosité
        gamma_frame = tk.Frame(render_adv_frame, bg=COLORS['bg_medium'])
        gamma_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(gamma_frame, text="Luminosite (Gamma):", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.gamma_var = tk.DoubleVar(value=float(minecraft_options.get('gamma', 1.0)))
        gamma_scale = tk.Scale(gamma_frame, from_=0.0, to=1.0, resolution=0.01,
                              orient='horizontal', variable=self.gamma_var,
                              bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                              length=200, showvalue=True)
        gamma_scale.pack(side='left', padx=(10, 0))
        
        # Niveaux de mipmap
        mipmap_frame = tk.Frame(render_adv_frame, bg=COLORS['bg_medium'])
        mipmap_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(mipmap_frame, text="Niveaux Mipmap:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.mipmap_levels_var = tk.StringVar(value=str(minecraft_options.get('mipmapLevels', '4')))
        mipmap_spin = tk.Spinbox(mipmap_frame, from_=0, to=4, width=5, textvariable=self.mipmap_levels_var)
        mipmap_spin.pack(side='left', padx=(10, 0))
        
        # Filtrage anisotropique
        aniso_frame = tk.Frame(render_adv_frame, bg=COLORS['bg_medium'])
        aniso_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(aniso_frame, text="Filtrage anisotropique:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.anisotropic_filtering_var = tk.StringVar(value=str(minecraft_options.get('anisotropicFiltering', '1')))
        aniso_spin = tk.Spinbox(aniso_frame, from_=1, to=16, width=5, textvariable=self.anisotropic_filtering_var)
        aniso_spin.pack(side='left', padx=(10, 0))
        
        # Blend de biome
        biome_frame = tk.Frame(render_adv_frame, bg=COLORS['bg_medium'])
        biome_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(biome_frame, text="Blend de biome:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.biome_blend_var = tk.StringVar(value=str(minecraft_options.get('biomeBlendRadius', '2')))
        biome_spin = tk.Spinbox(biome_frame, from_=0, to=7, width=5, textvariable=self.biome_blend_var)
        biome_spin.pack(side='left', padx=(10, 0))
        
        # Nuages
        self.clouds_var = tk.StringVar(value=minecraft_options.get('renderClouds', 'default'))
        clouds_frame = tk.Frame(render_adv_frame, bg=COLORS['bg_medium'])
        clouds_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(clouds_frame, text="Nuages:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        clouds_combo = ttk.Combobox(clouds_frame, textvariable=self.clouds_var,
                                   values=['off', 'fast', 'fancy', 'default'], state='readonly', width=12)
        clouds_combo.pack(side='left', padx=(10, 0))
        
        # Ciel
        self.sky_var = tk.BooleanVar(value=minecraft_options.get('renderSky', True))
        sky_check = tk.Checkbutton(render_adv_frame, text="Afficher le ciel", variable=self.sky_var,
                                  bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                  selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        sky_check.pack(anchor='w', pady=(5, 0))
        
        # Étoiles
        self.stars_var = tk.BooleanVar(value=minecraft_options.get('renderStars', True))
        stars_check = tk.Checkbutton(render_adv_frame, text="Afficher les etoiles", variable=self.stars_var,
                                    bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                    selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        stars_check.pack(anchor='w', pady=(5, 0))
        
        # Soleil et lune
        self.sun_moon_var = tk.BooleanVar(value=minecraft_options.get('renderSunMoon', True))
        sun_moon_check = tk.Checkbutton(render_adv_frame, text="Afficher soleil/lune", variable=self.sun_moon_var,
                                       bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                       selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        sun_moon_check.pack(anchor='w', pady=(5, 0))
        
        # Section Performance
        perf_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        perf_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(perf_frame, text="Performance", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        # Threads de chunks
        chunk_threads_frame = tk.Frame(perf_frame, bg=COLORS['bg_medium'])
        chunk_threads_frame.pack(fill='x', pady=(10, 5))
        
        tk.Label(chunk_threads_frame, text="Threads de chunks:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.chunk_threads_var = tk.StringVar(value=str(minecraft_options.get('chunkUpdateThreads', '1')))
        chunk_threads_spin = tk.Spinbox(chunk_threads_frame, from_=1, to=8, width=5, textvariable=self.chunk_threads_var)
        chunk_threads_spin.pack(side='left', padx=(10, 0))
        
        # Priorité des chunks
        self.prioritize_chunks_var = tk.BooleanVar(value=minecraft_options.get('prioritizeChunkUpdates', True))
        prioritize_check = tk.Checkbutton(perf_frame, text="Prioriser les mises a jour de chunks", variable=self.prioritize_chunks_var,
                                         bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                         selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        prioritize_check.pack(anchor='w', pady=(5, 0))
        
        # Animations
        self.animate_only_var = tk.BooleanVar(value=minecraft_options.get('animateOnlyVisibleTextures', False))
        animate_check = tk.Checkbutton(perf_frame, text="Animer uniquement les textures visibles", variable=self.animate_only_var,
                                      bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                      selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        animate_check.pack(anchor='w', pady=(5, 0))
        
        # Section Audio
        audio_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        audio_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(audio_frame, text="Audio", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        # Volume général
        sound_frame = tk.Frame(audio_frame, bg=COLORS['bg_medium'])
        sound_frame.pack(fill='x', pady=(10, 5))
        
        tk.Label(sound_frame, text="Volume general:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.sound_var = tk.DoubleVar(value=float(minecraft_options.get('sound', 1.0)))
        sound_scale = tk.Scale(sound_frame, from_=0.0, to=1.0, resolution=0.01,
                              orient='horizontal', variable=self.sound_var,
                              bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                              length=200, showvalue=True)
        sound_scale.pack(side='left', padx=(10, 0))
        
        # Musique
        music_frame = tk.Frame(audio_frame, bg=COLORS['bg_medium'])
        music_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(music_frame, text="Volume musique:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.music_var = tk.DoubleVar(value=float(minecraft_options.get('music', 1.0)))
        music_scale = tk.Scale(music_frame, from_=0.0, to=1.0, resolution=0.01,
                              orient='horizontal', variable=self.music_var,
                              bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                              length=200, showvalue=True)
        music_scale.pack(side='left', padx=(10, 0))
        
        # Section Contrôles
        controls_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        controls_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(controls_frame, text="Controles", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        # Sensibilité souris
        sens_frame = tk.Frame(controls_frame, bg=COLORS['bg_medium'])
        sens_frame.pack(fill='x', pady=(10, 5))
        
        tk.Label(sens_frame, text="Sensibilite souris:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.sensitivity_var = tk.DoubleVar(value=float(minecraft_options.get('sensitivity', 0.5)))
        sens_scale = tk.Scale(sens_frame, from_=0.0, to=1.0, resolution=0.01,
                             orient='horizontal', variable=self.sensitivity_var,
                             bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                             length=200, showvalue=True)
        sens_scale.pack(side='left', padx=(10, 0))
        
        # Inverser Y
        self.invert_y_var = tk.BooleanVar(value=minecraft_options.get('invertYMouse', False))
        invert_check = tk.Checkbutton(controls_frame, text="Inverser axe Y de la souris", variable=self.invert_y_var,
                                     bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                     selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        invert_check.pack(anchor='w', pady=(5, 0))
        
        # Auto-saut
        self.auto_jump_var = tk.BooleanVar(value=minecraft_options.get('autoJump', True))
        autojump_check = tk.Checkbutton(controls_frame, text="Saut automatique", variable=self.auto_jump_var,
                                       bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                       selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        autojump_check.pack(anchor='w', pady=(5, 0))
        
        # Section Interface
        interface_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        interface_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(interface_frame, text="Interface", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        # Échelle GUI
        gui_frame = tk.Frame(interface_frame, bg=COLORS['bg_medium'])
        gui_frame.pack(fill='x', pady=(10, 5))
        
        tk.Label(gui_frame, text="Echelle interface:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.gui_scale_var = tk.StringVar(value=str(minecraft_options.get('guiScale', '2')))
        gui_combo = ttk.Combobox(gui_frame, textvariable=self.gui_scale_var,
                                values=['0', '1', '2', '3', '4', 'auto'], state='readonly', width=8)
        gui_combo.pack(side='left', padx=(10, 0))
        
        # FOV
        fov_frame = tk.Frame(interface_frame, bg=COLORS['bg_medium'])
        fov_frame.pack(fill='x', pady=(5, 5))
        
        tk.Label(fov_frame, text="Champ de vision (FOV):", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.fov_var = tk.StringVar(value=str(minecraft_options.get('fov', '70.0')))
        fov_spin = tk.Spinbox(fov_frame, from_=30, to=110, increment=5, width=5, textvariable=self.fov_var)
        fov_spin.pack(side='left', padx=(10, 0))
        
        # Bobbing
        self.bobbing_var = tk.BooleanVar(value=minecraft_options.get('bobbing', True))
        bobbing_check = tk.Checkbutton(interface_frame, text="Balancement de la vue (Bobbing)", variable=self.bobbing_var,
                                      bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                      selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        bobbing_check.pack(anchor='w', pady=(5, 0))
        
        # Section Chat
        chat_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        chat_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(chat_frame, text="Chat", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        # Opacité chat
        chat_opacity_frame = tk.Frame(chat_frame, bg=COLORS['bg_medium'])
        chat_opacity_frame.pack(fill='x', pady=(10, 5))
        
        tk.Label(chat_opacity_frame, text="Opacite chat:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.chat_opacity_var = tk.DoubleVar(value=float(minecraft_options.get('chatOpacity', 1.0)))
        chat_opacity_scale = tk.Scale(chat_opacity_frame, from_=0.0, to=1.0, resolution=0.01,
                                     orient='horizontal', variable=self.chat_opacity_var,
                                     bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                     length=200, showvalue=True)
        chat_opacity_scale.pack(side='left', padx=(10, 0))
        
        # Couleurs chat
        self.chat_colors_var = tk.BooleanVar(value=minecraft_options.get('chatColors', True))
        chat_colors_check = tk.Checkbutton(chat_frame, text="Couleurs dans le chat", variable=self.chat_colors_var,
                                           bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                           selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        chat_colors_check.pack(anchor='w', pady=(5, 0))
        
        # Section Resource Packs et Shaders
        packs_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        packs_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(packs_frame, text="Resource Packs & Shaders", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        tk.Label(packs_frame, text="Ajoute tes propres resource packs et shaders en uploadant des fichiers ZIP",
                font=('Segoe UI', 9), bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(anchor='w', pady=(5, 15))
        
        packs_buttons = tk.Frame(packs_frame, bg=COLORS['bg_medium'])
        packs_buttons.pack(fill='x', pady=(0, 10))
        
        # Bouton Resource Packs
        resourcepack_btn = AnimatedButton(packs_buttons, "Ajouter Resource Pack", 
                                         lambda: self.upload_resourcepack(), 
                                         color='blue', width=180, height=35)
        resourcepack_btn.pack(side='left', padx=(0, 10))
        
        # Bouton Shaders
        shader_btn = AnimatedButton(packs_buttons, "Ajouter Shader", 
                                   lambda: self.upload_shader(), 
                                   color='purple', width=180, height=35)
        shader_btn.pack(side='left', padx=(0, 10))
        
        # Bouton Ouvrir dossiers
        open_folders_btn = AnimatedButton(packs_buttons, "Ouvrir Dossiers", 
                                         lambda: self.open_packs_folders(), 
                                         color='gray', width=150, height=35)
        open_folders_btn.pack(side='left')
        
        # Liste des packs installés
        packs_list_frame = tk.Frame(packs_frame, bg=COLORS['bg_medium'])
        packs_list_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        tk.Label(packs_list_frame, text="Packs installes:", font=('Segoe UI', 10, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        # Frame scrollable pour la liste
        packs_list_scroll = tk.Frame(packs_list_frame, bg=COLORS['bg_dark'], relief='flat', bd=1)
        packs_list_scroll.pack(fill='both', expand=True, pady=(5, 0))
        
        self.packs_listbox = tk.Listbox(packs_list_scroll, bg=COLORS['bg_dark'], fg=COLORS['text_white'],
                                        selectbackground=COLORS['accent_blue'], selectforeground=COLORS['text_white'],
                                        font=('Segoe UI', 9), height=6, relief='flat', bd=0)
        self.packs_listbox.pack(fill='both', expand=True, side='left')
        
        packs_scrollbar = tk.Scrollbar(packs_list_scroll, orient='vertical', command=self.packs_listbox.yview)
        packs_scrollbar.pack(side='right', fill='y')
        self.packs_listbox.config(yscrollcommand=packs_scrollbar.set)
        
        # Bouton supprimer
        delete_pack_btn = AnimatedButton(packs_list_frame, "Supprimer Selection", 
                                         lambda: self.delete_selected_pack(), 
                                         color='red', width=160, height=30)
        delete_pack_btn.pack(pady=(10, 0))
        
        # Charger la liste des packs
        self.root.after(100, self.refresh_packs_list)
        
        # Section Autres
        other_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        other_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(other_frame, text="Autres", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        # Difficulté
        diff_frame = tk.Frame(other_frame, bg=COLORS['bg_medium'])
        diff_frame.pack(fill='x', pady=(10, 5))
        
        tk.Label(diff_frame, text="Difficulte:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.difficulty_var = tk.StringVar(value=minecraft_options.get('difficulty', 'normal'))
        diff_combo = ttk.Combobox(diff_frame, textvariable=self.difficulty_var,
                                 values=['peaceful', 'easy', 'normal', 'hard'], state='readonly', width=12)
        diff_combo.pack(side='left', padx=(10, 0))
        
        # Sous-titres
        self.subtitles_var = tk.BooleanVar(value=minecraft_options.get('showSubtitles', False))
        subtitles_check = tk.Checkbutton(other_frame, text="Afficher les sous-titres", variable=self.subtitles_var,
                                         bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                         selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        subtitles_check.pack(anchor='w', pady=(5, 0))
        
        # Debug réduit
        self.reduced_debug_var = tk.BooleanVar(value=minecraft_options.get('reducedDebugInfo', False))
        debug_check = tk.Checkbutton(other_frame, text="Info debug reduite (F3)", variable=self.reduced_debug_var,
                                    bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                                    selectcolor=COLORS['bg_dark'], font=('Segoe UI', 10))
        debug_check.pack(anchor='w', pady=(5, 0))
        
        # Bouton sauvegarder
        save_mc_btn = AnimatedButton(main, "Sauvegarder les parametres Minecraft", self.save_minecraft_settings,
                                    color='green', width=250, height=40)
        save_mc_btn.pack(pady=20)
    
    def upload_resourcepack(self):
        """Ouvre un dialogue pour uploader un resource pack"""
        try:
            launcher = MinecraftLauncher(self.config)
            resourcepacks_dir = launcher.get_resourcepacks_dir()
            resourcepacks_dir.mkdir(parents=True, exist_ok=True)
            
            # Ouvrir le dialogue de sélection de fichier
            file_path = filedialog.askopenfilename(
                title="Selectionner un Resource Pack (ZIP)",
                filetypes=[("Fichiers ZIP", "*.zip"), ("Tous les fichiers", "*.*")]
            )
            
            if file_path:
                file_name = Path(file_path).name
                dest_path = resourcepacks_dir / file_name
                
                # Copier le fichier
                shutil.copy2(file_path, dest_path)
                
                self.log(f"Resource pack ajoute: {file_name}")
                messagebox.showinfo("Succes", f"Resource pack '{file_name}' ajoute avec succes!")
                
                # Rafraîchir la liste
                self.refresh_packs_list()
        except Exception as e:
            self.log(f"Erreur upload resource pack: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ajouter le resource pack:\n{e}")
    
    def upload_shader(self):
        """Ouvre un dialogue pour uploader un shader"""
        try:
            launcher = MinecraftLauncher(self.config)
            shaderpacks_dir = launcher.get_shaderpacks_dir()
            shaderpacks_dir.mkdir(parents=True, exist_ok=True)
            
            # Ouvrir le dialogue de sélection de fichier
            file_path = filedialog.askopenfilename(
                title="Selectionner un Shader (ZIP)",
                filetypes=[("Fichiers ZIP", "*.zip"), ("Tous les fichiers", "*.*")]
            )
            
            if file_path:
                file_name = Path(file_path).name
                dest_path = shaderpacks_dir / file_name
                
                # Copier le fichier
                shutil.copy2(file_path, dest_path)
                
                self.log(f"Shader ajoute: {file_name}")
                messagebox.showinfo("Succes", f"Shader '{file_name}' ajoute avec succes!")
                
                # Rafraîchir la liste
                self.refresh_packs_list()
        except Exception as e:
            self.log(f"Erreur upload shader: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ajouter le shader:\n{e}")
    
    def open_packs_folders(self):
        """Ouvre les dossiers resourcepacks et shaderpacks dans l'explorateur"""
        try:
            launcher = MinecraftLauncher(self.config)
            resourcepacks_dir = launcher.get_resourcepacks_dir()
            shaderpacks_dir = launcher.get_shaderpacks_dir()
            
            # Créer les dossiers s'ils n'existent pas
            resourcepacks_dir.mkdir(parents=True, exist_ok=True)
            shaderpacks_dir.mkdir(parents=True, exist_ok=True)
            
            # Ouvrir les dossiers
            if sys.platform == 'win32':
                os.startfile(str(resourcepacks_dir))
                os.startfile(str(shaderpacks_dir))
            elif sys.platform == 'darwin':
                os.system(f'open "{resourcepacks_dir}"')
                os.system(f'open "{shaderpacks_dir}"')
            else:
                os.system(f'xdg-open "{resourcepacks_dir}"')
                os.system(f'xdg-open "{shaderpacks_dir}"')
            
            self.log("Dossiers resourcepacks et shaderpacks ouverts")
        except Exception as e:
            self.log(f"Erreur ouverture dossiers: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir les dossiers:\n{e}")
    
    def refresh_packs_list(self):
        """Rafraîchit la liste des resource packs et shaders installés"""
        try:
            if not hasattr(self, 'packs_listbox'):
                return
            
            self.packs_listbox.delete(0, tk.END)
            
            launcher = MinecraftLauncher(self.config)
            resourcepacks_dir = launcher.get_resourcepacks_dir()
            shaderpacks_dir = launcher.get_shaderpacks_dir()
            
            # Ajouter les resource packs
            if resourcepacks_dir.exists():
                for pack_file in resourcepacks_dir.glob('*.zip'):
                    self.packs_listbox.insert(tk.END, f"📦 Resource Pack: {pack_file.name}")
            
            # Ajouter les shaders
            if shaderpacks_dir.exists():
                for shader_file in shaderpacks_dir.glob('*.zip'):
                    self.packs_listbox.insert(tk.END, f"✨ Shader: {shader_file.name}")
            
            if self.packs_listbox.size() == 0:
                self.packs_listbox.insert(tk.END, "Aucun pack installe")
        except Exception as e:
            self.log(f"Erreur rafraîchissement liste packs: {e}")
    
    def delete_selected_pack(self):
        """Supprime le pack sélectionné dans la liste"""
        try:
            selection = self.packs_listbox.curselection()
            if not selection:
                messagebox.showwarning("Aucune selection", "Selectionne un pack a supprimer")
                return
            
            selected_text = self.packs_listbox.get(selection[0])
            
            # Extraire le nom du fichier
            if "Resource Pack:" in selected_text:
                file_name = selected_text.split("Resource Pack: ")[1].strip()
                pack_type = "resource pack"
                launcher = MinecraftLauncher(self.config)
                file_path = launcher.get_resourcepacks_dir() / file_name
            elif "Shader:" in selected_text:
                file_name = selected_text.split("Shader: ")[1].strip()
                pack_type = "shader"
                launcher = MinecraftLauncher(self.config)
                file_path = launcher.get_shaderpacks_dir() / file_name
            else:
                messagebox.showwarning("Erreur", "Impossible de determiner le type de pack")
                return
            
            # Confirmer la suppression
            if messagebox.askyesno("Confirmation", f"Supprimer le {pack_type} '{file_name}' ?"):
                if file_path.exists():
                    file_path.unlink()
                    self.log(f"{pack_type.capitalize()} supprime: {file_name}")
                    messagebox.showinfo("Succes", f"{pack_type.capitalize()} supprime avec succes!")
                    self.refresh_packs_list()
                else:
                    messagebox.showerror("Erreur", "Le fichier n'existe plus")
        except Exception as e:
            self.log(f"Erreur suppression pack: {e}")
            messagebox.showerror("Erreur", f"Impossible de supprimer le pack:\n{e}")
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """Compare deux versions (format X.Y.Z)
        Retourne: -1 si v1 < v2, 0 si v1 == v2, 1 si v1 > v2"""
        def version_tuple(v):
            return tuple(map(int, (v.split("."))))
        
        try:
            t1 = version_tuple(v1)
            t2 = version_tuple(v2)
            if t1 < t2:
                return -1
            elif t1 > t2:
                return 1
            return 0
        except:
            return 0
    
    def check_for_updates(self, silent: bool = False):
        """Vérifie les mises à jour disponibles sur GitHub"""
        def check():
            try:
                self.root.after(0, lambda: self.log("Verification des mises a jour..."))
                
                # Vérifier la version minimale requise
                if self.compare_versions(LAUNCHER_VERSION, MIN_REQUIRED_VERSION) < 0:
                    self.root.after(0, lambda: self._force_update_dialog(
                        f"Version minimale requise: {MIN_REQUIRED_VERSION}\n"
                        f"Votre version: {LAUNCHER_VERSION}\n\n"
                        "Une mise a jour est obligatoire pour continuer."
                    ))
                    return
                
                # Récupérer la dernière release depuis GitHub
                headers = {'User-Agent': 'IllamaLauncher/1.0'}
                # Ajouter le token GitHub si fourni (pour repos privés)
                if GITHUB_TOKEN:
                    headers['Authorization'] = f'token {GITHUB_TOKEN}'
                
                req = urllib.request.Request(
                    GITHUB_RELEASES_URL,
                    headers=headers
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    
                    latest_version = data.get('tag_name', '').lstrip('v')
                    download_url = None
                    installer_url = None
                    
                    # Chercher l'asset .exe (priorité à l'installateur)
                    for asset in data.get('assets', []):
                        name = asset.get('name', '')
                        url = asset.get('browser_download_url', '')
                        if name.endswith('.exe'):
                            if 'Setup' in name or 'Installer' in name or 'Setup' in name.lower():
                                installer_url = url  # Installateur prioritaire
                            else:
                                download_url = url  # Autre .exe en fallback
                        elif name.endswith('.zip') and not download_url:
                            download_url = url
                    
                    # Utiliser l'installateur si trouvé, sinon l'URL de téléchargement
                    final_url = installer_url if installer_url else download_url
                    
                    if not final_url:
                        # Si pas d'asset, construire l'URL par défaut
                        final_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest/download/IllamaLauncher_Setup.exe"
                    
                    # Comparer les versions
                    if self.compare_versions(LAUNCHER_VERSION, latest_version) < 0:
                        # Mise à jour disponible
                        self.root.after(0, lambda: self._show_update_dialog(
                            latest_version, 
                            data.get('body', ''),
                            final_url
                        ))
                    else:
                        if not silent:
                            self.root.after(0, lambda: self.log(f"Launcher a jour (v{LAUNCHER_VERSION})"))
            
            except urllib.error.URLError as e:
                if not silent:
                    self.root.after(0, lambda: self.log(f"Impossible de verifier les mises a jour: {e}"))
            except Exception as e:
                if not silent:
                    self.root.after(0, lambda: self.log(f"Erreur verification mises a jour: {e}"))
        
        threading.Thread(target=check, daemon=True).start()
    
    def start_periodic_update_check(self):
        """Démarre la vérification périodique des mises à jour"""
        interval_minutes = self.config.get('update_check_interval', 60)
        
        # Si l'intervalle est 0 ou négatif, ne pas démarrer
        if interval_minutes <= 0:
            return
        
        interval_ms = interval_minutes * 60 * 1000  # Convertir en millisecondes
        
        def schedule_next():
            if self.update_check_job is not None:
                self.root.after_cancel(self.update_check_job)
            
            # Vérifier l'intervalle actuel (peut avoir changé)
            current_interval = self.config.get('update_check_interval', 60)
            if current_interval <= 0:
                self.update_check_job = None
                return
            
            # Vérifier silencieusement (sans afficher de dialogue si pas de mise à jour)
            self.update_check_job = self.root.after(current_interval * 60 * 1000, lambda: (
                self.check_for_updates(silent=True),
                schedule_next()  # Programmer la prochaine vérification
            ))
        
        # Programmer la première vérification périodique
        schedule_next()
    
    def stop_periodic_update_check(self):
        """Arrête la vérification périodique des mises à jour"""
        if self.update_check_job is not None:
            self.root.after_cancel(self.update_check_job)
            self.update_check_job = None
    
    def _force_update_dialog(self, message: str):
        """Affiche un dialogue obligatoire pour forcer la mise à jour"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Mise a jour obligatoire")
        dialog.geometry("500x300")
        dialog.configure(bg=COLORS['bg_dark'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"500x300+{x}+{y}")
        
        main = tk.Frame(dialog, bg=COLORS['bg_dark'], padx=30, pady=30)
        main.pack(fill='both', expand=True)
        
        # Icône d'alerte
        tk.Label(main, text="⚠️", font=('Segoe UI', 48),
                bg=COLORS['bg_dark'], fg=COLORS['accent_red']).pack(pady=(0, 20))
        
        # Message
        tk.Label(main, text="Mise a jour obligatoire", 
                font=('Segoe UI', 18, 'bold'),
                bg=COLORS['bg_dark'], fg=COLORS['text_white']).pack(pady=(0, 15))
        
        tk.Label(main, text=message, 
                font=('Segoe UI', 10),
                bg=COLORS['bg_dark'], fg=COLORS['text_gray'],
                justify='left', wraplength=440).pack(pady=(0, 20))
        
        # Boutons
        btn_frame = tk.Frame(main, bg=COLORS['bg_dark'])
        btn_frame.pack()
        
        def download_update():
            dialog.destroy()
            webbrowser.open(f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest")
            self.root.after(1000, self.root.quit)
        
        def auto_update():
            dialog.destroy()
            self._download_and_install_update(f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest/download/IllamaLauncher_Setup.exe")
        
        AnimatedButton(btn_frame, "Mettre a jour automatiquement", auto_update,
                      color='green', width=220, height=40).pack(side='left', padx=5)
        
        AnimatedButton(btn_frame, "Telecharger manuellement", download_update,
                      color='blue', width=200, height=40).pack(side='left', padx=5)
        
        AnimatedButton(btn_frame, "Quitter", lambda: self.root.quit(),
                      color='red', width=120, height=40).pack(side='left', padx=5)
    
    def _show_update_dialog(self, version: str, release_notes: str, download_url: str):
        """Affiche un dialogue pour proposer la mise à jour"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Mise a jour disponible")
        dialog.geometry("550x400")
        dialog.configure(bg=COLORS['bg_dark'])
        dialog.transient(self.root)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"550x400+{x}+{y}")
        
        main = tk.Frame(dialog, bg=COLORS['bg_dark'], padx=30, pady=20)
        main.pack(fill='both', expand=True)
        
        # Titre
        tk.Label(main, text="✨ Mise a jour disponible", 
                font=('Segoe UI', 18, 'bold'),
                bg=COLORS['bg_dark'], fg=COLORS['accent_gold']).pack(pady=(0, 10))
        
        version_text = f"Version actuelle: {LAUNCHER_VERSION} → Nouvelle version: {version}"
        tk.Label(main, text=version_text, 
                font=('Segoe UI', 11),
                bg=COLORS['bg_dark'], fg=COLORS['text_white']).pack(pady=(0, 15))
        
        # Notes de version
        notes_frame = tk.Frame(main, bg=COLORS['bg_medium'], relief='flat', bd=1)
        notes_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        tk.Label(notes_frame, text="Notes de version:", 
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w', padx=10, pady=(10, 5))
        
        notes_text = release_notes[:500] + "..." if len(release_notes) > 500 else release_notes
        notes_label = tk.Label(notes_frame, text=notes_text, 
                              font=('Segoe UI', 9),
                              bg=COLORS['bg_medium'], fg=COLORS['text_gray'],
                              justify='left', wraplength=480, anchor='nw')
        notes_label.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Boutons
        btn_frame = tk.Frame(main, bg=COLORS['bg_dark'])
        btn_frame.pack()
        
        def download_update():
            dialog.destroy()
            webbrowser.open(download_url if download_url else 
                          f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest")
            self.log("Redirection vers la page de telechargement")
        
        def auto_update():
            dialog.destroy()
            # Chercher l'URL de l'installateur .exe
            update_url = download_url
            if not update_url or not update_url.endswith('.exe'):
                # Essayer de construire l'URL de l'installateur
                update_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest/download/IllamaLauncher_Setup.exe"
            self._download_and_install_update(update_url)
        
        AnimatedButton(btn_frame, "Mettre a jour automatiquement", auto_update,
                      color='green', width=220, height=40).pack(side='left', padx=5)
        
        AnimatedButton(btn_frame, "Telecharger manuellement", download_update,
                      color='blue', width=200, height=40).pack(side='left', padx=5)
        
        AnimatedButton(btn_frame, "Plus tard", dialog.destroy,
                      color='gray', width=120, height=40).pack(side='left', padx=5)
    
    def _download_and_install_update(self, download_url: str):
        """Télécharge et installe automatiquement la mise à jour"""
        # Créer un dialogue de progression
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("Mise a jour en cours")
        progress_dialog.geometry("500x250")
        progress_dialog.configure(bg=COLORS['bg_dark'])
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        
        # Centrer la fenêtre
        progress_dialog.update_idletasks()
        x = (progress_dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (progress_dialog.winfo_screenheight() // 2) - (250 // 2)
        progress_dialog.geometry(f"500x250+{x}+{y}")
        
        main = tk.Frame(progress_dialog, bg=COLORS['bg_dark'], padx=30, pady=30)
        main.pack(fill='both', expand=True)
        
        tk.Label(main, text="Telechargement de la mise a jour...", 
                font=('Segoe UI', 14, 'bold'),
                bg=COLORS['bg_dark'], fg=COLORS['text_white']).pack(pady=(0, 20))
        
        # Barre de progression
        progress_frame = tk.Frame(main, bg=COLORS['bg_dark'])
        progress_frame.pack(fill='x', pady=(0, 10))
        
        progress_label = tk.Label(progress_frame, text="0%", 
                                 font=('Segoe UI', 10),
                                 bg=COLORS['bg_dark'], fg=COLORS['text_gray'])
        progress_label.pack()
        
        progress_bar = ProgressBarMC(progress_frame, width=400, height=20)
        progress_bar.pack(pady=(5, 0))
        
        status_label = tk.Label(main, text="Preparation...", 
                               font=('Segoe UI', 9),
                               bg=COLORS['bg_dark'], fg=COLORS['text_gray'])
        status_label.pack(pady=(10, 0))
        
        def download():
            try:
                download_path = Path(os.environ.get('TEMP', '.')) / "IllamaLauncher_Setup_Update.exe"
                
                # Télécharger avec progression
                ssl_ctx = ssl.create_default_context()
                req = urllib.request.Request(download_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=120) as response:
                    total_size = int(response.headers.get('Content-Length', 0))
                    downloaded_size = 0
                    chunk_size = 8192
                    
                    with open(download_path, 'wb') as f:
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Mettre à jour la progression
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                size_mb = downloaded_size / 1024 / 1024
                                total_mb = total_size / 1024 / 1024
                                
                                progress_dialog.after(0, lambda p=progress: progress_bar.set_progress(p))
                                progress_dialog.after(0, lambda p=progress: progress_label.config(text=f"{p:.1f}%"))
                                progress_dialog.after(0, lambda s=f"{size_mb:.1f} MB / {total_mb:.1f} MB": status_label.config(text=s))
                
                # Vérifier que le fichier est valide
                if download_path.stat().st_size < 1000000:  # Moins de 1 MB = invalide
                    raise Exception("Fichier telecharge invalide")
                
                # Fermer le dialogue de progression
                progress_dialog.after(0, progress_dialog.destroy)
                
                # Lancer l'installateur
                self.root.after(0, lambda: self.log("Installateur de mise a jour telecharge, lancement..."))
                self.root.after(0, lambda: status_label.config(text="Lancement de l'installateur..."))
                
                if sys.platform == 'win32':
                    # Lancer l'installateur qui remplacera les fichiers
                    os.startfile(str(download_path))
                    
                    # Fermer le launcher après un court délai
                    self.root.after(2000, self.root.quit)
                else:
                    # Linux/Mac - ouvrir le fichier
                    import subprocess
                    subprocess.Popen(['xdg-open' if sys.platform != 'darwin' else 'open', str(download_path)])
                    self.root.after(2000, self.root.quit)
                
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    progress_dialog.after(0, lambda: messagebox.showerror("Erreur",
                        "L'installateur n'a pas ete trouve sur GitHub.\n\n"
                        "Assure-toi que le fichier 'IllamaLauncher_Setup.exe' est bien present dans la release."))
                else:
                    progress_dialog.after(0, lambda: messagebox.showerror("Erreur",
                        f"Erreur HTTP {e.code} lors du telechargement."))
                progress_dialog.after(0, progress_dialog.destroy)
            except Exception as e:
                error_msg = str(e)
                progress_dialog.after(0, lambda: messagebox.showerror("Erreur",
                    f"Impossible de telecharger la mise a jour:\n\n{error_msg}\n\n"
                    "Tu peux telecharger manuellement depuis GitHub."))
                progress_dialog.after(0, progress_dialog.destroy)
        
        threading.Thread(target=download, daemon=True).start()
    
    def create_advanced_tab(self):
        """Onglet avance"""
        scroll = ScrollableFrame(self.advanced_tab)
        scroll.pack(fill='both', expand=True)
        
        main = scroll.scrollable_frame
        
        # Mises à jour
        update_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        update_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        tk.Label(update_frame, text="Mises a jour", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        version_info = tk.Frame(update_frame, bg=COLORS['bg_medium'])
        version_info.pack(fill='x', pady=(10, 10))
        
        tk.Label(version_info, text=f"Version actuelle: {LAUNCHER_VERSION}", 
                font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        check_update_btn = AnimatedButton(version_info, "Verifier les mises a jour", 
                                         lambda: self.check_for_updates(silent=False),
                                         color='blue', width=180, height=32)
        check_update_btn.pack(side='right')
        
        # Intervalle de vérification automatique
        interval_frame = tk.Frame(update_frame, bg=COLORS['bg_medium'])
        interval_frame.pack(fill='x', pady=(10, 0))
        
        tk.Label(interval_frame, text="Verification automatique toutes les:", 
                font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.update_interval_spin = tk.Spinbox(interval_frame, from_=0, to=1440, increment=5, width=5, font=('Segoe UI', 10))
        self.update_interval_spin.delete(0, 'end')
        self.update_interval_spin.insert(0, str(self.config.get('update_check_interval', 60)))
        self.update_interval_spin.pack(side='left', padx=(10, 5))
        
        tk.Label(interval_frame, text="minutes", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left', padx=(5, 0))
        
        tk.Label(interval_frame, text="(0 = desactive)", font=('Segoe UI', 9),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(side='left', padx=(10, 0))
        
        # Versions
        ver_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        ver_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(ver_frame, text="Versions", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        tk.Label(ver_frame, text="Minecraft:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(anchor='w', pady=(10, 2))
        
        self.mc_var = tk.StringVar(value=self.config.get('minecraft_version', '1.20.1'))
        mc_combo = ttk.Combobox(ver_frame, textvariable=self.mc_var, 
                               values=get_sorted_mc_versions(), state='readonly')
        mc_combo.pack(fill='x')
        mc_combo.bind('<<ComboboxSelected>>', self.on_mc_change)
        
        tk.Label(ver_frame, text="Forge:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(anchor='w', pady=(10, 2))
        
        self.forge_var = tk.StringVar(value=self.config.get('forge_version', '47.4.1'))
        self.forge_combo = ttk.Combobox(ver_frame, textvariable=self.forge_var, state='readonly')
        self.forge_combo.pack(fill='x')
        self.update_forge_list()
        
        # Prism
        prism_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        prism_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(prism_frame, text="Prism Launcher", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        self.prism_adv_status = tk.Label(prism_frame, text="Verification...",
                                        font=('Segoe UI', 10), bg=COLORS['bg_medium'], fg=COLORS['text_gray'])
        self.prism_adv_status.pack(anchor='w', pady=(10, 10))
        
        prism_btns = tk.Frame(prism_frame, bg=COLORS['bg_medium'])
        prism_btns.pack(fill='x')
        
        check_btn = AnimatedButton(prism_btns, "Verifier", self.check_prism_status,
                                  color='gray', width=100, height=32)
        check_btn.pack(side='left')
        
        install_btn = AnimatedButton(prism_btns, "Installer", self.install_prism,
                                    color='gold', width=100, height=32)
        install_btn.pack(side='left', padx=(10, 0))
        
        # Paramètres de téléchargement
        download_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        download_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(download_frame, text="Parametres de telechargement", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        tk.Label(download_frame, text="Ajustez ces parametres pour optimiser la vitesse de telechargement", 
                font=('Segoe UI', 9), bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(anchor='w', pady=(5, 15))
        
        # Téléchargements simultanés
        workers_frame = tk.Frame(download_frame, bg=COLORS['bg_medium'])
        workers_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(workers_frame, text="Telechargements simultanes:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.download_workers_spin = tk.Spinbox(workers_frame, from_=1, to=10, width=5, font=('Segoe UI', 10))
        self.download_workers_spin.delete(0, 'end')
        self.download_workers_spin.insert(0, str(self.config.get('download_workers', 5)))
        self.download_workers_spin.pack(side='left', padx=(10, 5))
        
        tk.Label(workers_frame, text="(1-10, recommande: 3-5)", font=('Segoe UI', 9),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(side='left', padx=(5, 0))
        
        # Nombre de tentatives
        retries_frame = tk.Frame(download_frame, bg=COLORS['bg_medium'])
        retries_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(retries_frame, text="Tentatives par fichier:", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.download_retries_spin = tk.Spinbox(retries_frame, from_=1, to=10, width=5, font=('Segoe UI', 10))
        self.download_retries_spin.delete(0, 'end')
        self.download_retries_spin.insert(0, str(self.config.get('download_retries', 3)))
        self.download_retries_spin.pack(side='left', padx=(10, 5))
        
        tk.Label(retries_frame, text="(1-10, recommande: 3)", font=('Segoe UI', 9),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(side='left', padx=(5, 0))
        
        # Timeout
        timeout_frame = tk.Frame(download_frame, bg=COLORS['bg_medium'])
        timeout_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(timeout_frame, text="Timeout (secondes):", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.download_timeout_spin = tk.Spinbox(timeout_frame, from_=30, to=600, increment=30, width=6, font=('Segoe UI', 10))
        self.download_timeout_spin.delete(0, 'end')
        self.download_timeout_spin.insert(0, str(self.config.get('download_timeout', 180)))
        self.download_timeout_spin.pack(side='left', padx=(10, 5))
        
        tk.Label(timeout_frame, text="(30-600, recommande: 180)", font=('Segoe UI', 9),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(side='left', padx=(5, 0))
        
        # Taille des chunks
        chunk_frame = tk.Frame(download_frame, bg=COLORS['bg_medium'])
        chunk_frame.pack(fill='x')
        
        tk.Label(chunk_frame, text="Taille buffer (KB):", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(side='left')
        
        self.download_chunk_spin = tk.Spinbox(chunk_frame, from_=8, to=128, increment=8, width=6, font=('Segoe UI', 10))
        self.download_chunk_spin.delete(0, 'end')
        chunk_size_kb = self.config.get('download_chunk_size', 32768) // 1024
        self.download_chunk_spin.insert(0, str(chunk_size_kb))
        self.download_chunk_spin.pack(side='left', padx=(10, 5))
        
        tk.Label(chunk_frame, text="(8-128 KB, recommande: 32)", font=('Segoe UI', 9),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(side='left', padx=(5, 0))
        
        # Compte
        acc_frame = tk.Frame(main, bg=COLORS['bg_medium'], padx=20, pady=15)
        acc_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(acc_frame, text="Compte", font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text_white']).pack(anchor='w')
        
        username = self.config.get('mc_username', 'Inconnu')
        tk.Label(acc_frame, text=f"Connecte: {username}", font=('Segoe UI', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_gray']).pack(anchor='w', pady=(10, 10))
        
        logout_btn = AnimatedButton(acc_frame, "Deconnexion", self.logout,
                                   color='red', width=120, height=32)
        logout_btn.pack(anchor='w')
        
        # Bouton sauvegarder
        save_btn = AnimatedButton(main, "Sauvegarder", self.save_advanced,
                                 color='green', width=150, height=40)
        save_btn.pack(pady=20)
    
    def set_resolution(self, width, height):
        self.width_spin.delete(0, 'end')
        self.width_spin.insert(0, str(width))
        self.height_spin.delete(0, 'end')
        self.height_spin.insert(0, str(height))
    
    def on_mc_change(self, event=None):
        self.update_forge_list()
    
    def update_forge_list(self):
        mc = self.mc_var.get()
        if mc in MINECRAFT_FORGE_VERSIONS:
            data = MINECRAFT_FORGE_VERSIONS[mc]
            self.forge_combo['values'] = data['versions']
            self.forge_var.set(data['recommended'])
    
    def check_prism_status(self):
        """Verifie si Prism est installe et valide"""
        launcher = MinecraftLauncher(self.config)
        prism_path = launcher.find_prism_launcher()
        
        if prism_path:
            # Vérifier l'intégrité de l'installation
            try:
                prism_file = Path(prism_path)
                if prism_file.exists():
                    file_size = prism_file.stat().st_size
                    if file_size > 1000000:  # Au moins 1 MB
                        self.prism_status.config(text=f"Prism Launcher installe ({file_size / 1024 / 1024:.1f} MB)", 
                                                fg=COLORS['minecraft_green'])
                        self.prism_adv_status.config(text=f"Installe: {prism_path}", fg=COLORS['minecraft_green'])
                        self.install_prism_btn.pack_forget()
                        self.play_btn.set_enabled(True)
                        self.log(f"Prism Launcher detecte et valide: {prism_path}")
                    else:
                        # Fichier trop petit, probablement corrompu
                        self.prism_status.config(text="Prism Launcher corrompu", fg=COLORS['accent_red'])
                        self.prism_adv_status.config(text="Installation invalide", fg=COLORS['accent_red'])
                        self.install_prism_btn.pack(side='right')
                        self.play_btn.set_enabled(False)
                        self.log("Prism Launcher detecte mais fichier invalide (trop petit)")
                else:
                    # Fichier n'existe pas
                    self.prism_status.config(text="Prism Launcher non trouve", fg=COLORS['accent_red'])
                    self.prism_adv_status.config(text="Fichier introuvable", fg=COLORS['accent_red'])
                    self.install_prism_btn.pack(side='right')
                    self.play_btn.set_enabled(False)
                    self.log("Prism Launcher non trouve a l'emplacement attendu")
            except Exception as e:
                self.prism_status.config(text="Erreur verification", fg=COLORS['accent_red'])
                self.prism_adv_status.config(text=f"Erreur: {e}", fg=COLORS['accent_red'])
                self.install_prism_btn.pack(side='right')
                self.play_btn.set_enabled(False)
                self.log(f"Erreur lors de la verification: {e}")
        else:
            self.prism_status.config(text="Prism Launcher non installe", fg=COLORS['accent_red'])
            self.prism_adv_status.config(text="Non installe", fg=COLORS['accent_red'])
            self.install_prism_btn.pack(side='right')
            self.play_btn.set_enabled(False)
            self.log("Prism Launcher non detecte - Installation requise")
    
    def install_prism(self):
        """Telecharge et installe Prism - Verifie d'abord si deja installe"""
        # Vérifier d'abord si Prism est déjà installé
        launcher = MinecraftLauncher(self.config)
        prism_path = launcher.find_prism_launcher()
        
        if prism_path:
            # Prism est déjà installé, vérifier l'intégrité
            self.log("Prism Launcher deja installe, verification de l'integrite...")
            self.prism_status.config(text="Verification de l'installation...", fg=COLORS['accent_gold'])
            
            def verify_installation():
                try:
                    # Vérifier que l'exécutable existe et est valide
                    if Path(prism_path).exists():
                        file_size = Path(prism_path).stat().st_size
                        if file_size > 1000000:  # Au moins 1 MB
                            self.root.after(0, lambda: self.log(f"Prism Launcher valide: {prism_path} ({file_size / 1024 / 1024:.1f} MB)"))
                            self.root.after(0, lambda: self.prism_status.config(
                                text="Prism Launcher installe et valide", fg=COLORS['minecraft_green']))
                            self.root.after(0, lambda: messagebox.showinfo("Verification",
                                f"Prism Launcher est deja installe et fonctionnel.\n\n"
                                f"Emplacement: {prism_path}\n\n"
                                "Aucun telechargement necessaire."))
                            # Mettre à jour le statut
                            self.root.after(0, self.check_prism_status)
                            return
                    
                    # Si l'exécutable est corrompu ou invalide
                    self.root.after(0, lambda: self.log("Installation Prism detectee mais invalide, telechargement necessaire"))
                    self._download_prism_installer()
                    
                except Exception as e:
                    self.root.after(0, lambda: self.log(f"Erreur verification: {e}"))
                    self.root.after(0, lambda: self.prism_status.config(
                        text="Erreur verification", fg=COLORS['accent_red']))
                    # Essayer de télécharger quand même
                    self._download_prism_installer()
            
            threading.Thread(target=verify_installation, daemon=True).start()
        else:
            # Prism n'est pas installé, télécharger
            self._download_prism_installer()
    
    def _download_prism_installer(self):
        """Telecharge l'installateur Prism"""
        self.log("Telechargement de Prism Launcher...")
        self.prism_status.config(text="Telechargement...", fg=COLORS['accent_gold'])
        
        def download():
            try:
                # URLs alternatives pour Prism Launcher (essayer plusieurs)
                urls = [
                    "https://github.com/PrismLauncher/PrismLauncher/releases/latest/download/PrismLauncher-Windows-MSVC-Setup.exe",
                    "https://github.com/PrismLauncher/PrismLauncher/releases/download/latest/PrismLauncher-Windows-MSVC-Setup.exe",
                    "https://github.com/PrismLauncher/PrismLauncher/releases/latest/download/PrismLauncher-Windows-Setup.exe"
                ]
                
                download_path = Path(os.environ.get('TEMP', '.')) / "PrismLauncher-Setup.exe"
                ssl_ctx = ssl.create_default_context()
                
                # Essayer chaque URL jusqu'à ce qu'une fonctionne
                downloaded = False
                for url in urls:
                    try:
                        self.root.after(0, lambda u=url: self.log(f"Tentative: {u}"))
                        req = urllib.request.Request(url, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        
                        with urllib.request.urlopen(req, context=ssl_ctx, timeout=120) as response:
                            if response.status == 200:
                                with open(download_path, 'wb') as f:
                                    # Télécharger par chunks pour afficher la progression
                                    total_size = int(response.headers.get('Content-Length', 0))
                                    downloaded_size = 0
                                    chunk_size = 8192
                                    
                                    while True:
                                        chunk = response.read(chunk_size)
                                        if not chunk:
                                            break
                                        f.write(chunk)
                                        downloaded_size += len(chunk)
                                
                                # Vérifier que le fichier est valide (au moins 1 MB)
                                if download_path.stat().st_size > 1000000:
                                    downloaded = True
                                    break
                    except urllib.error.HTTPError as e:
                        if e.code == 404:
                            self.root.after(0, lambda: self.log(f"URL non trouvee (404): {url}"))
                            continue
                        else:
                            raise
                    except Exception as e:
                        self.root.after(0, lambda: self.log(f"Erreur avec {url}: {e}"))
                        continue
                
                if not downloaded:
                    raise Exception("Aucune URL valide trouvee pour telecharger Prism Launcher")
                
                if sys.platform == 'win32':
                    os.startfile(str(download_path))
                
                self.root.after(0, lambda: self.log("Installateur Prism lance"))
                self.root.after(0, lambda: self.prism_status.config(
                    text="Installe Prism puis clique Verifier", fg=COLORS['accent_gold']))
                self.root.after(0, lambda: messagebox.showinfo("Installation",
                    "L'installateur Prism Launcher a ete lance.\n\n"
                    "1. Suis les instructions d'installation\n"
                    "2. Une fois termine, reviens ici\n"
                    "3. Clique sur 'Verifier' dans l'onglet Avance"))
                
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.log(f"Erreur telechargement: {error_msg}"))
                self.root.after(0, lambda: self.prism_status.config(
                    text="Erreur telechargement", fg=COLORS['accent_red']))
                self.root.after(0, lambda: messagebox.showerror("Erreur",
                    f"Impossible de telecharger Prism Launcher.\n\n"
                    f"Erreur: {error_msg}\n\n"
                    "Tu peux telecharger Prism Launcher manuellement depuis:\n"
                    "https://prismlauncher.org/download/"))
        
        threading.Thread(target=download, daemon=True).start()
    
    def play_game(self):
        """Lance le jeu"""
        if self.is_syncing:
            return
        
        self.is_syncing = True
        self.play_btn.set_enabled(False)
        self.play_btn.set_text("Preparation...")
        
        def check_and_sync():
            """Vérifie les fichiers et synchronise"""
            try:
                launcher = MinecraftLauncher(self.config)
                
                # Créer l'instance si nécessaire
                if not launcher.instance_exists():
                    self.root.after(0, lambda: self.log("Creation de l'instance Prism..."))
                    self.root.after(0, lambda: self.status_label.config(text="Creation de l'instance..."))
                    launcher.create_instance()
                
                # Récupérer le dossier mods de l'instance
                mods_dir = launcher.get_mods_dir()
                mods_dir.mkdir(parents=True, exist_ok=True)
                
                self.root.after(0, lambda: self.log(f"Dossier mods: {mods_dir}"))
                
                # Sync mods
                sync = GoogleDriveSync(
                    self.config.get('google_drive_folder_id', DRIVE_FOLDER_ID),
                    mods_dir,
                    self.config.get('api_key', DRIVE_API_KEY)
                )
                
                # Vérifier d'abord les fichiers à remplacer
                self.root.after(0, lambda: self.status_label.config(text="Verification des fichiers..."))
                self.root.after(0, lambda: self.play_btn.set_text("Verification..."))
                
                remote_files = sync.get_folder_files()
                remote_dict = {f['name']: f for f in remote_files}
                local_files = {f.name for f in mods_dir.iterdir() if f.suffix == '.jar'}
                
                files_to_replace = []
                for f in remote_files:
                    if f['name'] in local_files:
                        local_path = mods_dir / f['name']
                        if local_path.exists():
                            local_md5 = sync._calculate_md5(local_path)
                            remote_md5 = f.get('md5', '')
                            if remote_md5 and local_md5 and remote_md5 != local_md5:
                                files_to_replace.append(f['name'])
                
                # Si des fichiers doivent être remplacés, demander confirmation
                if files_to_replace:
                    self.root.after(0, lambda: self._ask_replace_files(files_to_replace, sync, mods_dir, launcher))
                else:
                    # Pas de fichiers à remplacer, continuer la synchronisation normale
                    self._do_sync(sync, mods_dir, launcher)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: self.log(f"Erreur: {e}"))
                self.root.after(0, lambda: self.status_label.config(text=f"Erreur: {e}"))
                self.root.after(0, self._reset_play_btn)
        
        threading.Thread(target=check_and_sync, daemon=True).start()
    
    def _ask_replace_files(self, files_to_replace, sync, mods_dir, launcher):
        """Demande confirmation pour remplacer les fichiers"""
        file_list = '\n'.join(files_to_replace[:10])  # Limiter à 10 fichiers pour l'affichage
        if len(files_to_replace) > 10:
            file_list += f"\n... et {len(files_to_replace) - 10} autres fichiers"
        
        msg = f"{len(files_to_replace)} fichier(s) doivent etre remplaces pour correspondre au serveur:\n\n{file_list}\n\nVeux-tu les remplacer maintenant?"
        
        if messagebox.askyesno("Fichiers a remplacer", msg):
            # L'utilisateur accepte, on fait la synchronisation avec remplacement forcé
            self.root.after(0, lambda: self.log(f"Remplacement de {len(files_to_replace)} fichiers accepte"))
            self._do_sync(sync, mods_dir, launcher, force_replace=True)
        else:
            # L'utilisateur refuse, on continue sans remplacer
            self.root.after(0, lambda: self.log("Remplacement refuse, synchronisation sans remplacement"))
            self._do_sync(sync, mods_dir, launcher, force_replace=False)
    
    def _do_sync(self, sync, mods_dir, launcher, force_replace=False):
        """Effectue la synchronisation"""
        try:
            self.root.after(0, lambda: self.play_btn.set_text("Synchronisation..."))
            
            def progress_cb(msg, current, total):
                pct = (current / total * 100) if total > 0 else 0
                self.root.after(0, lambda m=msg: self.status_label.config(text=m))
                self.root.after(0, lambda p=pct: self.progress_bar.set_progress(p))
                self.root.after(0, lambda m=msg: self.log(m))
            
            stats = sync.sync(progress_cb, force_replace=force_replace, config=self.config)
            
            added = len(stats['added'])
            removed = len(stats['removed'])
            unchanged = len(stats['unchanged'])
            updated = len(stats.get('updated', []))
            errors = len(stats['errors'])
            
            sync_msg = f"Sync termine: +{added} nouveaux"
            if updated > 0:
                sync_msg += f", {updated} remplaces"
            if removed > 0:
                sync_msg += f", -{removed} supprimes"
            if unchanged > 0:
                sync_msg += f", {unchanged} inchanges"
            
            self.root.after(0, lambda: self.log(sync_msg))
            
            if errors > 0:
                self.root.after(0, lambda: self.log(f"Attention: {errors} erreurs"))
            
            # Sauvegarder last sync
            self.config['last_sync'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            self.save_config()
            
            # FORCER le serveur Illama avant le lancement (sécurité)
            self.root.after(0, lambda: self.log("Verification du serveur..."))
            launcher.create_server_dat()
            launcher.create_options_txt()
            launcher._enforce_server_only()
            
            # Lancer le jeu
            self.root.after(0, lambda: self.status_label.config(text="Lancement du jeu..."))
            self.root.after(0, lambda: self.play_btn.set_text("Lancement..."))
            self.root.after(0, lambda: self.log("Lancement de l'instance IllamaServer..."))
            
            if launcher.launch():
                self.root.after(0, lambda: self.log("Jeu lance! Bon jeu sur Illama Server!"))
                self.root.after(0, lambda: self.status_label.config(text="Jeu lance!"))
                self.root.after(0, lambda: self.progress_bar.set_progress(100))
                
                # Minimiser dans le tray
                if self.config.get('minimize_to_tray', True):
                    self.root.after(2000, self.hide_window)
            else:
                self.root.after(0, lambda: self.log("Erreur: Impossible de lancer Prism"))
                self.root.after(0, lambda: messagebox.showerror("Erreur", 
                    "Impossible de lancer Prism Launcher.\n\n"
                    "Verifie qu'il est bien installe."))
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.log(f"Erreur: {e}"))
            self.root.after(0, lambda: self.status_label.config(text=f"Erreur: {e}"))
        finally:
            self.root.after(0, self._reset_play_btn)
    
    def _reset_play_btn(self):
        self.is_syncing = False
        self.play_btn.set_enabled(True)
        self.play_btn.set_text("JOUER")
    
    def save_settings(self):
        """Sauvegarde les parametres"""
        self.config['ram_min'] = int(self.ram_min_spin.get())
        self.config['ram_max'] = int(self.ram_max_spin.get())
        self.config['window_width'] = int(self.width_spin.get())
        self.config['window_height'] = int(self.height_spin.get())
        self.config['fullscreen'] = self.fullscreen_var.get()
        self.config['borderless'] = self.borderless_var.get()
        self.config['auto_connect'] = self.auto_connect_var.get()
        self.config['minimize_to_tray'] = self.minimize_tray_var.get()
        
        self.save_config()
        self.log("Parametres sauvegardes")
        messagebox.showinfo("Sauvegarde", "Parametres sauvegardes!")
    
    def save_minecraft_settings(self):
        """Sauvegarde les parametres Minecraft"""
        if 'minecraft_options' not in self.config:
            self.config['minecraft_options'] = {}
        
        # Graphiques
        self.config['minecraft_options']['graphics'] = self.graphics_var.get()
        self.config['minecraft_options']['renderDistance'] = int(self.render_distance_var.get())
        self.config['minecraft_options']['entityDistanceScaling'] = round(self.entity_distance_var.get(), 1)
        self.config['minecraft_options']['particles'] = self.particles_var.get()
        self.config['minecraft_options']['maxFps'] = int(self.max_fps_var.get())
        self.config['minecraft_options']['vsync'] = self.vsync_var.get()
        self.config['minecraft_options']['entityShadows'] = self.entity_shadows_var.get()
        self.config['minecraft_options']['useVbo'] = self.use_vbo_var.get()
        
        # Rendu Avancé
        self.config['minecraft_options']['ao'] = self.ao_var.get()
        self.config['minecraft_options']['smoothLighting'] = self.smooth_lighting_var.get()
        self.config['minecraft_options']['gamma'] = round(self.gamma_var.get(), 2)
        self.config['minecraft_options']['mipmapLevels'] = int(self.mipmap_levels_var.get())
        self.config['minecraft_options']['anisotropicFiltering'] = int(self.anisotropic_filtering_var.get())
        self.config['minecraft_options']['biomeBlendRadius'] = int(self.biome_blend_var.get())
        self.config['minecraft_options']['renderClouds'] = self.clouds_var.get()
        self.config['minecraft_options']['renderSky'] = self.sky_var.get()
        self.config['minecraft_options']['renderStars'] = self.stars_var.get()
        self.config['minecraft_options']['renderSunMoon'] = self.sun_moon_var.get()
        
        # Performance
        self.config['minecraft_options']['chunkUpdateThreads'] = int(self.chunk_threads_var.get())
        self.config['minecraft_options']['prioritizeChunkUpdates'] = self.prioritize_chunks_var.get()
        self.config['minecraft_options']['animateOnlyVisibleTextures'] = self.animate_only_var.get()
        
        # Audio
        self.config['minecraft_options']['sound'] = round(self.sound_var.get(), 2)
        self.config['minecraft_options']['music'] = round(self.music_var.get(), 2)
        
        # Contrôles
        self.config['minecraft_options']['sensitivity'] = round(self.sensitivity_var.get(), 2)
        self.config['minecraft_options']['invertYMouse'] = self.invert_y_var.get()
        self.config['minecraft_options']['autoJump'] = self.auto_jump_var.get()
        
        # Interface
        gui_scale = self.gui_scale_var.get()
        self.config['minecraft_options']['guiScale'] = gui_scale if gui_scale != 'auto' else 'auto'
        self.config['minecraft_options']['fov'] = float(self.fov_var.get())
        self.config['minecraft_options']['bobbing'] = self.bobbing_var.get()
        
        # Chat
        self.config['minecraft_options']['chatOpacity'] = round(self.chat_opacity_var.get(), 2)
        self.config['minecraft_options']['chatColors'] = self.chat_colors_var.get()
        
        # Autres
        self.config['minecraft_options']['difficulty'] = self.difficulty_var.get()
        self.config['minecraft_options']['showSubtitles'] = self.subtitles_var.get()
        self.config['minecraft_options']['reducedDebugInfo'] = self.reduced_debug_var.get()
        
        self.save_config()
        self.log("Parametres Minecraft sauvegardes")
        messagebox.showinfo("Sauvegarde", "Parametres Minecraft sauvegardes!")
    
    def save_advanced(self):
        """Sauvegarde les parametres avances"""
        self.config['minecraft_version'] = self.mc_var.get()
        self.config['forge_version'] = self.forge_var.get()
        
        # Paramètres de téléchargement
        self.config['download_workers'] = int(self.download_workers_spin.get())
        self.config['download_retries'] = int(self.download_retries_spin.get())
        self.config['download_timeout'] = int(self.download_timeout_spin.get())
        chunk_size_kb = int(self.download_chunk_spin.get())
        self.config['download_chunk_size'] = chunk_size_kb * 1024  # Convertir en bytes
        
        # Sauvegarder l'intervalle de vérification des mises à jour
        new_interval = int(self.update_interval_spin.get())
        old_interval = self.config.get('update_check_interval', 60)
        self.config['update_check_interval'] = new_interval
        
        # Redémarrer la vérification périodique si l'intervalle a changé
        if new_interval != old_interval:
            self.stop_periodic_update_check()
            if new_interval > 0:
                self.start_periodic_update_check()
                self.log(f"Verification automatique configuree: toutes les {new_interval} minutes")
            else:
                self.log("Verification automatique desactivee")
        
        self.save_config()
        self.log("Configuration avancee sauvegardee")
        messagebox.showinfo("Sauvegarde", "Configuration sauvegardee!")
    
    def logout(self):
        """Deconnexion"""
        if messagebox.askyesno("Deconnexion", "Veux-tu vraiment te deconnecter?"):
            try:
                AUTH_FILE.unlink()
            except:
                pass
            
            self.config['mc_username'] = ''
            self.config['mc_uuid'] = ''
            self.save_config()
            
            messagebox.showinfo("Deconnexion", "Tu as ete deconnecte. Le launcher va se fermer.")
            self.quit_app()
    
    def log(self, message: str):
        """Ajoute un message au log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
    
    def load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except:
                pass
        return DEFAULT_CONFIG.copy()
    
    def _on_window_configure(self, event=None):
        """Sauvegarde la position et taille de la fenêtre"""
        if event and event.widget == self.root:
            # Ne sauvegarder que si c'est la fenêtre principale qui bouge
            geometry = self.root.geometry()
            if geometry and 'x' in geometry:
                self.config['window_geometry'] = geometry
                # Sauvegarder de manière asynchrone pour ne pas ralentir
                self.root.after(500, self._save_window_position)
    
    def _save_window_position(self):
        """Sauvegarde la position de la fenêtre dans le fichier de config"""
        try:
            geometry = self.root.geometry()
            if geometry:
                self.config['window_geometry'] = geometry
                self.save_config()
        except:
            pass
    
    def save_config(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def on_close(self):
        """Gere la fermeture de la fenetre"""
        # Sauvegarder la position avant de fermer
        self._save_window_position()
        
        if self.config.get('minimize_to_tray', True) and self.tray.tray_available:
            self.hide_window()
        else:
            self.quit_app()
    
    def hide_window(self):
        """Cache la fenetre dans le tray"""
        self.root.withdraw()
    
    def show_window(self):
        """Affiche la fenetre"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def quit_app(self):
        """Quitte l'application"""
        # Arrêter la vérification périodique
        self.stop_periodic_update_check()
        self.tray.stop()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()


# ============================================================
# MAIN
# ============================================================

def main():
    # Verifier auth existante
    auth_data = None
    if AUTH_FILE.exists():
        try:
            with open(AUTH_FILE, 'r') as f:
                auth_data = json.load(f)
        except:
            pass
    
    # Charger config
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = {**DEFAULT_CONFIG, **json.load(f)}
        except:
            pass
    
    # Mettre a jour config avec auth
    if auth_data:
        config.update(auth_data)
    
    def start_launcher(final_config):
        # Sauvegarder config
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_config, f, indent=2)
        
        # Lancer GUI principal
        app = LauncherGUI(final_config)
        app.run()
    
    def on_setup_complete(setup_config):
        config.update(setup_config)
        start_launcher(config)
    
    def on_login_success(auth_result):
        config.update(auth_result)
        
        if not config.get('setup_completed'):
            wizard = SetupWizard(on_setup_complete)
            wizard.run()
        else:
            start_launcher(config)
    
    # Flux principal
    if auth_data and config.get('mc_username'):
        # Deja connecte
        if not config.get('setup_completed'):
            wizard = SetupWizard(on_setup_complete)
            wizard.run()
        else:
            start_launcher(config)
    else:
        # Besoin de login
        login = LoginScreen(on_login_success)
        login.run()


if __name__ == "__main__":
    main()
