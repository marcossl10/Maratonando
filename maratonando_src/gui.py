# /home/marcos/Maratonando/maratonando/gui.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import json # Para histórico
import os   # Para caminho do arquivo
import sv_ttk # Importa a biblioteca de temas
import threading # Para rodar busca/extração sem travar a GUI
import time # Para timestamp do histórico
import math # Importar math para ceil
import re # Para limpar título do histórico
from pathlib import Path # Para lidar com caminhos de forma mais robusta (IMPORT DO ÍCONE)
import sys # Para sys.stderr nos logs de debug

# Importar o parser de anime
from .core.parsers import animefire_parser # Use relative import
# Importar a função de tocar vídeo
from .core.player import play_video

HISTORY_FILE = "history.json" # Nome do arquivo de histórico

class AnimeApp:
    def __init__(self, root):
        self.root = root

        # --- Definir Ícone ---
        # Caminho padrão para instalação
        installed_icon_path = Path("/usr/share/maratonando/icons/maratonando.png")
        # Caminho relativo para desenvolvimento
        dev_icon_path = Path(__file__).parent.parent / "icons" / "maratonando.png"

        # Usa o caminho instalado se existir, senão usa o de desenvolvimento
        icon_path = installed_icon_path if installed_icon_path.exists() else dev_icon_path

        self._set_icon(icon_path)
        # --- Fim Ícone ---

        self.root.title("Maratonando Animes")


        # Aplica o tema escuro ANTES de criar os widgets principais
        sv_ttk.set_theme("dark")

        # Configura cores para widgets Tk clássicos (Listbox)
        self.listbox_bg = "#2b2b2b" # Cor de fundo escura (ajuste se necessário)
        self.listbox_fg = "#ffffff" # Cor do texto clara
        self.listbox_select_bg = "#0078d4" # Cor de fundo da seleção (azul)

        self.root.geometry("700x500") # Aumentar a altura inicial para 500

        # --- Abas ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # --- Aba de Busca ---
        self.search_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.search_tab, text="Buscar")

        # --- Aba de Histórico ---
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text="Histórico")

        # --- Elementos da GUI (Aba de Busca) ---
        self.search_controls_frame = ttk.Frame(self.search_tab)
        self.search_controls_frame.pack(pady=5)

        self.search_label = ttk.Label(self.search_controls_frame, text="Buscar Anime:")
        self.search_label.pack(pady=5)

        self.search_entry = ttk.Entry(self.search_controls_frame, width=40)
        self.search_entry.pack(pady=5)
        self.search_entry.bind("<Return>", self.start_search_thread) # Buscar ao pressionar Enter

        # Frame para os botões de busca e limpar
        self.button_frame = ttk.Frame(self.search_controls_frame)
        self.button_frame.pack(pady=5)

        self.search_button = ttk.Button(self.button_frame, text="Buscar", command=self.start_search_thread)
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(self.button_frame, text="Limpar", command=self.clear_search_results)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Label para indicar o conteúdo da lista de resultados
        self.results_label = ttk.Label(self.search_tab, text="Faça uma busca para ver os resultados") # Texto inicial
        self.results_label.pack(pady=(5,0))

        # Frame para resultados e episódios
        self.results_frame = ttk.Frame(self.search_tab)
        self.results_frame.pack(pady=(10, 0), fill=tk.BOTH, expand=True) # Reduzir padding inferior

        # --- Listbox de Resultados (com scrollbar, boa prática) ---
        self.results_subframe = ttk.Frame(self.results_frame)
        self.results_subframe.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.results_scrollbar = ttk.Scrollbar(self.results_subframe, orient=tk.VERTICAL)
        self.results_listbox = tk.Listbox(
            self.results_subframe,
            width=50, height=10,
            yscrollcommand=self.results_scrollbar.set,
            bg=self.listbox_bg, fg=self.listbox_fg, # Aplica cores
            selectbackground=self.listbox_select_bg, # Cor da seleção
            borderwidth=0, highlightthickness=0 # Remove bordas padrão
        )
        self.results_scrollbar.config(command=self.results_listbox.yview)
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.results_listbox.bind("<<ListboxSelect>>", self.on_anime_select) # Evento ao selecionar anime

        # --- Listbox de Episódios ---
        self.episodes_subframe = ttk.Frame(self.results_frame) # Usa ttk.Frame
        self.episodes_subframe.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        self.episodes_listbox = tk.Listbox(
            self.episodes_subframe, width=30, height=10,
            bg=self.listbox_bg, fg=self.listbox_fg, # Aplica cores
            selectbackground=self.listbox_select_bg, # Cor da seleção
            borderwidth=0, highlightthickness=0 # Remove bordas padrão
        )
        self.episodes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.episodes_listbox.bind("<<ListboxSelect>>", self.on_episode_select) # Evento ao selecionar episódio

        # --- Controles de Paginação de Episódios (Abaixo do results_frame) ---
        self.episode_pagination_frame = ttk.Frame(self.search_tab) # Pai é a aba de busca
        self.episode_pagination_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 10)) # Empacotar na parte inferior da aba

        self.prev_episode_button = ttk.Button(self.episode_pagination_frame, text="< Anterior", command=self.go_to_previous_page, state=tk.DISABLED)
        self.next_episode_button = ttk.Button(self.episode_pagination_frame, text="Próximo >", command=self.go_to_next_page, state=tk.DISABLED)

        # Empacotar na ordem correta: Próximo (direita), Anterior (esquerda), Label (esquerda)
        self.next_episode_button.pack(side=tk.RIGHT, padx=5)
        self.prev_episode_button.pack(side=tk.LEFT, padx=5)
        self.episode_page_label = ttk.Label(self.episode_pagination_frame, text="Página -/-")
        self.episode_page_label.pack(side=tk.LEFT, padx=5)

        # --- Elementos da GUI (Aba de Histórico) ---
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

        # Frame para botões do histórico
        self.history_button_frame = ttk.Frame(self.history_tab)
        self.history_button_frame.pack(pady=5)

        self.refresh_history_button = ttk.Button(self.history_button_frame, text="Atualizar", command=self.refresh_history)
        self.refresh_history_button.pack(side=tk.LEFT, padx=5)

        self.clear_history_button = ttk.Button(self.history_button_frame, text="Limpar Histórico", command=self.clear_history)
        self.clear_history_button.pack(side=tk.LEFT, padx=5)

        # --- Barra de Status (Comum a todas as abas) ---
        self.status_label = ttk.Label(root, text="Pronto.")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Variáveis de estado
        self.search_results_data = []
        self.history_data = [] # Armazena dados do histórico
        self.selected_anime_title = "" # Guarda o título do anime selecionado na busca
        self.current_selected_episode = None # Guarda o episódio selecionado para add histórico

        self.episode_details_data = {}
        self.is_updating_episodes = False # Flag para controlar atualização
        self.episodes_per_page = 10 # Diminuir para 10 episódios por página
        self.current_episode_page = 1
        self.last_selected_episode_listbox_index = -1 # Índice do último ep clicado na listbox atual
        self.target_episode_url_from_history = None # Guarda a URL do ep a selecionar vindo do histórico

        # Carrega histórico ao iniciar
        self.load_history()
        # Seleciona a aba de Busca como padrão ao iniciar
        self.notebook.select(self.search_tab)

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

    def refresh_history(self):
        """Recarrega a lista de histórico do arquivo."""
        self.load_history()
        self.update_status("Histórico atualizado.")

    def clear_history(self):
        """Limpa todo o histórico após confirmação."""
        if messagebox.askyesno("Limpar Histórico", "Tem certeza que deseja apagar TODO o histórico?\nEsta ação não pode ser desfeita."):
            self.history_data = [] # Limpa a lista em memória
            self.history_listbox.delete(0, tk.END) # Limpa a listbox visualmente
            self.save_history() # Salva a lista vazia no arquivo
            self.update_status("Histórico limpo.")
        else:
            self.update_status("Limpeza do histórico cancelada.")

    def clear_search_results(self):
        """Limpa os resultados da busca, a lista de episódios e o campo de busca."""
        self.search_entry.delete(0, tk.END) # Limpa o campo de entrada
        self.results_listbox.delete(0, tk.END) # Limpa a lista de resultados
        self.episodes_listbox.delete(0, tk.END) # Limpa a lista de episódios
        self.search_results_data = [] # Limpa os dados dos resultados
        self.episode_details_data = {} # Limpa os dados dos detalhes
        self.selected_anime_title = "" # Limpa o título selecionado
        self.current_selected_episode = None # Limpa o episódio selecionado
        self.last_selected_episode_listbox_index = -1 # Reseta o índice do último clique
        self.results_label.config(text="Faça uma busca para ver os resultados") # Reseta o label
        # Limpa e desabilita paginação
        self.episode_page_label.config(text="Página -/-")
        self.prev_episode_button.config(state=tk.DISABLED)
        self.next_episode_button.config(state=tk.DISABLED)
        self.update_status("Resultados limpos. Pronto para nova busca.") # Atualiza status

    def update_status(self, message):
        """Atualiza a barra de status (thread-safe)"""
        self.root.after(0, lambda: self.status_label.config(text=message))

    def set_ui_state(self, state):
        """Habilita ou desabilita elementos da UI (tk.NORMAL ou tk.DISABLED)"""
        self.search_entry.config(state=state)
        self.search_button.config(state=state)
        self.clear_button.config(state=state) # Habilita/desabilita o botão Limpar também
        # Usamos 'disabled' e 'normal' para Listbox state
        listbox_state = tk.DISABLED if state == tk.DISABLED else tk.NORMAL
        # Apenas desabilita/habilita as listboxes se elas existirem
        try:
            self.results_listbox.config(state=listbox_state)
        except tk.TclError: # Pode dar erro se a janela estiver fechando
            pass
        try:
            # Não desabilitamos mais a listbox de episódios globalmente aqui
            # Apenas controlamos o binding do evento
            pass # self.episodes_listbox.config(state=listbox_state)
        except tk.TclError:
            pass

        # Habilita/desabilita os botões do histórico (exceto quando o estado geral é desabilitado)
        history_button_state = state if state == tk.DISABLED else tk.NORMAL
        try:
            self.refresh_history_button.config(state=history_button_state)
            self.clear_history_button.config(state=history_button_state)
        except tk.TclError:
            pass
        # Desabilita botões de paginação se a UI geral estiver desabilitada
        if state == tk.DISABLED:
            try:
                self.prev_episode_button.config(state=tk.DISABLED)
                self.next_episode_button.config(state=tk.DISABLED)
            except tk.TclError:
                pass
        # Se estiver habilitando, a função _re_enable_episode_selection ou update_episode_list_page cuidará do estado dos botões


    def load_history(self):
        """Carrega o histórico do arquivo JSON e atualiza a listbox."""
        # Determina o caminho do arquivo de histórico no diretório home do usuário
        home = Path.home()
        config_dir = home / ".local" / "share" / "maratonando"
        config_dir.mkdir(parents=True, exist_ok=True) # Cria o diretório se não existir
        self.history_file_path = config_dir / HISTORY_FILE

        try:
            if self.history_file_path.exists():
                with open(self.history_file_path, 'r', encoding='utf-8') as f:
                    self.history_data = json.load(f)
            else:
                self.history_data = []
        except (json.JSONDecodeError, IOError) as e:
            print(f"[History Error] Erro ao carregar histórico de '{self.history_file_path}': {e}")
            self.history_data = [] # Reseta em caso de erro

        # Atualiza a listbox de histórico
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
             # Tenta definir o caminho padrão se não existir
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

        # Adiciona o novo item no final (será mostrado no topo devido ao reversed na load_history)
        self.history_data.append(new_entry)

        # Opcional: Limitar tamanho do histórico (ex: manter últimos 100)
        max_history = 100
        if len(self.history_data) > max_history:
            self.history_data = self.history_data[-max_history:]

        self.save_history()


    def start_search_thread(self, event=None):
        """Inicia a busca em uma thread separada para não travar a GUI"""
        query = self.search_entry.get().strip() # Remove espaços extras no início/fim
        if not query:
            messagebox.showwarning("Busca", "Digite um termo para buscar.")
            return

        self.update_status(f"Buscando por '{query}'...")
        self.set_ui_state(tk.DISABLED) # Desabilita UI
        self.results_listbox.delete(0, tk.END) # Limpa resultados anteriores
        self.episodes_listbox.delete(0, tk.END) # Limpa episódios anteriores
        # Limpa e desabilita paginação ao iniciar nova busca
        self.episode_page_label.config(text="Página -/-")
        self.prev_episode_button.config(state=tk.DISABLED)
        self.next_episode_button.config(state=tk.DISABLED)
        self.search_results_data = []
        self.episode_details_data = {}
        self.last_selected_episode_listbox_index = -1 # Reseta o índice do último clique

        # Cria e inicia a thread
        thread = threading.Thread(target=self.perform_search, args=(query,), daemon=True)
        thread.start()
        # self.perform_search(query) # --- CHAMADA DIRETA PARA TESTE ---

    def perform_search(self, query):
        """Executa a busca (dentro da thread)"""
        try:
            print(f"[Thread Debug] Iniciando busca por: {query}") # DEBUG
            results = animefire_parser.search(query)
            print(f"[Thread Debug] Busca concluída. Resultados: {results}") # DEBUG
            self.search_results_data = results # Armazena os dados completos

            # Atualiza a Listbox na thread principal da GUI
            print("[Thread Debug] Agendando atualização da GUI...") # DEBUG
            def update_gui():
                # Desvincula o evento ANTES de modificar a lista
                self.results_listbox.unbind("<<ListboxSelect>>")
                self.set_ui_state(tk.NORMAL) # Reabilita UI PRIMEIRO
                self.results_label.config(text="Resultados da Busca") # Muda o label
                self.results_listbox.delete(0, tk.END) # Garante que está limpa
                if results:
                    for i, result in enumerate(results):
                        self.results_listbox.insert(tk.END, f"{i+1}. {result['title']}")
                    self.update_status(f"{len(results)} animes encontrados.")
                else:
                    self.update_status("Nenhum anime encontrado.")
                # Revincula o evento DEPOIS de modificar a lista
                self.results_listbox.bind("<<ListboxSelect>>", self.on_anime_select)
                print("[GUI Update Debug] Atualização da GUI executada.") # DEBUG

                # --- Verifica se a busca foi iniciada pelo histórico ---
                if self.target_episode_url_from_history:
                    found_anime_for_history = False
                    for i, result in enumerate(self.search_results_data):
                        # Comparação case-insensitive
                        if result.get('title', '').lower() == self.selected_anime_title.lower(): # Usa o título guardado (case-insensitive)
                            self.results_listbox.selection_clear(0, tk.END)
                            self.results_listbox.selection_set(i)
                            self.results_listbox.activate(i)
                            self.results_listbox.see(i)
                            self.on_anime_select() # Dispara o carregamento dos episódios
                            found_anime_for_history = True
                            break
                    if not found_anime_for_history:
                        self.update_status(f"Anime '{self.selected_anime_title}' do histórico não encontrado na busca.")
                        self.target_episode_url_from_history = None # Limpa se não achou


            self.root.after(0, update_gui) # Agenda a atualização da GUI

        except Exception as e:
            print(f"[Thread Debug] ERRO na busca: {e}") # DEBUG
            self.update_status(f"Erro na busca: {e}")
            self.root.after(0, lambda: self.set_ui_state(tk.NORMAL)) # Reabilita UI em caso de erro
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao buscar: {e}"))
            self.target_episode_url_from_history = None # Limpa alvo do histórico em caso de erro na busca

    def on_anime_select(self, event=None):
        """Chamado quando um anime é selecionado na lista de resultados (busca ou populares)."""
        selected_indices = self.results_listbox.curselection()
        if not selected_indices:
            return

        selected_index = selected_indices[0]
        # Usa self.search_results_data que contém ou populares ou busca
        if selected_index < len(self.search_results_data):
            selected_anime = self.search_results_data[selected_index]
            self.selected_anime_title = selected_anime.get('title', 'Anime Desconhecido') # Guarda o título
            self.update_status(f"Carregando episódios para: {self.selected_anime_title}...")
            self.episodes_listbox.config(state=tk.DISABLED) # Desabilita só a lista de episódios
            # Desabilita botões de paginação enquanto carrega
            self.prev_episode_button.config(state=tk.DISABLED)
            self.next_episode_button.config(state=tk.DISABLED)
            self.episode_page_label.config(text="Carregando...") # Indica carregamento
            self.episodes_listbox.delete(0, tk.END) # Limpa lista de episódios
            self.episode_details_data = {}
            self.last_selected_episode_listbox_index = -1 # Reseta o índice do último clique

            # Inicia busca de episódios em thread
            thread = threading.Thread(target=self.perform_fetch_episodes, args=(selected_anime['url'],), daemon=True)
            thread.start()

    def _re_enable_episode_selection(self):
        """Re-vincula o evento de seleção de episódio e reabilita os botões de paginação."""
        try:
            # Re-vincula o evento de seleção
            self.episodes_listbox.bind("<<ListboxSelect>>", self.on_episode_select)
            # Reabilita a listbox (caso tenha sido desabilitada por erro)
            self.episodes_listbox.config(state=tk.NORMAL)

            # Reabilita os botões de paginação com base na página atual e no total de páginas
            all_episodes = self.episode_details_data.get('episodes', [])
            if all_episodes: # Só habilita se houver episódios carregados
                total_pages = math.ceil(len(all_episodes) / self.episodes_per_page)
                self.prev_episode_button.config(state=tk.NORMAL if self.current_episode_page > 1 else tk.DISABLED)
                self.next_episode_button.config(state=tk.NORMAL if self.current_episode_page < total_pages else tk.DISABLED)
            else: # Desabilita se não houver episódios carregados
                 self.prev_episode_button.config(state=tk.DISABLED)
                 self.next_episode_button.config(state=tk.DISABLED)

        except tk.TclError:
            # Ignora erros se a janela estiver fechando
            pass
        except AttributeError:
             # Ignora se os widgets ainda não foram totalmente inicializados
             pass

        self.last_selected_episode_listbox_index = -1 # Reseta o índice para permitir nova seleção após falha/conclusão
        self.target_episode_url_from_history = None # Limpa o alvo do histórico também

    def update_episode_list_page(self):
        """Atualiza a listbox de episódios para mostrar a página atual."""
        self.is_updating_episodes = True # Define a flag ANTES de modificar
        self.episodes_listbox.config(state=tk.NORMAL) # Habilita para limpar/inserir
        self.episodes_listbox.delete(0, tk.END)

        all_episodes = self.episode_details_data.get('episodes', [])
        total_episodes = len(all_episodes)

        if not all_episodes:
            self.update_status("Nenhum episódio encontrado para este anime.")
            self.episode_page_label.config(text="Página -/-")
            self.prev_episode_button.config(state=tk.DISABLED)
            self.next_episode_button.config(state=tk.DISABLED)
            self.root.after(100, lambda: setattr(self, 'is_updating_episodes', False)) # Limpa flag
            # Garante que o evento de clique seja reativado mesmo sem episódios
            self.root.after(100, lambda: self.episodes_listbox.bind("<<ListboxSelect>>", self.on_episode_select))
            return

        total_pages = math.ceil(total_episodes / self.episodes_per_page)

        # Garante que a página atual seja válida
        if self.current_episode_page < 1:
            self.current_episode_page = 1
        if self.current_episode_page > total_pages:
            self.current_episode_page = total_pages

        # Calcula os índices dos episódios para a página atual
        start_index = (self.current_episode_page - 1) * self.episodes_per_page
        end_index = start_index + self.episodes_per_page
        episodes_to_display = all_episodes[start_index:end_index]

        # Insere os episódios da página atual na listbox
        try:
            for i, episode in enumerate(episodes_to_display):
                # Mostra o número global do episódio (opcional, mas útil)
                global_ep_num = start_index + i + 1
                title_to_insert = episode.get('title', 'Título Desconhecido')
                display_text = f"{global_ep_num}. {title_to_insert}"
                self.episodes_listbox.insert(tk.END, display_text)
            self.update_status(f"Mostrando {len(episodes_to_display)} de {total_episodes} episódios.")

            # --- Selecionar episódio vindo do histórico ---
            if self.target_episode_url_from_history:
                target_listbox_index = -1
                # Itera sobre os episódios *desta página* para encontrar o índice correto na listbox
                for idx, ep_data_in_page in enumerate(episodes_to_display):
                    # Compara a URL do episódio na página atual com a URL alvo
                    if ep_data_in_page.get('url') == self.target_episode_url_from_history:
                        target_listbox_index = idx
                        break
                if target_listbox_index != -1:
                    self.episodes_listbox.selection_clear(0, tk.END)
                    self.episodes_listbox.selection_set(target_listbox_index)
                    self.episodes_listbox.activate(target_listbox_index)
                    self.episodes_listbox.see(target_listbox_index)
                    self.last_selected_episode_listbox_index = target_listbox_index # Prepara para o próximo clique
                    self.update_status(f"Episódio {start_index + target_listbox_index + 1} selecionado. Clique novamente para assistir.")
                else:
                     # Se o episódio alvo não está nesta página, apenas informa
                     self.update_status(f"Episódio do histórico não encontrado na página {self.current_episode_page}.")
                self.target_episode_url_from_history = None # Limpa o alvo após tentar selecionar
        except Exception as insert_err:
            self.episodes_listbox.delete(0, tk.END) # Limpa em caso de erro
            print(f"[GUI Update Debug] ERRO ao inserir na Listbox de episódios: {insert_err}")
            self.update_status("Erro ao exibir episódios.")

        # Atualiza o label da página
        self.episode_page_label.config(text=f"Página {self.current_episode_page}/{total_pages}")

        # Habilita/Desabilita botões de paginação
        self.prev_episode_button.config(state=tk.NORMAL if self.current_episode_page > 1 else tk.DISABLED)
        self.next_episode_button.config(state=tk.NORMAL if self.current_episode_page < total_pages else tk.DISABLED)

        # Limpa a flag APÓS um pequeno atraso
        self.root.after(100, lambda: setattr(self, 'is_updating_episodes', False))
        # Garante que o evento de clique seja reativado
        self.root.after(100, lambda: self.episodes_listbox.bind("<<ListboxSelect>>", self.on_episode_select))
        print(f"[GUI Update Debug] Página {self.current_episode_page} de episódios exibida.")

    def go_to_previous_page(self):
        """Vai para a página anterior de episódios."""
        if self.current_episode_page > 1:
            self.current_episode_page -= 1
            self.last_selected_episode_listbox_index = -1 # Reseta o índice ao mudar de página
            self.update_episode_list_page()

    def go_to_next_page(self):
        """Vai para a próxima página de episódios."""
        all_episodes = self.episode_details_data.get('episodes', [])
        total_pages = math.ceil(len(all_episodes) / self.episodes_per_page)
        if self.current_episode_page < total_pages:
            self.current_episode_page += 1
            self.last_selected_episode_listbox_index = -1 # Reseta o índice ao mudar de página
            self.update_episode_list_page()

    def perform_fetch_episodes(self, anime_url):
        """Busca os detalhes e episódios (dentro da thread)"""
        try:
            print(f"[Thread Debug] Buscando detalhes/episódios de: {anime_url}") # DEBUG
            details = animefire_parser.fetch_details(anime_url)
            print(f"[Thread Debug] Detalhes obtidos: {details}") # DEBUG
            self.episode_details_data = details # Armazena detalhes

            target_page = 1 # Página padrão é a 1
            # Verifica se viemos do histórico e calcula a página alvo
            if self.target_episode_url_from_history and details and 'episodes' in details:
                all_episodes = details['episodes']
                target_index = -1
                for i, ep in enumerate(all_episodes):
                    if ep.get('url') == self.target_episode_url_from_history:
                        target_index = i
                        break
                if target_index != -1:
                    # Calcula a página (1-based)
                    target_page = math.floor(target_index / self.episodes_per_page) + 1
                    print(f"[Debug] Episódio do histórico encontrado no índice {target_index}, página {target_page}")
                else:
                    print(f"[Debug] Episódio do histórico ({self.target_episode_url_from_history}) não encontrado na lista.")
                    self.target_episode_url_from_history = None # Limpa se não achou

            self.current_episode_page = target_page # Define a página a ser exibida
            self.root.after(0, self.update_episode_list_page) # Agenda a atualização da página correta

        except Exception as e:
            print(f"[Thread Debug] ERRO ao buscar episódios: {e}") # DEBUG
            # Limpa a lista e atualiza status/botões em caso de erro
            def handle_fetch_error():
                self.episode_details_data = {'episodes': []} # Limpa dados
                self.update_episode_list_page() # Atualiza UI para estado vazio/erro
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

        # Calcula o índice correspondente na lista original self.history_data
        selected_reversed_index = selected_indices[0]
        original_index = len(self.history_data) - 1 - selected_reversed_index

        if 0 <= original_index < len(self.history_data):
            selected_history_item = self.history_data[original_index]
            episode_url = selected_history_item.get('episode_url')
            episode_title = selected_history_item.get('episode_title', 'Episódio')
            anime_title = selected_history_item.get('anime_title') # Precisa do título do anime

            if episode_url and anime_title:
                self.update_status(f"Carregando '{anime_title}' - '{episode_title}' do histórico...")
                self.target_episode_url_from_history = episode_url # Guarda a URL alvo
                self.selected_anime_title = anime_title # Guarda o título para comparação na busca
                self.notebook.select(self.search_tab) # Muda para a aba de busca

                # Tenta encontrar o anime nos resultados atuais
                found_in_results = False
                for i, result in enumerate(self.search_results_data):
                    # Comparação case-insensitive
                    if result.get('title', '').lower() == anime_title.lower():
                        self.results_listbox.selection_clear(0, tk.END)
                        self.results_listbox.selection_set(i)
                        self.results_listbox.activate(i)
                        self.results_listbox.see(i)
                        self.on_anime_select() # Dispara o carregamento dos episódios
                        found_in_results = True
                        break

                # Se não encontrou nos resultados atuais, faz uma nova busca
                if not found_in_results:
                    # Limpa o título antes de buscar (remove Dublado/Legendado etc.)
                    # Limpeza SIMPLES: remove (Dublado/Legendado) e converte para minúsculas
                    temp_title = re.sub(r'\s*\((Dublado|Legendado)\)\s*$', '', anime_title, flags=re.IGNORECASE)
                    cleaned_title = temp_title.strip().lower() # Converte para minúsculas e remove espaços
                    self.search_entry.delete(0, tk.END)
                    self.search_entry.insert(0, cleaned_title) # Usa o título limpo (optional, good for user feedback)
                    self.start_search_thread() # Inicia a busca (o episódio será selecionado depois)

            else:
                self.update_status("Dados incompletos no item do histórico (título ou URL faltando).")
        else:
             self.update_status("Erro ao obter item do histórico.")


    def on_episode_select(self, event=None):
        """
        Chamado quando um episódio é selecionado.
        Primeiro clique: seleciona. Segundo clique no mesmo item: carrega vídeo.
        """
        if self.is_updating_episodes: # Ignora o evento se a lista está sendo atualizada
            print("[Event Debug] Evento on_episode_select ignorado (atualizando lista).") # DEBUG
            return
        selected_indices = self.episodes_listbox.curselection()
        if not selected_indices:
            return

        selected_listbox_index = selected_indices[0]

        # Verifica se é o segundo clique no mesmo item
        if selected_listbox_index == self.last_selected_episode_listbox_index:
            # É o segundo clique, iniciar busca do vídeo
            print(f"[Event Debug] Segundo clique no índice {selected_listbox_index}. Carregando vídeo...")

            # Calcula o índice real na lista completa de episódios
            start_index = (self.current_episode_page - 1) * self.episodes_per_page
            selected_global_index = start_index + selected_listbox_index
            all_episodes = self.episode_details_data.get('episodes', [])

            if 0 <= selected_global_index < len(all_episodes):
                selected_episode = all_episodes[selected_global_index]
                self.current_selected_episode = selected_episode # Guarda para adicionar ao histórico
                self.update_status(f"Obtendo vídeo para: {selected_episode['title']}...")
                # Desvincular evento para evitar cliques múltiplos durante o carregamento
                self.episodes_listbox.unbind("<<ListboxSelect>>")
                # Desabilita botões de paginação também
                self.prev_episode_button.config(state=tk.DISABLED)
                self.next_episode_button.config(state=tk.DISABLED)

                # Inicia obtenção do vídeo em thread
                thread = threading.Thread(target=self.perform_get_video, args=(selected_episode['url'],), daemon=True)
                thread.start()
            else:
                print(f"[Error] Índice de episódio selecionado inválido no segundo clique: {selected_global_index}")
                self.update_status("Erro ao selecionar episódio.")
                self.last_selected_episode_listbox_index = -1 # Reseta para permitir nova seleção
        else:
            # É o primeiro clique, apenas guarda o índice e atualiza status
            self.last_selected_episode_listbox_index = selected_listbox_index
            # Calcula o número global para exibir na mensagem
            start_index = (self.current_episode_page - 1) * self.episodes_per_page
            global_ep_num = start_index + selected_listbox_index + 1
            self.update_status(f"Episódio {global_ep_num} selecionado. Clique novamente para assistir.")


    def perform_get_video(self, episode_page_url):
        """Obtém as fontes de vídeo e tenta tocar (dentro da thread)"""
        try:
            print(f"[Thread Debug] perform_get_video: Chamando get_video_sources para {episode_page_url}") # Log Adicional
            video_sources = animefire_parser.get_video_sources(episode_page_url)
            print(f"[Thread Debug] perform_get_video: get_video_sources retornou: {video_sources}") # Log Adicional

            if not video_sources:
                print("[Thread Debug] perform_get_video: Nenhuma fonte de vídeo encontrada.") # Log Adicional
                # Agendar a atualização da UI para mostrar o erro
                def show_error_ui():
                    self.update_status("Falha ao obter o link do vídeo do site.") # Mensagem atualizada
                    # Mostra o erro primeiro
                    messagebox.showerror("Erro", "Não foi possível obter o link do vídeo do site.\nO link pode estar quebrado ou o site offline.") # Mensagem atualizada
                    # Reabilita a lista e botões DEPOIS que o usuário fecha o messagebox
                    # Apenas reabilita os controles, sem redesenhar a lista
                    self._re_enable_episode_selection()
                self.root.after(0, show_error_ui)
                return

            chosen_source = None
            # Guarda a URL original da página do episódio para o histórico
            episode_url_for_history = episode_page_url
            # Guarda o título original do episódio para o histórico
            # Verifica se current_selected_episode foi definido (pode vir do histórico)
            episode_title_for_history = self.current_selected_episode.get('title', 'Episódio') if self.current_selected_episode else 'Episódio'

            if len(video_sources) == 1:
                chosen_source = video_sources[0]
                self.update_status(f"Fonte única encontrada ({chosen_source.get('label', 'N/A')}). Tocando...")
                # --- CORREÇÃO: Passar a URL DO IFRAME/BLOGGER para play_selected_video ---
                video_url_to_play = chosen_source['src'] # URL do iframe/blogger
                # episode_page_url # URL da página do episódio AnimeFire (Não mais usada para tocar)
                # Chama a função para tocar o vídeo na thread principal (para interagir com subprocess)
                print(f"[Thread Debug] perform_get_video: Agendando play_selected_video com URL: {video_url_to_play}") # Log Adicional
                self.root.after(0, self.play_selected_video, video_url_to_play, episode_url_for_history, episode_title_for_history) # Passa URL da página
                print(f"[Thread Debug] perform_get_video: Agendamento concluído.") # Log Adicional
            else:
                # Múltiplas fontes, pedir para o usuário escolher
                options = [f"{i+1}. {s.get('label', f'Opção {i+1}')}" for i, s in enumerate(video_sources)]
                prompt_text = "Qualidades disponíveis:\n" + "\n".join(options) + "\n\nDigite o NÚMERO da opção desejada:"

                # Função para rodar o simpledialog na thread principal
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
                        # Reabilita a lista e botões se cancelar
                        self._re_enable_episode_selection() # Usa a função auxiliar

                    if selected_source:
                        self.update_status(f"Opção {selected_source.get('label', 'N/A')} selecionada. Tocando...")
                        # --- CORREÇÃO: Passar a URL DO IFRAME/BLOGGER para play_selected_video ---
                        video_url_to_play = selected_source['src'] # URL do iframe/blogger
                        # episode_page_url # URL da página do episódio AnimeFire (Não mais usada para tocar)
                        self.play_selected_video(video_url_to_play, episode_url_for_history, episode_title_for_history) # Passa URL da página
                    # else: # Se não selecionou fonte válida, reabilita
                    #     self._re_enable_episode_selection() # Já é feito no finally ou no cancel

                # Agenda a execução do diálogo na thread principal
                self.root.after(0, ask_quality)

        except Exception as e:
            # Garante que a UI seja reabilitada mesmo em caso de erro GERAL na busca do vídeo
            print(f"[Thread Debug] perform_get_video: ERRO GERAL: {e}", file=sys.stderr) # Log Adicional
            def show_general_error_ui(err_msg):
                 self.update_status(f"Erro ao obter vídeo: {err_msg}")
                 messagebox.showerror("Erro", f"Erro ao obter vídeo: {err_msg}")
                 # Reabilita a lista e botões
                 # Apenas reabilita os controles, sem redesenhar a lista
                 self._re_enable_episode_selection()
            self.root.after(0, show_general_error_ui, str(e))

    def _run_play_video_thread(self, video_url, title):
        """Função para ser executada na thread do player."""
        try:
            play_video(video_url, title=title, referer=None)
        except FileNotFoundError:
             # Erro já tratado na chamada principal, mas logamos aqui também
             print(f"[Thread Player Debug] Erro FileNotFoundError ao tentar executar play_video.", file=sys.stderr)
        except Exception as play_err:
             # Erro já tratado na chamada principal, mas logamos aqui também
             print(f"[Thread Player Debug] Erro inesperado na thread do player: {play_err}", file=sys.stderr)
        finally:
            # Após o player fechar (ou falhar), agenda a reabilitação da UI na thread principal
            print("[Thread Player Debug] Player fechado ou falhou. Agendando reabilitação da UI.")
            self.root.after(0, self._re_enable_episode_selection)


    # Modificar a assinatura para aceitar a URL do vídeo diretamente
    def play_selected_video(self, video_url_to_play, episode_url_original, episode_title_original):
        """Toca o vídeo da fonte selecionada (executa na thread principal)"""
        print(f"[Main Thread Debug] play_selected_video: Iniciada com URL: {video_url_to_play}") # Log Adicional
        # Remover a verificação de 'source' pois agora recebemos a URL diretamente
        if not video_url_to_play:
            self.update_status("Fonte de vídeo inválida.")
            messagebox.showerror("Erro", "Fonte de vídeo inválida.")
            # Garante reabilitação mesmo com erro antes de tocar (se necessário)
            # Apenas reabilita os controles, sem redesenhar a lista
            self.root.after(0, self._re_enable_episode_selection)
            return

        # --- Adiciona ao Histórico ANTES de tocar ---
        try:
            # Usa a URL original da página do episódio para o histórico
            self.add_to_history(self.selected_anime_title, episode_title_original, episode_url_original)
        except Exception as history_err:
            print(f"[History Error] Erro ao adicionar ao histórico: {history_err}")

        # video_url = source['src'] # Não precisamos mais disso
        # label = source.get('label', 'N/A') # Não temos mais label aqui
        self.update_status(f"Iniciando player...") # Status genérico

        popup = None # Inicializa popup como None
        try:
            print(f"[Main Thread Debug] play_selected_video: play_video chamado. Criando popup...") # Log Adicional
            # --- Criar Popup de Carregamento ---
            # MOVER CRIAÇÃO DO POPUP PARA ANTES DE CHAMAR play_video
            popup = tk.Toplevel(self.root)
            popup.title("Carregando")
            popup.geometry("200x50") # Tamanho pequeno
            popup.resizable(False, False)
            popup.transient(self.root) # Associar à janela principal
            # popup.grab_set() # REMOVER: Pode causar conflitos de timing/foco
            # popup.overrideredirect(True) # Opcional: remove a barra de título e bordas

            # Centralizar popup
            root_x = self.root.winfo_x()
            root_y = self.root.winfo_y()
            root_w = self.root.winfo_width()
            root_h = self.root.winfo_height()
            popup_x = root_x + (root_w // 2) - (200 // 2)
            popup_y = root_y + (root_h // 2) - (50 // 2)
            popup.geometry(f"+{popup_x}+{popup_y}")

            label_popup = ttk.Label(popup, text="Iniciando player...", padding=(10, 10))
            label_popup.pack(expand=True, fill=tk.BOTH)
            self.root.update_idletasks() # Força a atualização da UI para mostrar o popup
            # --- Fim Popup ---

            # --- Agendar fechamento do popup após 8 segundos ---
            popup_duration = 8000 # 8 segundos em milissegundos
            self.root.after(popup_duration, popup.destroy)

            # --- Iniciar play_video em uma thread separada ---
            player_thread = threading.Thread(
                target=self._run_play_video_thread,
                args=(video_url_to_play, f"{self.selected_anime_title} - {episode_title_original}"),
                daemon=True)
            player_thread.start()

        except FileNotFoundError:
             self.update_status("Erro: Comando 'mpv' não encontrado.")
             print(f"[Main Thread Debug] play_selected_video: ERRO - mpv não encontrado", file=sys.stderr) # Log Adicional
             if popup: popup.destroy() # Garante que o popup feche em caso de erro
             messagebox.showerror("Erro", "Player 'mpv' não encontrado. Verifique a instalação.")
             self.root.after(0, self._re_enable_episode_selection) # Reabilita imediatamente
             return # Sai da função se o player não foi encontrado
        except Exception as play_err:
             print(f"[Main Thread Debug] play_selected_video: ERRO ao chamar play_video/criar popup: {play_err}", file=sys.stderr) # Log Adicional
             # Mensagem de erro mais informativa
             self.update_status(f"Erro ao iniciar player.")
             if popup: popup.destroy() # Garante que o popup feche em caso de erro
             messagebox.showerror("Erro ao Iniciar Player", f"Não foi possível iniciar o player MPV.\n\nCausas comuns:\n- O link do vídeo pode ter expirado ou estar protegido (Erro 403 Forbidden).\n- Problema na instalação do MPV ou dependências.\n\nErro original: {play_err}")
             self.root.after(0, self._re_enable_episode_selection) # Reabilita imediatamente
             return # Sai da função se houve erro ao iniciar


# --- Ponto de entrada ---
if __name__ == "__main__": # Protege a execução se importado
    root = tk.Tk()
    app = AnimeApp(root)
    root.mainloop()
