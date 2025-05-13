import flet as ft
import threading
import json
import os
from pathlib import Path
import time
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from .core.parsers import AnimeFireParser, AnimesOnlineParser
from .core.player import ExternalMediaPlayer

APP_NAME = "Maratonando"
APP_VERSION = "2.0.0"
PRIMARY_COLOR = ft.Colors.BLUE_700
BG_COLOR = ft.Colors.BLUE_GREY_900
CARD_COLOR = ft.Colors.BLUE_GREY_800
TEXT_COLOR = ft.Colors.WHITE
ACCENT_COLOR = ft.Colors.BLUE_700

CONFIG_DIR_NAME = "maratonando"
HISTORY_FILE = "history.json"

class FletAnimeApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = f"{APP_NAME} - v{APP_VERSION}"
        self.page.bgcolor = BG_COLOR
        self.page.theme_mode = ft.ThemeMode.DARK

        # Definindo as dimensões da janela
        # É importante que: min_width <= initial_width <= max_width
        # e min_height <= initial_height <= max_height

        initial_width = 700
        initial_height = 600

        self.page.window_min_width = 600
        self.page.window_min_height = 400
        self.page.window_max_width = 1280
        self.page.window_max_height = 720

        self.page.window_width = initial_width
        self.page.window_height = initial_height

        self.background_images = ["background1.png", "background2.png", "background3.png", "background4.png", "background5.png", "background6.png"]
        self.background_cycle_interval = 10
        self.current_background_index = 0

        self.bg_image = ft.Image(
            src=self.background_images[self.current_background_index],
            fit=ft.ImageFit.COVER,
            opacity=1.0,
            width=float("inf"),
            height=180,
            expand=False,
        )

        self.change_background_button = ft.IconButton(
            icon=ft.Icons.IMAGE_SEARCH_ROUNDED,
            tooltip="Mudar Imagem de Fundo",
            on_click=self.on_change_background_click,
            icon_color=ft.Colors.with_opacity(0.7, TEXT_COLOR),
            icon_size=24,
        )

        self.support_messages = [
            "Gostando do Maratonando? Considere apoiar o desenvolvimento me pagando um café? pix 83980601072!",
            "Sua ajuda mantém o app funcionando e melhorando. Projeto de um homem só!'.",
            "Pequenos gestos fazem uma grande diferença. Apoie o Maratonando!",
            "Ajude a manter este projeto vivo! Detalhes na aba 'Sobre'.",
            "Apoie o Maratonando pix 83980601072!",
        ]
        self.current_support_message_index = 0
        self.support_message_visible_duration = 20
        self.support_message_hidden_duration = 10
        self.support_message_text = ft.Text(
            value="",
            color=ft.Colors.AMBER_ACCENT_700,
            weight=ft.FontWeight.BOLD,
            size=13,
            text_align=ft.TextAlign.CENTER,
            visible=False
        )

        self.parser = None
        self.player = ExternalMediaPlayer()

        self.history_data = []
        self.max_history_items = 100
        self._setup_history_path()
        self.load_history()

        # Busca
        # Controle para selecionar o parser
        self.parser_selector = ft.SegmentedButton(
            selected={"AnimesOnline"},
            segments=[
                ft.Segment(value="AnimeFire", label=ft.Text("Servidor 1")),
                ft.Segment(value="AnimesOnline", label=ft.Text("Servidor 2")),
            ],
            on_change=self.on_parser_change,
            allow_empty_selection=False,
            allow_multiple_selection=False,
            style=ft.ButtonStyle(
                bgcolor={
                    "selected": ACCENT_COLOR,
                    "hovered": ft.Colors.with_opacity(0.1, ACCENT_COLOR),
                    "": CARD_COLOR,
                },
                color={"selected": ft.Colors.WHITE, "": TEXT_COLOR},
                shape=ft.RoundedRectangleBorder(radius=10),
            )
        )
        self.search_entry = ft.TextField(
            label="Buscar Anime/Série...",
            expand=True,
            bgcolor=CARD_COLOR,
            color=TEXT_COLOR,
            border_color=ACCENT_COLOR,
            focused_border_color=ACCENT_COLOR,
            cursor_color=ACCENT_COLOR,
            border_radius=10,
            height=48,
            text_size=18,
            on_submit=self.on_search,
        )
        self.search_button = ft.FilledButton(
            text="Buscar",
            icon=ft.Icons.SEARCH_ROUNDED,
            bgcolor=ACCENT_COLOR,
            color=ft.Colors.WHITE,
            height=48,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.on_search
        )
        self.search_progress_ring = ft.ProgressRing(visible=False, width=32, height=32, color=ACCENT_COLOR)
        self.search_results_list = ft.ListView(expand=True, spacing=8, height=336)
        self.search_results_container = ft.Container(
            self.search_results_list,
            bgcolor=CARD_COLOR,
            border_radius=10,
            padding=10,
            expand=True,
        )

        # Detalhes
        self.anime_image = ft.Image(
            src="https://via.placeholder.com/120x180?text=Sem+Capa",
            width=120,
            fit=ft.ImageFit.CONTAIN,
            border_radius=8,
            expand=False,
        )
        self.anime_image.visible = False
        self.anime_desc_text = ft.Text(
            "", size=16, color=ft.Colors.GREY_300, weight=ft.FontWeight.NORMAL,
            max_lines=2, overflow=ft.TextOverflow.ELLIPSIS
        )
        self.episodes_list_view = ft.ListView(expand=True, spacing=8)
        self.episodes_list_container = ft.Container(
            self.episodes_list_view,
            bgcolor=CARD_COLOR,
            border_radius=10,
            padding=10,
            expand=True,
        )

        # Histórico
        self.history_list_view = ft.ListView(expand=True, spacing=8, height=350)
        self.history_list_container = ft.Container(
            self.history_list_view,
            bgcolor=CARD_COLOR,
            border_radius=10,
            padding=10
        )
        self.clear_history_button = ft.FilledButton(
            "Limpar Histórico",
            icon=ft.Icons.DELETE_FOREVER_ROUNDED,
            bgcolor=ft.Colors.RED_700,
            color=ft.Colors.WHITE,
            height=44,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.on_clear_history
        )

        self.loading_text = ft.Text("", color=ft.Colors.WHITE, size=18)
        # Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Buscar",
                    icon=ft.Icons.SEARCH_ROUNDED,
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                self.parser_selector,
                                self.search_entry,
                                self.search_button,
                                self.search_progress_ring], spacing=10),
                            self.search_results_container,
                        ], spacing=16),
                        bgcolor=BG_COLOR,
                        border_radius=16,
                        padding=20,
                    )
                ),
                ft.Tab(
                    text="Episódios",
                    icon=ft.Icons.MOVIE_ROUNDED,
                    content=ft.Container(
                        ft.Row([
                            ft.Column([
                                self.anime_image,
                            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.START),
                            ft.Container(
                                ft.Column([
                                    self.loading_text,
                                    self.episodes_list_container,
                                ], spacing=8),
                                expand=True,
                                alignment=ft.alignment.top_left,
                                padding=0,
                                margin=0,
                            ),
                        ],
                        spacing=24,
                        vertical_alignment=ft.CrossAxisAlignment.START
                        ),
                        bgcolor=BG_COLOR,
                        border_radius=16,
                        padding=10
                    )
                ),
                ft.Tab(
                    text="Histórico",
                    icon=ft.Icons.HISTORY_EDU_ROUNDED,
                    content=ft.Container(
                        ft.Column([
                            ft.Row([self.clear_history_button], alignment=ft.MainAxisAlignment.END),
                            self.history_list_container,
                        ], spacing=16),
                        bgcolor=BG_COLOR,
                        border_radius=16,
                        padding=20,
                    )
                ),
                ft.Tab(
                    text="Sobre",
                    icon=ft.Icons.INFO_ROUNDED,
                    content=ft.Container(
                        content=self._build_about_content(),
                        bgcolor=BG_COLOR,
                        border_radius=16,
                        padding=20,
                        alignment=ft.alignment.center,
                        expand=True
                    )
                )
            ],
            expand=True,
            indicator_color=ACCENT_COLOR,
            label_color=ACCENT_COLOR,
            unselected_label_color=ft.Colors.GREY_400,
        )

        self.page.add(
            ft.Stack(
                [
                    self.bg_image,
                    ft.Container(
                        content=self.change_background_button,
                        alignment=ft.alignment.top_right,
                        padding=ft.padding.only(top=10, right=10)
                    )
                ]
            ),
            ft.Container(
                content=self.support_message_text,
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=5, bottom=5)
            ),
            self.tabs
        )

        self._initialize_parser(list(self.parser_selector.selected)[0])
        self.update_history()
        self._start_background_cycling_thread()
        self.page.update()
        self._start_support_message_cycler_thread()

    def on_change_background_click(self, e):
        """Alterna para a próxima imagem de fundo."""
        logging.debug("on_change_background_click: Iniciando troca de imagem.")
        if not self.background_images:
            logging.warning("on_change_background_click: Lista de imagens de fundo está vazia. Nada a fazer.")
            return
        if len(self.background_images) <= 1:
            logging.info("on_change_background_click: Não há imagens suficientes para ciclar.")
            return

        self.current_background_index = (self.current_background_index + 1) % len(self.background_images)
        new_image_src = self.background_images[self.current_background_index]
        self.bg_image.src = new_image_src
        logging.info(f"Imagem de fundo alterada para: {new_image_src}")
        self.bg_image.update()
        self.page.update()
        logging.debug("on_change_background_click: page.update() chamado.")

    def _start_background_cycling_thread(self):
        """Inicia a thread que troca a imagem de fundo automaticamente."""
        if len(self.background_images) > 1:
            thread = threading.Thread(target=self._background_cycling_task, daemon=True)
            thread.start()
            logging.info(f"_start_background_cycling_thread: Thread de troca de fundo iniciada com intervalo de {self.background_cycle_interval}s.")
        else:
            logging.info("_start_background_cycling_thread: Apenas uma ou nenhuma imagem de fundo disponível. Troca automática desativada.")

    def _background_cycling_task(self):
        """Tarefa em loop para trocar a imagem de fundo."""
        logging.debug("_background_cycling_task: Tarefa iniciada.")
        try:
            while True:
                time.sleep(self.background_cycle_interval)
                logging.debug(f"_background_cycling_task: Acordou após {self.background_cycle_interval}s. Agendando troca de imagem.")
                self.on_change_background_click(None)
                logging.debug("_background_cycling_task: Chamada para self.on_change_background_click() concluída.")
        except Exception as ex:
            logging.error(f"Erro fatal na thread _background_cycling_task: {ex}", exc_info=True)

    def _start_support_message_cycler_thread(self):
        """Inicia a thread que cicla as mensagens de apoio."""
        if self.support_messages:
            thread = threading.Thread(target=self._support_message_cycling_task, daemon=True)
            thread.start()
            logging.info("Thread de ciclagem de mensagens de apoio iniciada.")

    def _support_message_cycling_task(self):
        """Tarefa em loop para mostrar e esconder mensagens de apoio."""
        logging.debug("_support_message_cycling_task: Tarefa iniciada.")
        logging.debug(f"_support_message_cycling_task: Primeiro ciclo: dormindo por {self.support_message_hidden_duration}s antes da primeira mensagem.")
        try:
            while True:
                time.sleep(self.support_message_hidden_duration)

                if self.support_messages:
                    message_to_show = self.support_messages[self.current_support_message_index]
                    self.current_support_message_index = (self.current_support_message_index + 1) % len(self.support_messages)
                    
                    logging.debug(f"_support_message_cycling_task: Mostrando mensagem: {message_to_show}")
                    self.support_message_text.value = message_to_show
                    self.support_message_text.visible = True
                    self.page.update()

                    time.sleep(self.support_message_visible_duration)
                    logging.debug("_support_message_cycling_task: Escondendo mensagem.")
                    self.support_message_text.visible = False
                    self.page.update()
        except Exception as ex:
            logging.error(f"Erro fatal na thread _support_message_cycling_task: {ex}", exc_info=True)

    def _setup_history_path(self):
        home = Path.home()
        config_dir_parent_str = os.environ.get("XDG_CONFIG_HOME", str(home / ".config"))
        config_dir_parent = Path(config_dir_parent_str)
        self.config_dir = config_dir_parent / CONFIG_DIR_NAME
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.history_file_path = self.config_dir / HISTORY_FILE

    def load_history(self):
        if self.history_file_path.exists():
            try:
                with open(self.history_file_path, 'r', encoding='utf-8') as f:
                    self.history_data = json.load(f)
            except Exception:
                self.history_data = []
        else:
            self.history_data = []

    def save_history(self):
        try:
            with open(self.history_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")

    def _initialize_parser(self, parser_name):
        """Instancia o parser selecionado e atualiza o estado."""
        if parser_name == "AnimeFire":
            self.parser = AnimeFireParser()
            self.active_parser_name = "AnimeFire"
        elif parser_name == "AnimesOnline":
            self.parser = AnimesOnlineParser()
            self.active_parser_name = "AnimesOnline"
        else:
            self.parser = AnimesOnlineParser()
            self.active_parser_name = "AnimesOnline"
            self.parser_selector.selected = {"AnimesOnline"}
        logging.info(f"Parser ativo definido para: {self.active_parser_name}")

    def on_search(self, e):
        query = self.search_entry.value.strip()
        query = query.lower()
        self.search_results_list.controls.clear()
        self.search_progress_ring.visible = True
        self.page.update()
        if not query:
            self.search_results_list.controls.append(ft.Text("Digite algo para buscar!", color=ft.Colors.WHITE))
            self.search_progress_ring.visible = False
            self.page.update()
        else:
            thread = threading.Thread(target=self._search_thread, args=(query,))
            thread.start()

    def on_parser_change(self, e):
        """Lida com a mudança de seleção do parser."""
        selected_parser_name = list(e.control.selected)[0]
        logging.info(f"Mudando parser para: {selected_parser_name}")
        self._initialize_parser(selected_parser_name)
        self.clear_search_results()

    def _search_thread(self, query):
        try:
            results = self.parser.search(query)
            self._show_search_results(results)
        except Exception as ex:
            self._show_search_error(str(ex))

    def _show_search_results(self, results):
        self.search_results_list.controls.clear()
        self.search_progress_ring.visible = False
        if not results:
            self.search_results_list.controls.append(ft.Text("Nenhum resultado encontrado.", color=ft.Colors.WHITE))
        else:
            for anime in results:
                item = ft.Container(
                    content=ft.ListTile(
                        leading=ft.Image(
                            src=anime.get("image") or anime.get("cover") or "",
                            width=48,
                            height=64,
                            fit=ft.ImageFit.COVER,
                            border_radius=8,
                        ) if anime.get("image") or anime.get("cover") else None,
                        title=ft.Text(anime.get("title", "Sem título"), color=ft.Colors.WHITE, size=18, overflow=ft.TextOverflow.ELLIPSIS),
                        data=anime,
                        on_click=self.on_result_click,
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
                    border_radius=8,
                    border=ft.border.all(2, ACCENT_COLOR)
                )
                self.search_results_list.controls.append(item)
        self.page.update()

    def _show_search_error(self, msg):
        self.search_results_list.controls.clear()
        self.search_progress_ring.visible = False
        self.search_results_list.controls.append(ft.Text(f"Erro: {msg}", color=ft.Colors.WHITE))
        self.page.update()

    def on_result_click(self, e):
        anime = e.control.data
        self.episodes_list_view.controls.clear()
        thread = threading.Thread(target=self._details_thread, args=(anime,))
        thread.start()

    def clear_search_results(self):
        """Limpa os resultados da busca e a lista de episódios na UI."""
        self.search_entry.value = ""
        self.search_results_list.controls.clear()
        self.episodes_list_view.controls.clear()
        self.page.update()
    def _details_thread(self, anime):
        try:
            details = self.parser.get_details(anime["url"], fallback_image=anime.get("image", ""))
            if not details.get("cover_url"):
                if anime.get("image", ""):
                    details["cover_url"] = anime.get("image", "")
                else:
                    details["cover_url"] = "https://via.placeholder.com/200x300?text=Sem+Capa"
            details["image"] = details["cover_url"]
            episodes = details.get("episodes", [])
            self._show_episodes(anime, episodes)
            img_url = details.get("image")
            self.anime_image.visible = True
            self.anime_image.src = img_url or "https://via.placeholder.com/120x180?text=Sem+Capa"
            self.anime_desc_text.value = anime.get("title", "Sem título")
            self.page.update()
        except Exception as ex:
            self._show_episodes_error(str(ex))

    def _show_episodes(self, anime, episodes):
        self.episodes_list_view.controls.clear()
        if not episodes:
            self.episodes_list_view.controls.append(ft.Text("Nenhum episódio encontrado.", color=ft.Colors.WHITE))
        else:
            for ep in episodes:
                ep_title = ep.get("title", "Episódio")
                ep_url = ep.get("url")
                item = ft.Container(
                    content=ft.ListTile(
                        title=ft.Text(ep_title, color=ft.Colors.WHITE, size=16, overflow=ft.TextOverflow.ELLIPSIS),
                        on_click=lambda ev, anime=anime, ep=ep: self.on_episode_click(anime, ep),
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
                    border_radius=8,
                    border=ft.border.all(2, ACCENT_COLOR)
                )
                self.episodes_list_view.controls.append(item)
        self.tabs.selected_index = 1
        self.page.update()

    def _show_episodes_error(self, msg):
        self.episodes_list_view.controls.clear()
        self.episodes_list_view.controls.append(ft.Text(f"Erro: {msg}", color=ft.Colors.WHITE))
        self.page.update()

    def on_episode_click(self, anime, ep):
        anime_title = anime.get("title", "Sem título")
        episode_title = ep.get("title", "Episódio")
        episode_url = ep.get("url")
        self.add_to_history(anime_title, episode_title, anime.get("url"), episode_url, anime.get("image", ""))

        self.loading_text.value = "Abrindo player, aguarde... pode levar até 30 segundos"
        self.page.update()

        thread = threading.Thread(target=self._play_thread, args=(ep, episode_title))
        thread.start()

    def _play_thread(self, ep, episode_title):
        try:
            video_url = self.parser.get_video_source(ep["url"])
            if isinstance(video_url, list) and video_url:
                video_url = video_url[-1].get("src")
            if not video_url:
                raise Exception("Não foi possível obter o link do vídeo.")
            result = self.player.play_episode(video_url, episode_title)

            self.loading_text.value = ""
            self.page.update()

            if isinstance(result, int) and result != 0:
                self._show_episodes_error(f"Erro ao abrir o player (código {result}).")
        except Exception as ex:
            self.loading_text.value = ""
            self.page.update()
            self._show_episodes_error(f"Erro ao tocar: {ex}")

    def add_to_history(self, anime_title, episode_title, anime_url, episode_url, anime_image=""):
        prev_fav = False
        for item in self.history_data:
            if item.get('anime_title') == anime_title and item.get('episode_title') == episode_title:
                prev_fav = item.get('favorite', False)
        self.history_data = [
            item for item in self.history_data
            if not (item.get('anime_title') == anime_title and item.get('episode_title') == episode_title)
        ]
        new_entry = {
            "anime_title": anime_title,
            "episode_title": episode_title,
            "anime_url": anime_url,
            "episode_url": episode_url,
            "timestamp": int(time.time()),
            "favorite": prev_fav,
            "image": anime_image,
        }
        self.history_data.append(new_entry)
        if len(self.history_data) > self.max_history_items:
            self.history_data = self.history_data[-self.max_history_items:]
        self.save_history()
        self.update_history()

    def update_history(self):
        self.history_list_view.controls.clear()
        if not self.history_data:
            self.history_list_view.controls.append(
                ft.Text("Histórico vazio.", color=ft.Colors.LIME_400)
            )
        else:
            for item in reversed(self.history_data):
                anime_title = item.get("anime_title", "Desconhecido")
                episode_title = item.get("episode_title", "Episódio")
                is_fav = item.get("favorite", False)
                fav_icon = ft.IconButton(
                    icon=ft.Icons.FAVORITE_ROUNDED if is_fav else ft.Icons.FAVORITE_BORDER_ROUNDED,
                    icon_color=ft.Colors.RED_400 if is_fav else ft.Colors.GREY_400,
                    tooltip="Favoritar" if not is_fav else "Remover dos favoritos",
                    on_click=lambda e, i=item: self.toggle_favorite(i)
                )
                def make_on_click(anime_url, image):
                    return lambda e: self.on_history_details(anime_url, image)
                self.history_list_view.controls.append(
                    ft.Container(
                        content=ft.Row([
                            fav_icon,
                            ft.ListTile(
                                title=ft.Text(anime_title, color=TEXT_COLOR, size=16, no_wrap=True),
                                subtitle=ft.Text(episode_title, color=ft.Colors.GREY_300, no_wrap=True),
                                on_click=make_on_click(item.get("anime_url"), item.get("image", "")),
                                shape=ft.RoundedRectangleBorder(radius=8)
                            ),
                        ]),
                        bgcolor=ft.Colors.BLUE_GREY_800,
                        border_radius=8,
                    )
                )
        self.page.update()

    def toggle_favorite(self, item):
        for h in self.history_data:
            if h.get("anime_title") == item.get("anime_title") and h.get("episode_title") == item.get("episode_title"):
                h["favorite"] = not h.get("favorite", False)
                break
        self.save_history()
        self.update_history()

    def on_history_details(self, anime_url, anime_image=""):
        item = next((h for h in self.history_data if h.get("anime_url") == anime_url), None)
        if item:
            anime = {
                "title": item.get("anime_title", "Sem título"),
                "url": item.get("anime_url"),
                "image": anime_image or item.get("image", ""),
            }
            thread = threading.Thread(target=self._details_thread, args=(anime,))
            thread.start()

    def on_clear_history(self, e):
        self.history_data.clear()
        self.save_history()
        self.update_history()

    def _build_about_content(self):
        """Constrói e retorna o conteúdo da aba 'Sobre'."""
        return ft.Column(
            [
                ft.Text(APP_NAME, size=32, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Text(f"Versão: {APP_VERSION}", size=18, color=ft.Colors.GREY_400),
                ft.Divider(height=20, color=ft.Colors.with_opacity(0.5, TEXT_COLOR)),
                ft.Text("Desenvolvido por:", size=16, color=TEXT_COLOR),
                ft.Text("Marcos", size=20, weight=ft.FontWeight.W_500, color=ACCENT_COLOR),
                ft.Container(
                    content=ft.Text(
                        "GitHub: marcossl10",
                        size=16,
                        color=ACCENT_COLOR,
                    ),
                    on_click=lambda e: self.page.launch_url("https://github.com/marcossl10"),
                ),
                ft.Container(
                    content=ft.Text("Contato:", size=16, color=TEXT_COLOR),
                    margin=ft.margin.only(top=15)
                ),
                ft.Text("marcosslprado@gmail.com", size=18, color=ACCENT_COLOR),
                ft.Divider(height=20, color=ft.Colors.with_opacity(0.5, TEXT_COLOR)),
                ft.Text(
                    "Este aplicativo permite buscar e assistir animes de diversas fontes.",
                    size=14,
                    color=ft.Colors.GREY_300,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Divider(height=20, color=ft.Colors.with_opacity(0.5, TEXT_COLOR)),
                ft.Text(
                    "Me paga um café? PIX 83980601072",
                    size=18,
                    color=ft.Colors.AMBER_ACCENT_700,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )

def main(page: ft.Page):
    FletAnimeApp(page)

if __name__ == "__main__":
    ft.app(target=main)
