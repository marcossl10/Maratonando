# /home/marcos/Maratonando/maratonando_src/gui.py
 # Importação original que causa o ModuleNotFoundError quando embutido
from maratonando_src import customtkinter as ctk # Importação corrigida
import tkinter.messagebox as messagebox
import tkinter.simpledialog as simpledialog
import subprocess
import json
import os
import threading
import time
import math
import re
from pathlib import Path
import hashlib 
import sys
import logging
from io import BytesIO
import requests
from PIL import Image, ImageTk, ImageFont, ImageDraw 

from .core.parsers import AnimeFireParser
from .core.player import ExternalMediaPlayer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

HISTORY_FILE = "history.json"

class AnimeApp:
    def __init__(self, root: ctk.CTk):
        self.root = root
        project_base_dir = Path(__file__).resolve().parent.parent

        installed_icon_path = Path("/usr/share/maratonando/icons/maratonando.png")
        dev_icon_path = project_base_dir / "icons" / "maratonando.png"
        icon_path = installed_icon_path if installed_icon_path.exists() else dev_icon_path
        self._set_icon(icon_path)

        self.root.title("Maratonando Animes")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue") # Ou "green", "dark-blue"

        self.logo_images_filenames = ["logo1.png", "logo2.png", "logo3.png"]
        self.logo_cycle_interval = 10
        self.current_logo_index = 0

        initial_width = 700
        initial_height = 850
        min_width = 700
        min_height = 850
        max_width = 700
        max_height = 850

        self.root.geometry(f"{initial_width}x{initial_height}")
        self.root.minsize(min_width, min_height)
        self.root.maxsize(max_width, max_height)
        self.root.resizable(True, True)

        # --- Carregar Ícones ---
        self.search_icon_ctk = self._load_icon_ctk("search.png")
        self.clear_icon_ctk = self._load_icon_ctk("broom.png")
        self.history_icon_ctk = self._load_icon_ctk("history.png")
        self.prev_icon_ctk = self._load_icon_ctk("left.png")
        self.next_icon_ctk = self._load_icon_ctk("next.png")
        self.about_icon_ctk = self._load_icon_ctk("information.png")
        self.favorite_icon_ctk = self._load_icon_ctk("heart.png")
        self.episodes_icon_ctk = self._load_icon_ctk("ep_icon.png", placeholder_text="EP")
        self.refresh_icon_ctk = self._load_icon_ctk("sync.png", placeholder_text="↻")
    

        # --- Estrutura Principal da UI ---
        self.main_app_frame = ctk.CTkFrame(root, fg_color="transparent")
        self.main_app_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.header_logo_ctk = self._load_icon_ctk("logo1.png",size=(700,150), maintain_aspect=True)
        if self.header_logo_ctk:
            self.header_logo_label = ctk.CTkLabel(self.main_app_frame, image=self.header_logo_ctk, text="")
            self.header_logo_label.pack(pady=(0,10))

        self.navigation_frame = ctk.CTkFrame(self.main_app_frame, fg_color="transparent")
        self.navigation_frame.pack(pady=5)

        self.nav_search_button = ctk.CTkButton(self.navigation_frame, text="BUSCAR", image=self.search_icon_ctk, compound="left", command=lambda: self.show_page("search"))
        self.nav_search_button.pack(side="left", padx=5)

        self.nav_episodes_button = ctk.CTkButton(self.navigation_frame, text="EPISÓDIOS", image=self.episodes_icon_ctk, compound="left", command=lambda: self.show_page("episodes"), state="disabled")
        self.nav_episodes_button.pack(side="left", padx=5)

        self.nav_history_button = ctk.CTkButton(self.navigation_frame, text="HISTÓRICO", image=self.history_icon_ctk, compound="left", command=lambda: self.show_page("history"))
        self.nav_history_button.pack(side="left", padx=5)

        self.nav_about_button = ctk.CTkButton(self.navigation_frame, text="SOBRE", image=self.about_icon_ctk, compound="left", command=lambda: self.show_page("about"))
        self.nav_about_button.pack(side="left", padx=5)

        self.search_bar_frame = ctk.CTkFrame(self.main_app_frame, fg_color="transparent")
        self.search_bar_frame.pack(fill="x", pady=5, padx=10)

        # --- Lógica do Parser Simplificada ---
        self.active_parser = AnimeFireParser()
        self.active_parser_name = "AnimeFire" # Nome interno para o histórico

        self.search_entry = ctk.CTkEntry(self.search_bar_frame, placeholder_text="Buscar anime...")
        self.search_entry.pack(side="left", expand=True, fill="x", padx=(0,5))
        self.search_entry.bind("<Return>", self.start_search_thread)

        self.search_button_action = ctk.CTkButton(self.search_bar_frame, text="Buscar", image=self.search_icon_ctk, compound="left", command=self.start_search_thread, width=100)
        self.search_button_action.pack(side="left", padx=5)

        self.clear_button_action = ctk.CTkButton(self.search_bar_frame, text="Limpar", image=self.clear_icon_ctk, compound="left", command=self.clear_search_results, width=100)
        self.clear_button_action.pack(side="left", padx=5)

        self.content_area_frame = ctk.CTkFrame(self.main_app_frame, fg_color="transparent")
        self.content_area_frame.pack(fill="both", expand=True, pady=(10,0))
        # Configurar o grid do content_area_frame para permitir que a página ativa expanda
        self.content_area_frame.grid_rowconfigure(0, weight=1)
        self.content_area_frame.grid_columnconfigure(0, weight=1)

        self.pages = {}

        self._create_search_page()
        self._create_episodes_page()
        self._create_history_page()
        self._create_about_page()

        self.status_label = ctk.CTkLabel(self.main_app_frame, text="Pronto.", anchor="w")
        self.status_label.pack(side="bottom", fill="x", pady=(5,0), padx=5)

        self.search_results_data = [] 
        self.history_data = []
        self.selected_anime_title = ""
        # Atributos para paginação da busca
        self.search_results_per_page = 4
        self.current_search_page = 1
        self.total_search_results_data = [] 
        self.selected_anime_url_for_history = None
        self.current_selected_episode = None
        self.episode_details_data = {}
        self.is_updating_episodes = False
        self.episodes_per_page = 8 
        self.current_episode_page = 1
        self.last_selected_episode_listbox_index = -1
        self.target_episode_url_from_history = None

        self.player = ExternalMediaPlayer()
        self.load_history()

        self.show_page("search")
        self._start_logo_cycling_thread()

        # Configuração do Cache de Imagens
        home = Path.home()
        cache_dir_parent = os.environ.get('XDG_CACHE_HOME') or str(home / ".cache")
        self.image_cache_dir = Path(cache_dir_parent) / "maratonando" / "images"
        self.image_cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_filepath(self, url: str) -> Path:
        """Gera um nome de arquivo para o cache a partir de uma URL."""
        if not url:
            return None
        # Usa o hash MD5 da URL para criar um nome de arquivo único e seguro
        # Adiciona uma extensão comum, .webp é bom para imagens da web, mas .png é mais seguro para Pillow
        filename = hashlib.md5(url.encode('utf-8')).hexdigest() + ".png"
        return self.image_cache_dir / filename


    def _create_search_page(self):
        page = ctk.CTkFrame(self.content_area_frame, fg_color="transparent")
        page.grid_rowconfigure(0, weight=1)    
        page.grid_rowconfigure(1, weight=0)    
        page.grid_columnconfigure(0, weight=1) 

        self.search_results_scroll_frame = ctk.CTkScrollableFrame(page, label_text="Resultados da Busca", fg_color="transparent")
        self.search_results_scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        if hasattr(self.search_results_scroll_frame, "_scrollbar") and self.search_results_scroll_frame._scrollbar is not None:
            self.search_results_scroll_frame._scrollbar.grid_forget()

        # Frame de Paginação da Busca
        self.search_pagination_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.search_pagination_frame.grid(row=1, column=0, sticky='ew', pady=(5,0), padx=5)

        self.prev_search_button = ctk.CTkButton(self.search_pagination_frame, text="< Anterior", command=self.go_to_previous_search_page, state="disabled", image=self.prev_icon_ctk, compound="left")
        self.next_search_button = ctk.CTkButton(self.search_pagination_frame, text="Próximo >", command=self.go_to_next_search_page, state="disabled", image=self.next_icon_ctk, compound="right")
        self.search_page_label = ctk.CTkLabel(self.search_pagination_frame, text="Página -/-")

        self.search_pagination_frame.grid_columnconfigure(0, weight=1) 
        self.search_pagination_frame.grid_columnconfigure(1, weight=1) 
        self.search_pagination_frame.grid_columnconfigure(2, weight=1) 
        self.prev_search_button.grid(row=0, column=0, padx=5, sticky="w")
        self.search_page_label.grid(row=0, column=1, padx=5)
        self.next_search_button.grid(row=0, column=2, padx=5, sticky="e")
        self.pages["search"] = page

    def _create_episodes_page(self):
        page = ctk.CTkFrame(self.content_area_frame, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1) 

        self.cover_title_area_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.cover_title_area_frame.grid(row=0, column=0, sticky='ew', pady=(5,10), padx=5)
        self.cover_title_area_frame.grid_columnconfigure(0, weight=0) 
        self.cover_title_area_frame.grid_columnconfigure(1, weight=1) 

        self.target_cover_height = 200
        placeholder_width_approx = int(self.target_cover_height * (2/3))
        self.placeholder_image_ctk = self._load_icon_ctk(None, size=(placeholder_width_approx, self.target_cover_height), placeholder_text="Capa")

        self.anime_cover_label = ctk.CTkLabel(self.cover_title_area_frame, image=self.placeholder_image_ctk, text="")
        self.anime_cover_label.grid(row=0, column=0, rowspan=2, sticky='n', padx=(0,10))

        self.anime_title_label_ep_tab = ctk.CTkLabel(self.cover_title_area_frame, text="Nenhum anime selecionado", font=ctk.CTkFont(size=16, weight="bold"), anchor="w")
        self.anime_title_label_ep_tab.grid(row=0, column=1, sticky='new', pady=(0,5))
        
        self.anime_description_label_ep_tab = ctk.CTkLabel(self.cover_title_area_frame, text="", anchor="w", justify="left", wraplength=450)
        self.anime_description_label_ep_tab.grid(row=1, column=1, sticky='new')

        self.episodes_scroll_frame = ctk.CTkScrollableFrame(page, label_text="Episódios")
        self.episodes_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=0)
        if hasattr(self.episodes_scroll_frame, "_scrollbar") and self.episodes_scroll_frame._scrollbar is not None:
            self.episodes_scroll_frame._scrollbar.grid_forget()

        self.episode_pagination_frame = ctk.CTkFrame(page)
        self.episode_pagination_frame.grid(row=2, column=0, sticky='ew', pady=(5,0), padx=5)

        self.prev_episode_button = ctk.CTkButton(self.episode_pagination_frame, text="< Anterior", command=self.go_to_previous_page, state="disabled", image=self.prev_icon_ctk, compound="left")
        self.next_episode_button = ctk.CTkButton(self.episode_pagination_frame, text="Próximo >", command=self.go_to_next_page, state="disabled", image=self.next_icon_ctk, compound="right")
        self.episode_page_label = ctk.CTkLabel(self.episode_pagination_frame, text="Página -/-")

        self.episode_pagination_frame.grid_columnconfigure(0, weight=1)
        self.episode_pagination_frame.grid_columnconfigure(1, weight=1)
        self.episode_pagination_frame.grid_columnconfigure(2, weight=1)
        self.prev_episode_button.grid(row=0, column=0, padx=5, sticky="w")
        self.episode_page_label.grid(row=0, column=1, padx=5)
        self.next_episode_button.grid(row=0, column=2, padx=5, sticky="e")

        self.pages["episodes"] = page


    def _create_history_page(self):
        page = ctk.CTkFrame(self.content_area_frame, fg_color="transparent")
        page.grid_rowconfigure(1, weight=1) 
        page.grid_columnconfigure(0, weight=1)
        
        self.history_button_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.history_button_frame.grid(row=0, column=0, sticky="ew", pady=5, padx=5)

        self.refresh_history_button = ctk.CTkButton(self.history_button_frame, text="Atualizar", command=self.refresh_history, image=self.refresh_icon_ctk, compound="left")
        self.refresh_history_button.pack(side="left", padx=5)

        self.clear_history_button = ctk.CTkButton(self.history_button_frame, text="Limpar Histórico", command=self.clear_history, image=self.clear_icon_ctk, compound="left")
        self.clear_history_button.pack(side="left", padx=5)
        
        self.toggle_favorite_button = ctk.CTkButton(self.history_button_frame, text="Favoritar", command=self.toggle_favorite_selected, image=self.favorite_icon_ctk, compound="left", state="disabled")
        self.toggle_favorite_button.pack(side="left", padx=5)
        
        self.history_scroll_frame = ctk.CTkScrollableFrame(page, label_text="Seu Histórico", fg_color="transparent")
        self.history_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        if hasattr(self.history_scroll_frame, "_scrollbar") and self.history_scroll_frame._scrollbar is not None:
            self.history_scroll_frame._scrollbar.grid_forget()
        self.selected_history_item_widget = None 

        self.pages["history"] = page

    def _create_about_page(self):
        page = ctk.CTkFrame(self.content_area_frame, fg_color="transparent")
        page.grid_rowconfigure(0, weight=1)
        page.grid_columnconfigure(0, weight=1)
        self.populate_about_tab_content(page) 
        self.pages["about"] = page

    def show_page(self, page_name):
        for name, frame in self.pages.items():
            if name == page_name:
                frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            else:
                frame.grid_forget() 
        
        if hasattr(self, 'episode_details_data') and self.episode_details_data.get('episodes'):
            self.nav_episodes_button.configure(state="normal")
        elif not self.selected_anime_url_for_history:
             self.nav_episodes_button.configure(state="disabled")


    def _load_icon_ctk(self, filename, size=(24,24), placeholder_text="?", maintain_aspect=False):
        pil_image = None
        try:
            if filename:
                gui_dir = Path(__file__).resolve().parent
                icon_path = gui_dir / "assets" / filename
                if icon_path.exists():
                    img_pil_orig = Image.open(icon_path)
                    if filename.lower().endswith(".png") and img_pil_orig.mode != 'RGBA':
                        img_pil_orig = img_pil_orig.convert('RGBA')

                    if maintain_aspect:
                        original_width, original_height = img_pil_orig.size
                        if original_height == 0: raise ValueError("Altura do ícone é zero")
                        target_width, target_height = size
                        aspect_ratio = original_width / original_height
                        if target_width / aspect_ratio <= target_height:
                            new_width = target_width
                            new_height = int(new_width / aspect_ratio)
                        else:
                            new_height = target_height
                            new_width = int(new_height * aspect_ratio)
                        size_to_resize = (new_width if new_width > 0 else 1, new_height if new_height > 0 else 1)
                    else:
                        size_to_resize = size
                    pil_image = img_pil_orig.resize(size_to_resize, Image.LANCZOS)
                else:
                    logging.warning(f"Arquivo de ícone não encontrado: {icon_path}")
            
            if pil_image is None and placeholder_text: 
                placeholder_img = Image.new('RGBA', size, (0,0,0,0))
                draw = ImageDraw.Draw(placeholder_img)
                try:
                    font_size = max(8, int(size[1] * 0.6))
                    font = ImageFont.truetype("DejaVuSans.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()
                
                text_bbox = draw.textbbox((0,0), placeholder_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                draw.text(((size[0] - text_width) // 2, (size[1] - text_height) // 2 - int(font_size*0.05)), 
                          placeholder_text, font=font, fill="grey")
                pil_image = placeholder_img

            if pil_image:
                return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)

        except Exception as e:
            logging.error(f"Erro ao carregar ícone CTk {filename or placeholder_text}: {e}")
        return None


    def _set_icon(self, icon_path: Path):
        try:
            if icon_path.exists():
                if os.name == 'nt':
                    if icon_path.suffix.lower() == '.ico':
                        self.root.iconbitmap(str(icon_path))
                    else: 
                        img = Image.open(icon_path)
                        photo = ImageTk.PhotoImage(img)
                        self.root.wm_iconphoto(True, photo) 
                else: 
                    img = Image.open(icon_path)
                    photo = ImageTk.PhotoImage(img)
                    self.root.wm_iconphoto(True, photo)
        except Exception as e:
            logging.error(f"[Icon Error] Não foi possível definir o ícone '{icon_path}': {e}")

    def populate_about_tab_content(self, parent_frame: ctk.CTkFrame):
        about_content_frame = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent")
        about_content_frame.pack(expand=True, fill="both")
        if hasattr(about_content_frame, "_scrollbar") and about_content_frame._scrollbar is not None:
            about_content_frame._scrollbar.grid_forget()

        about_page_logo_ctk = self._load_icon_ctk("logo1.png", size=(400, 100), maintain_aspect=True)
        if about_page_logo_ctk:
            ctk.CTkLabel(about_content_frame, image=about_page_logo_ctk, text="").pack(pady=(0, 20))
        
        ctk.CTkLabel(about_content_frame, text="Maratonando Animes", font=ctk.CTkFont(size=20, weight="bold")).pack()
        
        ctk.CTkLabel(about_content_frame, text="Criador: Marcos", font=ctk.CTkFont(size=14)).pack(pady=(10,0))
        ctk.CTkLabel(about_content_frame, text="Contato: marcosslprado@gmail.com", font=ctk.CTkFont(size=14)).pack()
        
        ctk.CTkLabel(about_content_frame, text="Me ajude a manter o projeto vivo!", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,5))
        ctk.CTkLabel(about_content_frame, text="Que tal um café? PIX: 83980601072", font=ctk.CTkFont(size=15, weight="bold"), text_color=("black","yellow")).pack()


    def refresh_history(self):
        self.load_history()
        self.update_status("Histórico atualizado.")

    def clear_history(self):
        if messagebox.askyesno("Limpar Histórico", "Tem certeza que deseja apagar TODO o histórico?\nEsta ação não pode ser desfeita.", parent=self.root):
            self.history_data = []
            self._update_history_display()
            self.save_history()
            self.update_status("Histórico limpo.")
        else:
            self.update_status("Limpeza do histórico cancelada.")

    def clear_search_results(self):
        self.search_entry.delete(0, "end")
        self._clear_scrollable_frame(self.search_results_scroll_frame)
        self.search_results_data = [] 
        self.total_search_results_data = [] 
        self.current_search_page = 1
        if hasattr(self, 'search_page_label'): 
            self.search_page_label.configure(text="Página -/-")
            self.prev_search_button.configure(state="disabled")
            self.next_search_button.configure(state="disabled")
        
        self._clear_scrollable_frame(self.episodes_scroll_frame)
        self.episode_details_data = {}
        self.anime_title_label_ep_tab.configure(text="Nenhum anime selecionado")
        self.anime_description_label_ep_tab.configure(text="")
        if self.placeholder_image_ctk:
            self.anime_cover_label.configure(image=self.placeholder_image_ctk)
        self.nav_episodes_button.configure(state="disabled")
        self.update_status("Resultados limpos. Pronto para nova busca.")


    def _clear_scrollable_frame(self, scrollable_frame: ctk.CTkScrollableFrame):
        if scrollable_frame:
            for widget in scrollable_frame.winfo_children():
                widget.destroy()

    def update_status(self, message):
        self.root.after(0, lambda: self.status_label.configure(text=message))

    def set_ui_state(self, state): 
        self.search_entry.configure(state=state)
        self.search_button_action.configure(state=state)
        self.clear_button_action.configure(state=state)

        history_button_state = state
        if hasattr(self, 'refresh_history_button'): self.refresh_history_button.configure(state=history_button_state)
        if hasattr(self, 'clear_history_button'): self.clear_history_button.configure(state=history_button_state)
        
        fav_button_state = "disabled"
        if state == "normal" and self.selected_history_item_widget:
            fav_button_state = "normal"
        if hasattr(self, 'toggle_favorite_button'): self.toggle_favorite_button.configure(state=fav_button_state)

        if state == "disabled":
            if hasattr(self, 'prev_episode_button'): self.prev_episode_button.configure(state="disabled")
            if hasattr(self, 'next_episode_button'): self.next_episode_button.configure(state="disabled")
            if hasattr(self, 'prev_search_button'): self.prev_search_button.configure(state="disabled")
            if hasattr(self, 'next_search_button'): self.next_search_button.configure(state="disabled")
        else: 
            if hasattr(self, 'total_search_results_data') and self.total_search_results_data:
                total_search_pages = math.ceil(len(self.total_search_results_data) / self.search_results_per_page)
                if hasattr(self, 'prev_search_button'): self.prev_search_button.configure(state="normal" if self.current_search_page > 1 else "disabled")
                if hasattr(self, 'next_search_button'): self.next_search_button.configure(state="normal" if self.current_search_page < total_search_pages else "disabled")
            
            if hasattr(self, 'episode_details_data') and self.episode_details_data.get('episodes'):
                total_ep_pages = math.ceil(len(self.episode_details_data['episodes']) / self.episodes_per_page)
                if hasattr(self, 'prev_episode_button'): self.prev_episode_button.configure(state="normal" if self.current_episode_page > 1 else "disabled")
                if hasattr(self, 'next_episode_button'): self.next_episode_button.configure(state="normal" if self.current_episode_page < total_ep_pages else "disabled")


    def load_history(self):
        home = Path.home()
        config_home = os.environ.get('XDG_CONFIG_HOME') or str(home / ".config")
        config_dir = Path(config_home) / "maratonando"
        config_dir.mkdir(parents=True, exist_ok=True)
        self.history_file_path = config_dir / HISTORY_FILE
        try:
            if self.history_file_path.exists():
                with open(self.history_file_path, 'r', encoding='utf-8') as f:
                    self.history_data = json.load(f)
            else:
                self.history_data = []
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"[History Error] Erro ao carregar histórico de '{self.history_file_path}': {e}")
            self.history_data = []
        self._update_history_display()


    def _update_history_display(self):
        self._clear_scrollable_frame(self.history_scroll_frame)
        self.selected_history_item_widget = None
        if hasattr(self, 'toggle_favorite_button'): self.toggle_favorite_button.configure(state="disabled")

        for item_data in reversed(self.history_data):
            prefix = "★ " if item_data.get("favorite") else ""
            display_text = f"{prefix}{item_data.get('anime_title', '?')} - {item_data.get('episode_title', '?')}"
            
            item_frame = ctk.CTkFrame(self.history_scroll_frame, corner_radius=5)
            item_frame.pack(fill="x", pady=2, padx=2)

            label = ctk.CTkLabel(item_frame, text=display_text, anchor="w")
            label.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            
            item_frame.history_item_data = item_data 
            label.history_item_data = item_data

            def on_click_factory(widget, data):
                def on_click(event=None):
                    if self.selected_history_item_widget and self.selected_history_item_widget.winfo_exists():
                        self.selected_history_item_widget.configure(fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
                    
                    widget.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"]) 
                    self.selected_history_item_widget = widget
                    if hasattr(self, 'toggle_favorite_button'): self.toggle_favorite_button.configure(state="normal")
                return on_click

            def on_double_click_factory(data):
                 return lambda event=None: self.on_history_select_custom(data)

            item_frame.bind("<Button-1>", on_click_factory(item_frame, item_data))
            label.bind("<Button-1>", on_click_factory(item_frame, item_data)) 
            item_frame.bind("<Double-Button-1>", on_double_click_factory(item_data))
            label.bind("<Double-Button-1>", on_double_click_factory(item_data))


    def save_history(self):
        if not hasattr(self, 'history_file_path'):
             logging.warning("[History Error] Caminho do arquivo de histórico não definido.")
             home = Path.home()
             config_home = os.environ.get('XDG_CONFIG_HOME') or str(home / ".config")
             config_dir = Path(config_home) / "maratonando"
             config_dir.mkdir(parents=True, exist_ok=True)
             self.history_file_path = config_dir / HISTORY_FILE
        try:
            with open(self.history_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            logging.error(f"[History Error] Erro ao salvar histórico em '{self.history_file_path}': {e}")

    def add_to_history(self, anime_title, episode_title, episode_url, anime_url, anime_image_url):
        if not all([anime_title, episode_title, episode_url, anime_url]):
             logging.warning(f"Dados incompletos para histórico: AT='{anime_title}', ET='{episode_title}', EU='{episode_url}', AU='{anime_url}'")
             return
        existing_item = next((item for item in self.history_data if item.get('episode_url') == episode_url), None)
        is_favorite = existing_item['favorite'] if existing_item and 'favorite' in existing_item else False
        if existing_item: logging.debug(f"Item {episode_title} já existe. Favorito: {is_favorite}")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        new_entry = {"anime_title": anime_title, "episode_title": episode_title, "episode_url": episode_url,
                     "anime_url": anime_url, "anime_image_url": anime_image_url, "timestamp": timestamp,
                     "parser": self.active_parser_name, "favorite": is_favorite }
        self.history_data = [item for item in self.history_data if item.get('episode_url') != episode_url]
        self.history_data.append(new_entry)
        max_history = 100
        if len(self.history_data) > max_history: self.history_data = self.history_data[-max_history:]
        self.save_history()
        self._update_history_display() 


    def toggle_favorite_selected(self):
        if not self.selected_history_item_widget or not hasattr(self.selected_history_item_widget, 'history_item_data'):
            self.update_status("Nenhum item do histórico selecionado para favoritar.")
            return
        
        selected_data = self.selected_history_item_widget.history_item_data
        
        found = False
        for item in self.history_data:
            if item.get('episode_url') == selected_data.get('episode_url'):
                item["favorite"] = not item.get("favorite", False)
                found = True
                break
        if found:
            self.save_history()
            self._update_history_display() 
            self.update_status(f"Favorito {'adicionado' if selected_data.get('favorite') else 'removido'}.")
        else:
            self.update_status("Erro ao atualizar favorito: item não encontrado nos dados.")


    def start_search_thread(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            messagebox.showwarning("Busca", "Digite um termo para buscar.", parent=self.root)
            return
        self.update_status(f"Buscando por '{query}'...")
        self.set_ui_state("disabled")
        self._clear_scrollable_frame(self.search_results_scroll_frame)
        self.search_results_data = [] 
        self.total_search_results_data = [] 
        self.current_search_page = 1
        self.last_selected_episode_listbox_index = -1
        self.show_page("search")
        thread = threading.Thread(target=self.perform_search, args=(query,), daemon=True)
        thread.start()

    def perform_search(self, query):
        try:
            results = self.active_parser.search(query)
            self.total_search_results_data = results
            logging.info(f"[GUI] perform_search retornou {len(results)} resultados do parser.") 
            
            def _process_thread_results():
                self.set_ui_state("normal")
                self.current_search_page = 1 
                self.update_search_results_display() 
                
                if self.target_episode_url_from_history and self.selected_anime_url_for_history:
                    found_anime_for_history = next((anime for anime in self.total_search_results_data if anime.get('url') == self.selected_anime_url_for_history), None)
                    if found_anime_for_history:
                        logging.info(f"Histórico: Anime '{found_anime_for_history.get('title')}' encontrado. Selecionando...")
                        self._on_custom_anime_select(found_anime_for_history) 
                    else:
                        logging.warning(f"Histórico: Anime com URL '{self.selected_anime_url_for_history}' não encontrado.")
                        self.update_status(f"Anime '{self.selected_anime_title}' do histórico não encontrado.")
                        self.target_episode_url_from_history = None
                        self.selected_anime_url_for_history = None

            self.root.after(0, _process_thread_results)
        except Exception as e:
            logging.exception(f"ERRO na busca por '{query}' com parser '{self.active_parser_name}'")
            self.update_status(f"Erro na busca: {e}")
            self.root.after(0, lambda: self.set_ui_state("normal"))
            self.root.after(0, lambda err=e: messagebox.showerror("Erro", f"Erro ao buscar: {err}", parent=self.root))
            self.target_episode_url_from_history = None

    def update_search_results_display(self):
        """Atualiza a exibição dos resultados da busca com paginação."""
        self._clear_scrollable_frame(self.search_results_scroll_frame)

        if not self.total_search_results_data:
            ctk.CTkLabel(self.search_results_scroll_frame, text="Nenhum anime encontrado.").pack(pady=10)
            self.update_status("Nenhum anime encontrado.")
            self.search_page_label.configure(text="Página -/-")
            self.prev_search_button.configure(state="disabled")
            self.next_search_button.configure(state="disabled")
            return

        total_results = len(self.total_search_results_data)
        total_pages = math.ceil(total_results / self.search_results_per_page)

        if self.current_search_page < 1: self.current_search_page = 1
        if self.current_search_page > total_pages and total_pages > 0: self.current_search_page = total_pages
        elif total_pages == 0 : self.current_search_page = 1 

        start_index = (self.current_search_page - 1) * self.search_results_per_page
        end_index = start_index + self.search_results_per_page
        results_to_display = self.total_search_results_data[start_index:end_index]

        if not results_to_display and total_results > 0:
            ctk.CTkLabel(self.search_results_scroll_frame, text="Nenhum resultado nesta página.").pack(pady=10)
        else:
            for i, result in enumerate(results_to_display):
                        item_frame = ctk.CTkFrame(self.search_results_scroll_frame, corner_radius=5)
                        item_frame.pack(fill="x", pady=3, padx=3)
                        item_frame.grid_columnconfigure(1, weight=1)

                        list_cover_width = 60
                        list_cover_height = 90
                        
                        cover_label = ctk.CTkLabel(item_frame, text="Carreg...", width=list_cover_width, height=list_cover_height)
                        cover_label.grid(row=0, column=0, padx=5, pady=5, sticky="n")
                        
                        title_text = result.get('title', 'Título Desconhecido')

                        cover_url = result.get('image') or result.get('cover_url')

                        # Cores para o efeito hover
                        original_color = item_frame.cget("fg_color")
                        hover_color = ("gray75", "gray25") # (light_mode, dark_mode)

                        def on_enter(event, frame=item_frame, h_color=hover_color):
                            frame.configure(fg_color=h_color)
                        def on_leave(event, frame=item_frame, o_color=original_color):
                            frame.configure(fg_color=o_color)

                        if cover_url:
                            threading.Thread(target=self._load_search_result_cover_async_ctk, args=(cover_url, cover_label, (list_cover_width, list_cover_height)), daemon=True).start()
                        else:
                            placeholder_icon = self._load_icon_ctk(None, (list_cover_width, list_cover_height), "Sem Capa")
                            if placeholder_icon:
                                cover_label.configure(image=placeholder_icon, text="")
                        title_label = ctk.CTkLabel(item_frame, text=title_text, anchor="w", justify="left", font=ctk.CTkFont(size=13))
                        title_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

                        def _create_select_command(anime_result):
                            return lambda event=None: self._on_custom_anime_select(anime_result)

                        item_frame.bind("<Button-1>", _create_select_command(result))
                        cover_label.bind("<Button-1>", _create_select_command(result))
                        title_label.bind("<Button-1>", _create_select_command(result))
                        
                        # Adicionar bindings para o efeito hover ao item_frame e seus filhos diretos visíveis
                        item_frame.bind("<Enter>", on_enter)
                        item_frame.bind("<Leave>", on_leave)
                        # Vincular também aos filhos para manter o hover
                        cover_label.bind("<Enter>", on_enter)
                        cover_label.bind("<Leave>", on_leave)
                        title_label.bind("<Enter>", on_enter)
                        title_label.bind("<Leave>", on_leave)

                        item_frame.configure(cursor="hand2")
                        cover_label.configure(cursor="hand2")
                        title_label.configure(cursor="hand2")

                        # Adicionar separador visual, exceto para o último item da página (opcional)
                        # if i < len(results_to_display) - 1: # Descomente se não quiser separador após o último
                        separator = ctk.CTkFrame(self.search_results_scroll_frame, height=1, fg_color=("gray80", "gray20"))
                        separator.pack(fill="x", padx=5, pady=(0,3)) # pady no bottom para espaço antes do próximo item

        self.update_status(f"Mostrando {len(results_to_display)} de {total_results} resultados.")
        self.search_page_label.configure(text=f"Página {self.current_search_page}/{total_pages if total_pages > 0 else 1}")
        self.prev_search_button.configure(state="normal" if self.current_search_page > 1 else "disabled")
        self.next_search_button.configure(state="normal" if self.current_search_page < total_pages else "disabled")

    def go_to_previous_search_page(self):
        if self.current_search_page > 1:
            self.current_search_page -= 1
            self.update_search_results_display()

    def go_to_next_search_page(self):
        if not self.total_search_results_data: return
        total_pages = math.ceil(len(self.total_search_results_data) / self.search_results_per_page)
        if self.current_search_page < total_pages:
            self.current_search_page += 1
            self.update_search_results_display()


    def update_anime_cover_ctk(self, image_url, anime_title_text="Selecione um anime"):
        if not hasattr(self, 'anime_cover_label') or self.anime_cover_label is None:
            logging.warning("Label da capa (pág episódios) não inicializada.")
            return

        self.anime_title_label_ep_tab.configure(text=anime_title_text)

        if image_url:
            logging.debug(f"Iniciando carregamento da imagem (pág episódios): {image_url}")
            threading.Thread(target=self._load_image_async_ctk, args=(image_url, self.anime_cover_label, (int(self.target_cover_height * (2/3)), self.target_cover_height)), daemon=True).start()
        else:
            if self.placeholder_image_ctk:
                logging.debug("URL da imagem não fornecida, usando placeholder (pág episódios).")
                self.anime_cover_label.configure(image=self.placeholder_image_ctk)
            else:
                 self.anime_cover_label.configure(image=None)


    def _load_image_async_ctk(self, image_url, target_label: ctk.CTkLabel, target_size: tuple):
        cache_filepath = self._get_cache_filepath(image_url)
        original_img = None

        if cache_filepath and cache_filepath.exists():
            try:
                logging.debug(f"Carregando imagem do cache: {cache_filepath}")
                original_img = Image.open(cache_filepath)
            except Exception as e:
                logging.warning(f"Erro ao carregar imagem do cache {cache_filepath}: {e}. Tentando baixar...")
                original_img = None # Força o download

        if original_img is None: # Se não estiver no cache ou falhou ao carregar do cache
            try:
                logging.debug(f"Baixando imagem: {image_url}")
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(image_url, stream=True, timeout=10, headers=headers)
                response.raise_for_status()
                image_bytes = response.content
                original_img = Image.open(BytesIO(image_bytes))
                
                if cache_filepath: # Salva no cache
                    try:
                        original_img.save(cache_filepath, format='PNG') # Salva como PNG
                        logging.debug(f"Imagem salva no cache: {cache_filepath}")
                    except Exception as e:
                        logging.warning(f"Erro ao salvar imagem no cache {cache_filepath}: {e}")
            except Exception as e:
                logging.error(f"Erro ao baixar imagem {image_url}: {e}")
                if target_label.winfo_exists() and self.placeholder_image_ctk:
                     self.root.after(0, lambda: target_label.configure(image=self.placeholder_image_ctk, text=""))
                return

        if original_img:
            try:
                original_width, original_height = original_img.size
                if original_height == 0 or original_width == 0:
                    raise ValueError("Dimensões da imagem original são zero.")

                target_w, target_h = target_size
                img_aspect = original_width / original_height
                
                new_width = target_w if target_w / img_aspect <= target_h else int(target_h * img_aspect)
                new_height = int(new_width / img_aspect) if target_w / img_aspect <= target_h else target_h
                
                new_width = max(1, new_width)
                new_height = max(1, new_height)

                img_resized = original_img.resize((new_width, new_height), Image.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(new_width, new_height))
                if target_label.winfo_exists():
                    self.root.after(0, lambda: target_label.configure(image=ctk_image, text=""))
            except Exception as e:
                logging.error(f"Erro ao processar imagem (possivelmente do cache) {image_url}: {e}")
                if target_label.winfo_exists() and self.placeholder_image_ctk:
                    self.root.after(0, lambda: target_label.configure(image=self.placeholder_image_ctk, text=""))


    def _load_search_result_cover_async_ctk(self, image_url, target_label: ctk.CTkLabel, target_size: tuple):
        cache_filepath = self._get_cache_filepath(image_url)
        original_img = None

        if cache_filepath and cache_filepath.exists():
            try:
                logging.debug(f"Carregando capa da lista do cache: {cache_filepath}")
                original_img = Image.open(cache_filepath)
            except Exception as e:
                logging.warning(f"Erro ao carregar capa da lista do cache {cache_filepath}: {e}. Tentando baixar...")
                original_img = None

        if original_img is None:
            try:
                logging.debug(f"Baixando capa da lista: {image_url}")
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(image_url, stream=True, timeout=10, headers=headers)
                response.raise_for_status()
                image_bytes = response.content
                original_img = Image.open(BytesIO(image_bytes))
                if cache_filepath:
                    try:
                        original_img.save(cache_filepath, format='PNG')
                        logging.debug(f"Capa da lista salva no cache: {cache_filepath}")
                    except Exception as e:
                        logging.warning(f"Erro ao salvar capa da lista no cache {cache_filepath}: {e}")
            except Exception as e:
                logging.warning(f"Erro ao baixar capa da lista ({image_url}): {e}.")
                if target_label.winfo_exists():
                    placeholder_icon = self._load_icon_ctk(None, target_size, "Erro")
                    if placeholder_icon:
                        self.root.after(0, lambda: target_label.configure(image=placeholder_icon, text=""))
                return

        if original_img:
            try:
                target_w, target_h = target_size
                original_width, original_height = original_img.size
                if original_width == 0 or original_height == 0: return

                bg_color_hex = self._get_frame_bg_color()
                final_img_obj = Image.new('RGB', (target_w, target_h), bg_color_hex)

                img_aspect = original_width / original_height
                scaled_w = target_w if target_w / img_aspect <= target_h else int(target_h * img_aspect)
                scaled_h = int(scaled_w / img_aspect) if target_w / img_aspect <= target_h else target_h
                scaled_w = max(1, scaled_w)
                scaled_h = max(1, scaled_h)

                img_resized_content = original_img.resize((scaled_w, scaled_h), Image.LANCZOS)
                paste_x = (target_w - scaled_w) // 2
                paste_y = (target_h - scaled_h) // 2
                final_img_obj.paste(img_resized_content, (paste_x, paste_y))
                
                ctk_image = ctk.CTkImage(light_image=final_img_obj, dark_image=final_img_obj, size=target_size)
                if target_label.winfo_exists():
                    self.root.after(0, lambda: target_label.configure(image=ctk_image, text=""))
            except Exception as e:
                logging.warning(f"Erro ao processar capa da lista (possivelmente do cache) ({image_url}): {e}.")
                if target_label.winfo_exists():
                    placeholder_icon = self._load_icon_ctk(None, target_size, "Erro")
                    if placeholder_icon:
                        self.root.after(0, lambda: target_label.configure(image=placeholder_icon, text=""))

    def _get_frame_bg_color(self):
        """Obtém a cor de fundo apropriada para os placeholders de imagem."""
        bg_color_hex = None
        try:
            if ctk.get_appearance_mode().lower() == "dark":
                bg_color_hex = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1] 
            else:
                bg_color_hex = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][0] 
        except (KeyError, IndexError, TypeError, AttributeError): # AttributeError para ThemeManager
            pass # Usa o fallback

        if not bg_color_hex or not isinstance(bg_color_hex, str) or not bg_color_hex.startswith("#"):
            bg_color_hex = "#2b2b2b" if ctk.get_appearance_mode().lower() == "dark" else "#dbdbdb"
        return bg_color_hex

    def _start_logo_cycling_thread(self):
        if hasattr(self, 'header_logo_label') and self.header_logo_label and self.logo_images_filenames:
            self.logo_images_ctk = [self._load_icon_ctk(name, size=(690,150), maintain_aspect=True) for name in self.logo_images_filenames]
            self.logo_images_ctk = [img for img in self.logo_images_ctk if img is not None] 
            if len(self.logo_images_ctk) > 1:
                thread = threading.Thread(target=self._cycle_logo_task, daemon=True)
                thread.start()
                logging.info(f"Thread de ciclo de logos iniciada.")
            else:
                logging.info("Ciclo de logos desativado (logos insuficientes).")
        else:
            logging.info("Ciclo de logos desativado (label do logo não existe).")


    def _cycle_logo_task(self):
        try:
            while True:
                time.sleep(self.logo_cycle_interval)
                if hasattr(self, 'header_logo_label') and self.header_logo_label.winfo_exists() and self.logo_images_ctk:
                    self.current_logo_index = (self.current_logo_index + 1) % len(self.logo_images_ctk)
                    next_logo_ctk = self.logo_images_ctk[self.current_logo_index]
                    self.root.after(0, lambda: self.header_logo_label.configure(image=next_logo_ctk))
        except Exception as ex:
            logging.error(f"Erro na thread _cycle_logo_task: {ex}", exc_info=True)


    def _on_custom_anime_select(self, selected_anime_info):
        if selected_anime_info:
            self.selected_anime_title = selected_anime_info.get('title', 'Anime Desconhecido')
            self.selected_anime_url_for_history = selected_anime_info.get('url')
            self.update_status(f"Carregando: {self.selected_anime_title}...")
            self.current_anime_search_result_info = selected_anime_info # Armazena info da busca
            self._clear_scrollable_frame(self.episodes_scroll_frame)
            if hasattr(self, 'episode_page_label'): self.episode_page_label.configure(text="Carregando...")
            
            self.episode_details_data = {}
            self.last_selected_episode_listbox_index = -1 
            
            self.update_anime_cover_ctk(self.current_anime_search_result_info.get('image') or self.current_anime_search_result_info.get('cover_url'), self.selected_anime_title)
            
            self.show_page("episodes")
            self.nav_episodes_button.configure(state="normal")
            
            thread = threading.Thread(target=self.perform_fetch_episodes, args=(selected_anime_info['url'],), daemon=True)
            thread.start()

    def _re_enable_episode_selection(self):
        self.set_ui_state("normal") 
        self.last_selected_episode_listbox_index = -1
        self.target_episode_url_from_history = None

    def update_episode_list_page(self):
        self.is_updating_episodes = True
        if not hasattr(self, 'episodes_scroll_frame'):
            self.is_updating_episodes = False
            return
        self._clear_scrollable_frame(self.episodes_scroll_frame)
        
        all_episodes = self.episode_details_data.get('episodes', [])
        total_episodes = len(all_episodes)

        if not all_episodes:
            self.update_status("Nenhum episódio encontrado para este anime.")
            if hasattr(self, 'episode_page_label'): self.episode_page_label.configure(text="Página -/-")
            if hasattr(self, 'prev_episode_button'): self.prev_episode_button.configure(state="disabled")
            if hasattr(self, 'next_episode_button'): self.next_episode_button.configure(state="disabled")
            self.is_updating_episodes = False
            return

        total_pages = math.ceil(total_episodes / self.episodes_per_page)
        if self.current_episode_page < 1: self.current_episode_page = 1
        if self.current_episode_page > total_pages: self.current_episode_page = total_pages

        start_index = (self.current_episode_page - 1) * self.episodes_per_page
        end_index = start_index + self.episodes_per_page
        episodes_to_display = all_episodes[start_index:end_index]

        try:
            for i, episode_data in enumerate(episodes_to_display):
                global_ep_num = start_index + i + 1
                title_to_insert = episode_data.get('title', 'Título Desconhecido')
                display_text = f"{global_ep_num}. {title_to_insert}"
                episode_url = episode_data.get('url')

                is_watched = any(hist_item.get('episode_url') == episode_url for hist_item in self.history_data)
                
                button_text_color = None
                if is_watched:
                    display_text = f"✓ {display_text}"
                    # Cor para episódios assistidos: (light_mode, dark_mode)
                    button_text_color = ("orchid3", "orchid2") 
                
                ep_button = ctk.CTkButton(
                    self.episodes_scroll_frame,
                    text=display_text,
                    anchor="w",
                    command=lambda ep=episode_data, idx=i: self._on_episode_button_click(ep, idx),
                    text_color=button_text_color # Define a cor do texto se o episódio foi assistido
                )
                ep_button.pack(fill="x", pady=2, padx=2)

                if self.target_episode_url_from_history and episode_data.get('url') == self.target_episode_url_from_history:
                    self.last_selected_episode_listbox_index = i 
                    self.update_status(f"Episódio {global_ep_num} selecionado. Clique novamente para assistir.")
            self.update_status(f"Mostrando {len(episodes_to_display)} de {total_episodes} episódios.")
            if self.target_episode_url_from_history: 
                 self.target_episode_url_from_history = None

        except Exception as insert_err:
            logging.exception(f"ERRO ao criar botões de episódios: {insert_err}")
            self.update_status("Erro ao exibir episódios.")

        if hasattr(self, 'episode_page_label'): self.episode_page_label.configure(text=f"Página {self.current_episode_page}/{total_pages}")
        if hasattr(self, 'prev_episode_button'): self.prev_episode_button.configure(state="normal" if self.current_episode_page > 1 else "disabled")
        if hasattr(self, 'next_episode_button'): self.next_episode_button.configure(state="normal" if self.current_episode_page < total_pages else "disabled")
        self.is_updating_episodes = False


    def _on_episode_button_click(self, episode_data, listbox_index_equivalent):
        """Chamado quando um botão de episódio é clicado."""
        if self.is_updating_episodes: return

        if listbox_index_equivalent == self.last_selected_episode_listbox_index:
            self.current_selected_episode = episode_data
            self.update_status(f"Obtendo vídeo para: {episode_data['title']}...")
            self.set_ui_state("disabled") 
            thread = threading.Thread(target=self.perform_get_video, args=(episode_data['url'],), daemon=True)
            thread.start()
        else:
            self.last_selected_episode_listbox_index = listbox_index_equivalent
            start_index = (self.current_episode_page - 1) * self.episodes_per_page
            global_ep_num = start_index + listbox_index_equivalent + 1
            self.update_status(f"Episódio {global_ep_num} selecionado. Clique novamente para assistir.")

    def go_to_previous_page(self):
        if self.current_episode_page > 1:
            self.current_episode_page -= 1
            self.last_selected_episode_listbox_index = -1
            self.update_episode_list_page()

    def go_to_next_page(self):
        all_episodes = self.episode_details_data.get('episodes', [])
        total_pages = math.ceil(len(all_episodes) / self.episodes_per_page)
        if self.current_episode_page < total_pages:
            self.current_episode_page += 1
            self.last_selected_episode_listbox_index = -1
            self.update_episode_list_page()

    def perform_fetch_episodes(self, anime_url):
        try:
            details = self.active_parser.get_details(anime_url)
            self.episode_details_data = details
            
            # Passa a URL da imagem original da busca como fallback
            original_image_url_from_search = None
            if hasattr(self, 'current_anime_search_result_info') and self.current_anime_search_result_info:
                original_image_url_from_search = self.current_anime_search_result_info.get('image') or self.current_anime_search_result_info.get('cover_url')
            self.root.after(0, lambda: self._update_details_gui_ctk(details, original_image_url_from_search))
            
            target_page = 1
            if self.target_episode_url_from_history and details and 'episodes' in details:
                all_episodes = details['episodes']
                target_index = next((i for i, ep in enumerate(all_episodes) if ep.get('url') == self.target_episode_url_from_history), -1)
                if target_index != -1:
                    target_page = math.floor(target_index / self.episodes_per_page) + 1
            
            self.current_episode_page = target_page
            self.root.after(0, self.update_episode_list_page)
            self.root.after(100, self._re_enable_episode_selection)
        except Exception as e:
            logging.exception(f"ERRO ao buscar episódios para {anime_url}")
            def handle_fetch_error(error_exception):
                self.episode_details_data = {'episodes': []}
                self.update_anime_cover_ctk(None, self.selected_anime_title)
                self.update_episode_list_page()
                self.update_status(f"Erro ao carregar episódios: {error_exception}")
                messagebox.showerror("Erro", f"Erro ao carregar episódios: {error_exception}", parent=self.root)
            self.root.after(0, lambda err_e=e: handle_fetch_error(err_e))
    
    def _update_details_gui_ctk(self, details, fallback_image_url=None):
        if not details:
            self.update_anime_cover_ctk(fallback_image_url, "Detalhes não encontrados")
            self.anime_description_label_ep_tab.configure(text="")
            return
        
        anime_title_from_details = details.get('title', self.selected_anime_title)
        if anime_title_from_details:
            self.selected_anime_title = anime_title_from_details

        # Prioriza imagem dos detalhes, depois fallback, depois placeholder
        image_url_from_details = details.get('cover_url') or details.get('image') or fallback_image_url

        self.update_anime_cover_ctk(image_url_from_details, self.selected_anime_title)
        
        description = details.get('description', '')
        self.anime_description_label_ep_tab.configure(text=description if description else "")


    def on_history_select_custom(self, selected_history_item): 
        if not selected_history_item: return

        anime_title_from_history = selected_history_item.get('anime_title', '')
        anime_url_from_history = selected_history_item.get('anime_url')
        self.target_episode_url_from_history = selected_history_item.get('episode_url')
        parser_from_history = selected_history_item.get('parser', self.active_parser_name)

        if not all([anime_title_from_history, anime_url_from_history, self.target_episode_url_from_history]):
            self.update_status("Dados do histórico incompletos.")
            self.target_episode_url_from_history = None
            return

        # Apenas o parser AnimeFire é suportado agora
        if parser_from_history != "AnimeFire":
            messagebox.showwarning("Servidor Indisponível", f"O item do histórico foi assistido em um servidor ('{parser_from_history}') que não está mais ativo. A busca será feita no servidor padrão.", parent=self.root)
        
        self.selected_anime_title = anime_title_from_history
        self.selected_anime_url_for_history = anime_url_from_history

        self.show_page("search")
        cleaned_title_for_search = self._clean_title_for_search(anime_title_from_history)
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, cleaned_title_for_search)

        logging.info(f"Histórico: Buscando diretamente com o parser padrão.")
        self.start_search_thread()


    def _clean_title_for_search(self, title):
        temp_title = re.sub(r'\s*\((Dublado|Legendado|HD|SD|FullHD)\)\s*$', '', title, flags=re.IGNORECASE)
        return temp_title.strip()


    def perform_get_video(self, episode_page_url):
        try:
            video_sources = self.active_parser.get_video_source(episode_page_url)
            if not video_sources:
                self.root.after(0, lambda: (
                    self.update_status("Falha ao obter o link do vídeo do site."),
                    messagebox.showerror("Erro", "Não foi possível obter o link do vídeo do site.\nO link pode estar quebrado ou o site offline.", parent=self.root),
                    self._re_enable_episode_selection()
                ))
                return

            chosen_source = None
            episode_url_for_history = episode_page_url
            episode_title_for_history = self.current_selected_episode.get('title', 'Episódio') if self.current_selected_episode else 'Episódio'

            if len(video_sources) == 1:
                self.root.after(0, self._handle_single_video_source, video_sources[0], episode_url_for_history, episode_title_for_history)
            else:
                self.root.after(0, self._prompt_for_video_quality, video_sources, episode_url_for_history, episode_title_for_history)

        except Exception as e:
            logging.exception(f"ERRO GERAL ao obter vídeo para {episode_page_url}")
            self.root.after(0, lambda err_msg=str(e): (
                self.update_status(f"Erro ao obter vídeo: {err_msg}"),
                messagebox.showerror("Erro", f"Erro ao obter vídeo: {err_msg}", parent=self.root),
                self._re_enable_episode_selection()
            ))

    def _handle_single_video_source(self, chosen_source, episode_url_for_history, episode_title_for_history):
        """Lida com o caso de uma única fonte de vídeo, chamado pela thread principal."""
        self.update_status(f"Fonte única encontrada ({chosen_source.get('label', 'N/A')}). Tocando...")
        video_url_to_play = chosen_source['src']
        self.play_selected_video(video_url_to_play, episode_url_for_history, episode_title_for_history)

    def _prompt_for_video_quality(self, video_sources, episode_url_for_history, episode_title_for_history):
        """Cria e mostra o diálogo de seleção de qualidade, chamado pela thread principal."""
        dialog = ctk.CTkInputDialog(
            text="Qualidades disponíveis:\n" + "\n".join([f"{i+1}. {s.get('label', f'Opção {i+1}')}" for i, s in enumerate(video_sources)]) + "\n\nDigite o NÚMERO da opção:",
            title="Seleção de Qualidade"
        )
        choice_num_str = dialog.get_input() 

        selected_source = None
        if choice_num_str:
            try:
                choice_index = int(choice_num_str) - 1
                if 0 <= choice_index < len(video_sources):
                    selected_source = video_sources[choice_index]
                else:
                    self.update_status("Seleção inválida.")
                    messagebox.showwarning("Seleção Inválida", "Número da opção inválido.", parent=self.root)
            except ValueError:
                self.update_status("Entrada inválida.")
                messagebox.showwarning("Seleção Inválida", "Por favor, digite um número.", parent=self.root)
        else: 
            self.update_status("Seleção cancelada.")
            self._re_enable_episode_selection()

        if selected_source:
            self.update_status(f"Opção {selected_source.get('label', 'N/A')} selecionada. Tocando...")
            video_url_to_play = selected_source['src']
            self.play_selected_video(video_url_to_play, episode_url_for_history, episode_title_for_history)
        elif choice_num_str: 
             self._re_enable_episode_selection()


    def _run_play_video_thread(self, video_url, title):
        try:
            self.player.play_episode(video_url, title=title, referer=None)
        except FileNotFoundError:
             logging.error(f"Erro FileNotFoundError ao tentar executar play_video (mpv não encontrado?).")
        except Exception as play_err:
             logging.exception(f"Erro inesperado na thread do player")
        finally:
            logging.debug("Player fechado ou falhou. Agendando reabilitação da UI.")
            self.root.after(0, self._re_enable_episode_selection)


    def play_selected_video(self, video_url_to_play, episode_url_original, episode_title_original):
        if not video_url_to_play:
            self.update_status("Fonte de vídeo inválida.")
            messagebox.showerror("Erro", "Fonte de vídeo inválida.", parent=self.root)
            self.root.after(0, self._re_enable_episode_selection)
            return

        try:
            anime_image_url_for_history = self.episode_details_data.get('cover_url')
            if not anime_image_url_for_history and self.search_results_data:
                matching_anime = next((anime for anime in self.search_results_data if anime.get('url') == self.selected_anime_url_for_history), None)
                if matching_anime:
                    anime_image_url_for_history = matching_anime.get('image')
            self.add_to_history(self.selected_anime_title, episode_title_original, episode_url_original, self.selected_anime_url_for_history, anime_image_url_for_history)
        except Exception as history_err:
            logging.exception(f"Erro ao adicionar ao histórico: {history_err}")

        self.update_status(f"Iniciando player...")
        
        popup = ctk.CTkToplevel(self.root)
        popup.title("Carregando")
        popup.geometry("300x100")
        popup.resizable(False, False)
        popup.transient(self.root) 
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        popup_x = root_x + (root_w // 2) - (300 // 2)
        popup_y = root_y + (root_h // 2) - (100 // 2)
        popup.geometry(f"+{popup_x}+{popup_y}")

        ctk.CTkLabel(popup, text="Iniciando player...\nAguarde de 5 a 30 segundos.", justify="center").pack(expand=True, fill="both", padx=10, pady=10)
        
        popup_duration = 8000 
        
        def destroy_popup_if_exists():
            if popup.winfo_exists():
                popup.destroy()

        self.root.after(popup_duration, destroy_popup_if_exists)

        try:
            player_thread = threading.Thread(
                target=self._run_play_video_thread,
                args=(video_url_to_play, f"{self.selected_anime_title} - {episode_title_original}"),
                daemon=True)
            player_thread.start()
        except FileNotFoundError:
             self.update_status("Erro: Comando 'mpv' não encontrado.")
             logging.error(f"play_selected_video: ERRO - mpv não encontrado")
             destroy_popup_if_exists()
             messagebox.showerror("Erro", "Player 'mpv' não encontrado. Verifique a instalação.", parent=self.root)
             self.root.after(0, self._re_enable_episode_selection)
        except Exception as play_err:
             logging.exception(f"play_selected_video: ERRO ao chamar play_video/criar popup")
             self.update_status(f"Erro ao iniciar player.")
             destroy_popup_if_exists()
             messagebox.showerror("Erro ao Iniciar Player", f"Não foi possível iniciar o player MPV.\n\nCausas comuns:\n- O link do vídeo pode ter expirado ou estar protegido.\n- Problema na instalação do MPV.\n\nErro: {play_err}", parent=self.root)
             self.root.after(0, self._re_enable_episode_selection)


# Adicione esta função para encapsular a inicialização da GUI
def main_gui_func():
    root = ctk.CTk()
    app = AnimeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main_gui_func() # Chame a nova função
