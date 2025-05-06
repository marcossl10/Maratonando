# /home/marcos/Maratonando/maratonando_src/gui.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import json
import os
import sv_ttk
import threading
import time
import math
import re
from pathlib import Path
import sys

from .core.parsers import animefire_parser
from .core.player import play_video

HISTORY_FILE = "history.json" # Nome do arquivo de histórico

class AnimeApp:
    def __init__(self, root):
        self.root = root

        installed_icon_path = Path("/usr/share/maratonando/icons/maratonando.png")
        dev_icon_path = Path(__file__).parent.parent / "icons" / "maratonando.png"
        # Usa o caminho instalado se existir, senão usa o de desenvolvimento
        icon_path = installed_icon_path if installed_icon_path.exists() else dev_icon_path
        self._set_icon(icon_path)

        self.root.title("Maratonando Animes")

        sv_ttk.set_theme("dark")

        # Configura cores para widgets Tk clássicos (Listbox)
        self.listbox_bg = "#2b2b2b"
        self.listbox_fg = "#ffffff"
        self.listbox_select_bg = "#0078d4"

        self.root.geometry("700x500")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.search_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.search_tab, text="Buscar")

        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text="Histórico")

        self.about_tab = ttk.Frame(self.notebook) # Cria a frame para a nova aba
        self.notebook.add(self.about_tab, text="Sobre") # Adiciona a aba "Sobre"

        self.search_controls_frame = ttk.Frame(self.search_tab)
        self.search_controls_frame.pack(pady=5)

        self.search_label = ttk.Label(self.search_controls_frame, text="Buscar Anime:")
        self.search_label.pack(pady=5)

        self.search_entry = ttk.Entry(self.search_controls_frame, width=40)
        self.search_entry.pack(pady=5)
        self.search_entry.bind("<Return>", self.start_search_thread) # Buscar ao pressionar Enter

        self.button_frame = ttk.Frame(self.search_controls_frame)
        self.button_frame.pack(pady=5)

        self.search_button = ttk.Button(self.button_frame, text="Buscar", command=self.start_search_thread)
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(self.button_frame, text="Limpar", command=self.clear_search_results)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.results_label = ttk.Label(self.search_tab, text="Faça uma busca para ver os resultados")
        self.results_label.pack(pady=(5,0))

        self.results_frame = ttk.Frame(self.search_tab)
        self.results_frame.pack(pady=(10, 0), fill=tk.BOTH, expand=True)

        self.results_subframe = ttk.Frame(self.results_frame)
        self.results_subframe.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.results_scrollbar = ttk.Scrollbar(self.results_subframe, orient=tk.VERTICAL)
        self.results_listbox = tk.Listbox(
            self.results_subframe,
            width=50, height=10,
            yscrollcommand=self.results_scrollbar.set,
            bg=self.listbox_bg, fg=self.listbox_fg,
            selectbackground=self.listbox_select_bg,
            borderwidth=0, highlightthickness=0
        )
        self.results_scrollbar.config(command=self.results_listbox.yview)
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.results_listbox.bind("<<ListboxSelect>>", self.on_anime_select)

        self.episodes_subframe = ttk.Frame(self.results_frame)
        self.episodes_subframe.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        self.episodes_listbox = tk.Listbox(
            self.episodes_subframe, width=30, height=10,
            bg=self.listbox_bg, fg=self.listbox_fg,
            selectbackground=self.listbox_select_bg,
            borderwidth=0, highlightthickness=0
        )
        self.episodes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.episodes_listbox.bind("<<ListboxSelect>>", self.on_episode_select)

        self.episode_pagination_frame = ttk.Frame(self.search_tab)
        self.episode_pagination_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 10))

        self.prev_episode_button = ttk.Button(self.episode_pagination_frame, text="< Anterior", command=self.go_to_previous_page, state=tk.DISABLED)
        self.next_episode_button = ttk.Button(self.episode_pagination_frame, text="Próximo >", command=self.go_to_next_page, state=tk.DISABLED)

        self.next_episode_button.pack(side=tk.RIGHT, padx=5)
        self.prev_episode_button.pack(side=tk.LEFT, padx=5)
        self.episode_page_label = ttk.Label(self.episode_pagination_frame, text="Página -/-")
        self.episode_page_label.pack(side=tk.LEFT, padx=5)

        self.history_list_frame = ttk.Frame(self.history_tab)
        self.history_list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.history_scrollbar = ttk.Scrollbar(self.history_list_frame, orient=tk.VERTICAL)
        self.history_listbox = tk.Listbox(
            self.history_list_frame, height=15,
            yscrollcommand=self.history_scrollbar.set,
            bg=self.listbox_bg, fg=self.listbox_fg,
            selectbackground=self.listbox_select_bg,
            borderwidth=0, highlightthickness=0
        )
        self.history_scrollbar.config(command=self.history_listbox.yview)
        self.history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_listbox.bind("<Double-Button-1>", self.on_history_select) # Evento para tocar do histórico (Duplo Clique)

        self.history_button_frame = ttk.Frame(self.history_tab)
        self.history_button_frame.pack(pady=5)

        self.refresh_history_button = ttk.Button(self.history_button_frame, text="Atualizar", command=self.refresh_history)
        self.refresh_history_button.pack(side=tk.LEFT, padx=5)

        self.clear_history_button = ttk.Button(self.history_button_frame, text="Limpar Histórico", command=self.clear_history)
        self.clear_history_button.pack(side=tk.LEFT, padx=5)

        # self.about_button = ttk.Button(self.history_button_frame, text="Sobre", command=self.show_about_info) # REMOVE o botão daqui
        # self.about_button.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(root, text="Pronto.")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Variáveis de estado
        self.search_results_data = []
        self.history_data = []
        self.selected_anime_title = ""
        self.current_selected_episode = None

        self.episode_details_data = {}
        self.is_updating_episodes = False # Flag para controlar atualização
        self.episodes_per_page = 10
        self.current_episode_page = 1
        self.last_selected_episode_listbox_index = -1
        self.target_episode_url_from_history = None

        self.load_history()
        self.notebook.select(self.search_tab)

        # --- Popula a aba "Sobre" ---
        self.populate_about_tab()

    def _set_icon(self, icon_path: Path):
        """Define o ícone da janela, tentando diferentes métodos."""
        try:
            if icon_path.exists():
                if os.name == 'nt': # Windows
                    if icon_path.suffix.lower() == '.ico':
                        self.root.iconbitmap(str(icon_path))
                    else: # Tenta PhotoImage para outros formatos no Windows
                        img = tk.PhotoImage(file=str(icon_path))
                        self.root.iconphoto(True, img)
                else: # Linux/macOS (e outros)
                    img = tk.PhotoImage(file=str(icon_path))
                    self.root.iconphoto(True, img)
        except Exception as e:
            print(f"[Icon Error] Não foi possível definir o ícone '{icon_path}': {e}")

    def populate_about_tab(self):
        """Adiciona os widgets de informação na aba 'Sobre'."""
        about_frame = ttk.Frame(self.about_tab, padding="20")
        about_frame.pack(expand=True)

        message = (
            "Criador: Marcos\n" 
            "Contato: marcosslprado@gmail.com\n\n"
            "me ajude a manter"
            "Me pague um café? PIX: 83980601072"
        )

        about_label = ttk.Label(about_frame, text=message, justify=tk.CENTER, font=("Segoe UI", 10))
        about_label.pack()

    # def show_about_info(self): # REMOVE a função antiga que usava messagebox

    def refresh_history(self):
        """Recarrega a lista de histórico do arquivo."""
        self.load_history()
        self.update_status("Histórico atualizado.")

    def clear_history(self):
        """Limpa todo o histórico após confirmação."""
        if messagebox.askyesno("Limpar Histórico", "Tem certeza que deseja apagar TODO o histórico?\nEsta ação não pode ser desfeita."):
            self.history_data = []
            self.history_listbox.delete(0, tk.END)
            self.save_history()
            self.update_status("Histórico limpo.")
        else:
            self.update_status("Limpeza do histórico cancelada.")

    def clear_search_results(self):
        """Limpa os resultados da busca, a lista de episódios e o campo de busca."""
        self.search_entry.delete(0, tk.END)
        self.results_listbox.delete(0, tk.END)
        self.episodes_listbox.delete(0, tk.END)
        self.search_results_data = []
        self.episode_details_data = {}
        self.selected_anime_title = ""
        self.current_selected_episode = None
        self.last_selected_episode_listbox_index = -1
        self.results_label.config(text="Faça uma busca para ver os resultados")
        self.episode_page_label.config(text="Página -/-")
        self.prev_episode_button.config(state=tk.DISABLED)
        self.next_episode_button.config(state=tk.DISABLED)
        self.update_status("Resultados limpos. Pronto para nova busca.")

    def update_status(self, message):
        """Atualiza a barra de status (thread-safe)"""
        self.root.after(0, lambda: self.status_label.config(text=message))

    def set_ui_state(self, state):
        """Habilita ou desabilita elementos da UI (tk.NORMAL ou tk.DISABLED)"""
        self.search_entry.config(state=state)
        self.search_button.config(state=state)
        self.clear_button.config(state=state)
        listbox_state = tk.DISABLED if state == tk.DISABLED else tk.NORMAL
        try:
            self.results_listbox.config(state=listbox_state)
        except tk.TclError: # Pode dar erro se a janela estiver fechando
            pass
        try:
            # Não desabilitamos mais a listbox de episódios globalmente aqui
            pass
        except tk.TclError:
            pass

        history_button_state = state if state == tk.DISABLED else tk.NORMAL
        try:
            self.refresh_history_button.config(state=history_button_state)
            self.clear_history_button.config(state=history_button_state)
            # self.about_button.config(state=history_button_state) # Não existe mais aqui
        except tk.TclError:
            pass
        if state == tk.DISABLED:
            try:
                self.prev_episode_button.config(state=tk.DISABLED)
                self.next_episode_button.config(state=tk.DISABLED)
            except tk.TclError:
                pass
        # Se estiver habilitando, a função _re_enable_episode_selection ou update_episode_list_page cuidará do estado dos botões

    def load_history(self):
        """Carrega o histórico do arquivo JSON e atualiza a listbox."""
        home = Path.home()
        config_dir = home / ".local" / "share" / "maratonando"
        config_dir.mkdir(parents=True, exist_ok=True)
        self.history_file_path = config_dir / HISTORY_FILE

        try:
            if self.history_file_path.exists():
                with open(self.history_file_path, 'r', encoding='utf-8') as f:
                    self.history_data = json.load(f)
            else:
                self.history_data = []
        except (json.JSONDecodeError, IOError) as e:
            print(f"[History Error] Erro ao carregar histórico de '{self.history_file_path}': {e}")
            self.history_data = []

        try:
            self.history_listbox.delete(0, tk.END)
            # Mostra os mais recentes primeiro
            for item in reversed(self.history_data):
                display_text = f"{item.get('anime_title', '?')} - {item.get('episode_title', '?')}"
                self.history_listbox.insert(tk.END, display_text)
        except tk.TclError: # Ignora erro se a janela estiver fechando
            pass

    def save_history(self):
        """Salva o histórico atual no arquivo JSON."""
        if not hasattr(self, 'history_file_path'):
             print("[History Error] Caminho do arquivo de histórico não definido.")
             home = Path.home()
             config_dir = home / ".local" / "share" / "maratonando"
             config_dir.mkdir(parents=True, exist_ok=True)
             self.history_file_path = config_dir / HISTORY_FILE

        try:
            with open(self.history_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"[History Error] Erro ao salvar histórico em '{self.history_file_path}': {e}")

    def add_to_history(self, anime_title, episode_title, episode_url):
        """Adiciona um item ao histórico (evita duplicatas recentes) e salva."""
        if not all([anime_title, episode_title, episode_url]):
             print("[History Error] Dados incompletos para adicionar ao histórico.")
             return

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        new_entry = {
            "anime_title": anime_title,
            "episode_title": episode_title,
            "episode_url": episode_url,
            "timestamp": timestamp
        }

        # Remove item idêntico (baseado na URL) se já existir para colocá-lo no topo
        self.history_data = [item for item in self.history_data if item.get('episode_url') != episode_url]
        self.history_data.append(new_entry)

        # Limitar tamanho do histórico
        max_history = 100
        if len(self.history_data) > max_history:
            self.history_data = self.history_data[-max_history:]

        self.save_history()

    def start_search_thread(self, event=None):
        """Inicia a busca em uma thread separada para não travar a GUI"""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Busca", "Digite um termo para buscar.")
            return

        self.update_status(f"Buscando por '{query}'...")
        self.set_ui_state(tk.DISABLED)
        self.results_listbox.delete(0, tk.END)
        self.episodes_listbox.delete(0, tk.END)
        self.episode_page_label.config(text="Página -/-")
        self.prev_episode_button.config(state=tk.DISABLED)
        self.next_episode_button.config(state=tk.DISABLED)
        self.search_results_data = []
        self.episode_details_data = {}
        self.last_selected_episode_listbox_index = -1

        thread = threading.Thread(target=self.perform_search, args=(query,), daemon=True)
        thread.start()

    def perform_search(self, query):
        """Executa a busca (dentro da thread)"""
        try:
            results = animefire_parser.search(query)
            self.search_results_data = results

            def update_gui():
                self.results_listbox.unbind("<<ListboxSelect>>")
                self.set_ui_state(tk.NORMAL)
                self.results_label.config(text="Resultados da Busca")
                self.results_listbox.delete(0, tk.END)
                if results:
                    for i, result in enumerate(results):
                        self.results_listbox.insert(tk.END, f"{i+1}. {result['title']}")
                    self.update_status(f"{len(results)} animes encontrados.")
                else:
                    self.update_status("Nenhum anime encontrado.")
                self.results_listbox.bind("<<ListboxSelect>>", self.on_anime_select)

                # Verifica se a busca foi iniciada pelo histórico
                if self.target_episode_url_from_history:
                    found_anime_for_history = False
                    for i, result in enumerate(self.search_results_data):
                        if result.get('title', '').lower() == self.selected_anime_title.lower():
                            self.results_listbox.selection_clear(0, tk.END)
                            self.results_listbox.selection_set(i)
                            self.results_listbox.activate(i)
                            self.results_listbox.see(i)
                            self.on_anime_select()
                            found_anime_for_history = True
                            break
                    if not found_anime_for_history:
                        self.update_status(f"Anime '{self.selected_anime_title}' do histórico não encontrado na busca.")
                        self.target_episode_url_from_history = None

            self.root.after(0, update_gui)

        except Exception as e:
            print(f"[Thread Debug] ERRO na busca: {e}")
            self.update_status(f"Erro na busca: {e}")
            self.root.after(0, lambda: self.set_ui_state(tk.NORMAL))
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao buscar: {e}"))
            self.target_episode_url_from_history = None

    def on_anime_select(self, event=None):
        """Chamado quando um anime é selecionado na lista de resultados."""
        selected_indices = self.results_listbox.curselection()
        if not selected_indices:
            return

        selected_index = selected_indices[0]
        if selected_index < len(self.search_results_data):
            selected_anime = self.search_results_data[selected_index]
            self.selected_anime_title = selected_anime.get('title', 'Anime Desconhecido')
            self.update_status(f"Carregando episódios para: {self.selected_anime_title}...")
            self.episodes_listbox.config(state=tk.DISABLED)
            self.prev_episode_button.config(state=tk.DISABLED)
            self.next_episode_button.config(state=tk.DISABLED)
            self.episode_page_label.config(text="Carregando...")
            self.episodes_listbox.delete(0, tk.END)
            self.episode_details_data = {}
            self.last_selected_episode_listbox_index = -1

            thread = threading.Thread(target=self.perform_fetch_episodes, args=(selected_anime['url'],), daemon=True)
            thread.start()

    def _re_enable_episode_selection(self):
        """Re-vincula o evento de seleção de episódio e reabilita os botões de paginação."""
        try:
            self.episodes_listbox.bind("<<ListboxSelect>>", self.on_episode_select)
            self.episodes_listbox.config(state=tk.NORMAL)

            all_episodes = self.episode_details_data.get('episodes', [])
            if all_episodes:
                total_pages = math.ceil(len(all_episodes) / self.episodes_per_page)
                self.prev_episode_button.config(state=tk.NORMAL if self.current_episode_page > 1 else tk.DISABLED)
                self.next_episode_button.config(state=tk.NORMAL if self.current_episode_page < total_pages else tk.DISABLED)
            else:
                 self.prev_episode_button.config(state=tk.DISABLED)
                 self.next_episode_button.config(state=tk.DISABLED)

        except tk.TclError:
            pass
        except AttributeError:
             pass

        self.last_selected_episode_listbox_index = -1
        self.target_episode_url_from_history = None

    def update_episode_list_page(self):
        """Atualiza a listbox de episódios para mostrar a página atual."""
        self.is_updating_episodes = True
        self.episodes_listbox.config(state=tk.NORMAL)
        self.episodes_listbox.delete(0, tk.END)

        all_episodes = self.episode_details_data.get('episodes', [])
        total_episodes = len(all_episodes)

        if not all_episodes:
            self.update_status("Nenhum episódio encontrado para este anime.")
            self.episode_page_label.config(text="Página -/-")
            self.prev_episode_button.config(state=tk.DISABLED)
            self.next_episode_button.config(state=tk.DISABLED)
            self.root.after(100, lambda: setattr(self, 'is_updating_episodes', False))
            self.root.after(100, lambda: self.episodes_listbox.bind("<<ListboxSelect>>", self.on_episode_select))
            return

        total_pages = math.ceil(total_episodes / self.episodes_per_page)

        if self.current_episode_page < 1:
            self.current_episode_page = 1
        if self.current_episode_page > total_pages:
            self.current_episode_page = total_pages

        start_index = (self.current_episode_page - 1) * self.episodes_per_page
        end_index = start_index + self.episodes_per_page
        episodes_to_display = all_episodes[start_index:end_index]

        try:
            for i, episode in enumerate(episodes_to_display):
                global_ep_num = start_index + i + 1
                title_to_insert = episode.get('title', 'Título Desconhecido')
                display_text = f"{global_ep_num}. {title_to_insert}"
                self.episodes_listbox.insert(tk.END, display_text)
            self.update_status(f"Mostrando {len(episodes_to_display)} de {total_episodes} episódios.")

            if self.target_episode_url_from_history:
                target_listbox_index = -1
                for idx, ep_data_in_page in enumerate(episodes_to_display):
                    if ep_data_in_page.get('url') == self.target_episode_url_from_history:
                        target_listbox_index = idx
                        break
                if target_listbox_index != -1:
                    self.episodes_listbox.selection_clear(0, tk.END)
                    self.episodes_listbox.selection_set(target_listbox_index)
                    self.episodes_listbox.activate(target_listbox_index)
                    self.episodes_listbox.see(target_listbox_index)
                    self.last_selected_episode_listbox_index = target_listbox_index
                    self.update_status(f"Episódio {start_index + target_listbox_index + 1} selecionado. Clique novamente para assistir.")
                else:
                     self.update_status(f"Episódio do histórico não encontrado na página {self.current_episode_page}.")
                self.target_episode_url_from_history = None
        except Exception as insert_err:
            self.episodes_listbox.delete(0, tk.END)
            print(f"[GUI Update Debug] ERRO ao inserir na Listbox de episódios: {insert_err}")
            self.update_status("Erro ao exibir episódios.")

        self.episode_page_label.config(text=f"Página {self.current_episode_page}/{total_pages}")
        self.prev_episode_button.config(state=tk.NORMAL if self.current_episode_page > 1 else tk.DISABLED)
        self.next_episode_button.config(state=tk.NORMAL if self.current_episode_page < total_pages else tk.DISABLED)

        self.root.after(100, lambda: setattr(self, 'is_updating_episodes', False))
        self.root.after(100, lambda: self.episodes_listbox.bind("<<ListboxSelect>>", self.on_episode_select))
        print(f"[GUI Update Debug] Página {self.current_episode_page} de episódios exibida.")

    def go_to_previous_page(self):
        """Vai para a página anterior de episódios."""
        if self.current_episode_page > 1:
            self.current_episode_page -= 1
            self.last_selected_episode_listbox_index = -1
            self.update_episode_list_page()

    def go_to_next_page(self):
        """Vai para a próxima página de episódios."""
        all_episodes = self.episode_details_data.get('episodes', [])
        total_pages = math.ceil(len(all_episodes) / self.episodes_per_page)
        if self.current_episode_page < total_pages:
            self.current_episode_page += 1
            self.last_selected_episode_listbox_index = -1
            self.update_episode_list_page()

    def perform_fetch_episodes(self, anime_url):
        """Busca os detalhes e episódios (dentro da thread)"""
        try:
            details = animefire_parser.fetch_details(anime_url)
            self.episode_details_data = details

            target_page = 1
            if self.target_episode_url_from_history and details and 'episodes' in details:
                all_episodes = details['episodes']
                target_index = -1
                for i, ep in enumerate(all_episodes):
                    if ep.get('url') == self.target_episode_url_from_history:
                        target_index = i
                        break
                if target_index != -1:
                    target_page = math.floor(target_index / self.episodes_per_page) + 1
                    print(f"[Debug] Episódio do histórico encontrado no índice {target_index}, página {target_page}")
                else:
                    print(f"[Debug] Episódio do histórico ({self.target_episode_url_from_history}) não encontrado na lista.")
                    self.target_episode_url_from_history = None

            self.current_episode_page = target_page
            self.root.after(0, self.update_episode_list_page)

        except Exception as e:
            print(f"[Thread Debug] ERRO ao buscar episódios: {e}")
            def handle_fetch_error():
                self.episode_details_data = {'episodes': []}
                self.update_episode_list_page()
                self.update_status(f"Erro ao carregar episódios: {e}")
                messagebox.showerror("Erro", f"Erro ao carregar episódios: {e}")
            self.root.after(0, handle_fetch_error)

    def on_history_select(self, event=None):
        """
        Chamado quando um item é clicado duas vezes na lista de histórico.
        Tenta encontrar o anime na busca atual ou inicia uma nova busca,
        marcando o episódio para seleção posterior.
        """
        selected_indices = self.history_listbox.curselection()
        if not selected_indices:
            return

        selected_reversed_index = selected_indices[0]
        original_index = len(self.history_data) - 1 - selected_reversed_index

        if 0 <= original_index < len(self.history_data):
            selected_history_item = self.history_data[original_index]
            episode_url = selected_history_item.get('episode_url')
            episode_title = selected_history_item.get('episode_title', 'Episódio')
            anime_title = selected_history_item.get('anime_title')

            if episode_url and anime_title:
                self.update_status(f"Carregando '{anime_title}' - '{episode_title}' do histórico...")
                self.target_episode_url_from_history = episode_url
                self.selected_anime_title = anime_title
                self.notebook.select(self.search_tab)

                found_in_results = False
                for i, result in enumerate(self.search_results_data):
                    if result.get('title', '').lower() == anime_title.lower():
                        self.results_listbox.selection_clear(0, tk.END)
                        self.results_listbox.selection_set(i)
                        self.results_listbox.activate(i)
                        self.results_listbox.see(i)
                        self.on_anime_select()
                        found_in_results = True
                        break

                if not found_in_results:
                    temp_title = re.sub(r'\s*\((Dublado|Legendado)\)\s*$', '', anime_title, flags=re.IGNORECASE)
                    cleaned_title = temp_title.strip().lower()
                    self.search_entry.delete(0, tk.END)
                    self.search_entry.insert(0, cleaned_title)
                    self.start_search_thread()

            else:
                self.update_status("Dados incompletos no item do histórico (título ou URL faltando).")
        else:
             self.update_status("Erro ao obter item do histórico.")

    def on_episode_select(self, event=None):
        """
        Chamado quando um episódio é selecionado.
        Primeiro clique: seleciona. Segundo clique no mesmo item: carrega vídeo.
        """
        if self.is_updating_episodes:
            print("[Event Debug] Evento on_episode_select ignorado (atualizando lista).")
            return
        selected_indices = self.episodes_listbox.curselection()
        if not selected_indices:
            return

        selected_listbox_index = selected_indices[0]

        if selected_listbox_index == self.last_selected_episode_listbox_index:
            print(f"[Event Debug] Segundo clique no índice {selected_listbox_index}. Carregando vídeo...")

            start_index = (self.current_episode_page - 1) * self.episodes_per_page
            selected_global_index = start_index + selected_listbox_index
            all_episodes = self.episode_details_data.get('episodes', [])

            if 0 <= selected_global_index < len(all_episodes):
                selected_episode = all_episodes[selected_global_index]
                self.current_selected_episode = selected_episode
                self.update_status(f"Obtendo vídeo para: {selected_episode['title']}...")
                self.episodes_listbox.unbind("<<ListboxSelect>>")
                self.prev_episode_button.config(state=tk.DISABLED)
                self.next_episode_button.config(state=tk.DISABLED)

                thread = threading.Thread(target=self.perform_get_video, args=(selected_episode['url'],), daemon=True)
                thread.start()
            else:
                print(f"[Error] Índice de episódio selecionado inválido no segundo clique: {selected_global_index}")
                self.update_status("Erro ao selecionar episódio.")
                self.last_selected_episode_listbox_index = -1
        else:
            self.last_selected_episode_listbox_index = selected_listbox_index
            start_index = (self.current_episode_page - 1) * self.episodes_per_page
            global_ep_num = start_index + selected_listbox_index + 1
            self.update_status(f"Episódio {global_ep_num} selecionado. Clique novamente para assistir.")

    def perform_get_video(self, episode_page_url):
        """Obtém as fontes de vídeo e tenta tocar (dentro da thread)"""
        try:
            video_sources = animefire_parser.get_video_sources(episode_page_url)

            if not video_sources:
                def show_error_ui():
                    self.update_status("Falha ao obter o link do vídeo do site.")
                    messagebox.showerror("Erro", "Não foi possível obter o link do vídeo do site.\nO link pode estar quebrado ou o site offline.")
                    self._re_enable_episode_selection()
                self.root.after(0, show_error_ui)
                return

            chosen_source = None
            episode_url_for_history = episode_page_url
            episode_title_for_history = self.current_selected_episode.get('title', 'Episódio') if self.current_selected_episode else 'Episódio'

            if len(video_sources) == 1:
                chosen_source = video_sources[0]
                self.update_status(f"Fonte única encontrada ({chosen_source.get('label', 'N/A')}). Tocando...")
                video_url_to_play = chosen_source['src']
                self.root.after(0, self.play_selected_video, video_url_to_play, episode_url_for_history, episode_title_for_history)
            else:
                options = [f"{i+1}. {s.get('label', f'Opção {i+1}')}" for i, s in enumerate(video_sources)]
                prompt_text = "Qualidades disponíveis:\n" + "\n".join(options) + "\n\nDigite o NÚMERO da opção desejada:"

                def ask_quality():
                    choice_num_str = simpledialog.askstring("Seleção de Qualidade", prompt_text, parent=self.root)
                    selected_source = None
                    if choice_num_str:
                        try:
                            choice_index = int(choice_num_str) - 1
                            if 0 <= choice_index < len(video_sources):
                                selected_source = video_sources[choice_index]
                            else:
                                self.update_status("Seleção inválida.")
                                messagebox.showwarning("Seleção Inválida", "Número da opção inválido.")
                        except ValueError:
                            self.update_status("Entrada inválida.")
                            messagebox.showwarning("Seleção Inválida", "Por favor, digite um número.")
                    else:
                        self.update_status("Seleção cancelada.")
                        self._re_enable_episode_selection()

                    if selected_source:
                        self.update_status(f"Opção {selected_source.get('label', 'N/A')} selecionada. Tocando...")
                        video_url_to_play = selected_source['src']
                        self.play_selected_video(video_url_to_play, episode_url_for_history, episode_title_for_history)

                self.root.after(0, ask_quality)

        except Exception as e:
            print(f"[Thread Debug] perform_get_video: ERRO GERAL: {e}", file=sys.stderr)
            def show_general_error_ui(err_msg):
                 self.update_status(f"Erro ao obter vídeo: {err_msg}")
                 messagebox.showerror("Erro", f"Erro ao obter vídeo: {err_msg}")
                 self._re_enable_episode_selection()
            self.root.after(0, show_general_error_ui, str(e))

    def _run_play_video_thread(self, video_url, title):
        """Função para ser executada na thread do player."""
        try:
            play_video(video_url, title=title, referer=None)
        except FileNotFoundError:
             print(f"[Thread Player Debug] Erro FileNotFoundError ao tentar executar play_video.", file=sys.stderr)
        except Exception as play_err:
             print(f"[Thread Player Debug] Erro inesperado na thread do player: {play_err}", file=sys.stderr)
        finally:
            # Após o player fechar (ou falhar), agenda a reabilitação da UI na thread principal
            print("[Thread Player Debug] Player fechado ou falhou. Agendando reabilitação da UI.")
            self.root.after(0, self._re_enable_episode_selection)

    def play_selected_video(self, video_url_to_play, episode_url_original, episode_title_original):
        """Toca o vídeo da fonte selecionada (executa na thread principal)"""
        if not video_url_to_play:
            self.update_status("Fonte de vídeo inválida.")
            messagebox.showerror("Erro", "Fonte de vídeo inválida.")
            self.root.after(0, self._re_enable_episode_selection)
            return

        try:
            # Usa a URL original da página do episódio para o histórico
            self.add_to_history(self.selected_anime_title, episode_title_original, episode_url_original)
        except Exception as history_err:
            print(f"[History Error] Erro ao adicionar ao histórico: {history_err}")

        self.update_status(f"Iniciando player...")

        popup = None
        try:
            popup = tk.Toplevel(self.root)
            popup.title("Carregando")
            popup.geometry("210x85") # Tamanho ajustado
            popup.resizable(False, False)
            popup.transient(self.root)

            root_x = self.root.winfo_x()
            root_y = self.root.winfo_y()
            root_w = self.root.winfo_width()
            root_h = self.root.winfo_height()
            popup_x = root_x + (root_w // 2) - (210 // 2) # Ajustar largura
            popup_y = root_y + (root_h // 2) - (85 // 2)  # Ajustar altura
            popup.geometry(f"+{popup_x}+{popup_y}")

            label_popup = ttk.Label(popup, text="Iniciando player...\nAguarde de 5 a 30 segundos.", padding=(10, 10), justify=tk.CENTER)
            label_popup.pack(expand=True, fill=tk.BOTH)
            self.root.update_idletasks()

            popup_duration = 8000
            self.root.after(popup_duration, popup.destroy)

            player_thread = threading.Thread(
                target=self._run_play_video_thread,
                args=(video_url_to_play, f"{self.selected_anime_title} - {episode_title_original}"),
                daemon=True)
            player_thread.start()

        except FileNotFoundError:
             self.update_status("Erro: Comando 'mpv' não encontrado.")
             print(f"[Main Thread Debug] play_selected_video: ERRO - mpv não encontrado", file=sys.stderr)
             if popup: popup.destroy()
             messagebox.showerror("Erro", "Player 'mpv' não encontrado. Verifique a instalação.")
             self.root.after(0, self._re_enable_episode_selection)
             return
        except Exception as play_err:
             print(f"[Main Thread Debug] play_selected_video: ERRO ao chamar play_video/criar popup: {play_err}", file=sys.stderr)
             self.update_status(f"Erro ao iniciar player.")
             if popup: popup.destroy()
             messagebox.showerror("Erro ao Iniciar Player", f"Não foi possível iniciar o player MPV.\n\nCausas comuns:\n- O link do vídeo pode ter expirado ou estar protegido (Erro 403 Forbidden).\n- Problema na instalação do MPV ou dependências.\n\nErro original: {play_err}")
             self.root.after(0, self._re_enable_episode_selection)
             return

if __name__ == "__main__":
    root = tk.Tk()
    app = AnimeApp(root)
    root.mainloop()
