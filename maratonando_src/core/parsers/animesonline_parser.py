import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote_plus, urlparse, parse_qs
import logging
import re

log = logging.getLogger(__name__)

BASE_URL_ANIMESONLINE = "https://animesonlinecc.to/"
HTTP_HEADERS_ANIMESONLINE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": BASE_URL_ANIMESONLINE,
    "X-Requested-With": "XMLHttpRequest"
}

class AnimesOnlineParser:
    def __init__(self):
        pass

    def search(self, query: str) -> List[Dict[str, str]]:
        """
        Busca por animes no animesonlinecc.to usando a query fornecida.
        """
        if not query:
            log.warning("[AnimesOnline] Query de busca vazia recebida.")
            return []
        search_term_encoded = quote_plus(query)
        target_url = f"{BASE_URL_ANIMESONLINE}?s={search_term_encoded}"
        log.info(f"[AnimesOnline] Buscando por query: '{query}' em {target_url}")
        results = []
        try:
            response = requests.get(target_url, headers=HTTP_HEADERS_ANIMESONLINE, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            search_result_items = soup.select('div.result-item')
            log.debug(f"[AnimesOnline] Encontrados {len(search_result_items)} elementos 'div.result-item' na página de busca.")

            for item_container in search_result_items:
                title_tag = item_container.select_one('div.details div.title a')
                title = title_tag.get_text(strip=True) if title_tag else "Sem título"

                link_relative = title_tag['href'] if title_tag else None
                link_absolute = urljoin(BASE_URL_ANIMESONLINE, link_relative) if link_relative else None

                img_tag = item_container.select_one('div.image img')
                img_src = (img_tag.get('data-src') or img_tag.get('src')) if img_tag else None
                img_src_absolute = urljoin(BASE_URL_ANIMESONLINE, img_src) if img_src and not img_src.startswith('http') else img_src

                year_tag = item_container.select_one('div.details div.meta span.year')
                year = year_tag.get_text(strip=True) if year_tag else ""

                if title != "Sem título" and link_absolute:
                    results.append({
                        "title": title,
                        "url": link_absolute,
                        "image": img_src_absolute or "",
                        "year": year,
                        "source": "AnimesOnline"
                    })
            log.info(f"[AnimesOnline] Encontrados {len(results)} resultados para '{query}'.")
        except requests.exceptions.RequestException as e:
            log.error(f"[AnimesOnline] Erro de rede ao buscar '{query}': {e}", exc_info=False)
        except Exception as e:
            log.error(f"[AnimesOnline] Erro inesperado ao buscar '{query}': {e}", exc_info=True)
        return results

    def get_details(self, anime_url: str, fallback_image: str = "") -> Dict:
        """
        Busca detalhes (título, imagem, lista de episódios) de um anime.
        """
        log.info(f"[AnimesOnline] Buscando detalhes de: {anime_url}")
        details = {
            'title': 'Desconhecido',
            'image': fallback_image,
            'episodes': [], # Lista para armazenar {'title': 'Nome Ep', 'url': 'link_ep'}
            'type': 'series', # Assume series por padrão
            'synopsis': '', # Inicializa com string vazia
            'source': 'AnimesOnline'
        }
        try:
            response = requests.get(anime_url, headers=HTTP_HEADERS_ANIMESONLINE, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            title_tag_main = soup.select_one('div.data h1')
            if title_tag_main:
                details['title'] = title_tag_main.get_text(strip=True)
            else:
                title_tag_main = soup.select_one('div.sheader h1.title')
                if title_tag_main:
                    details['title'] = title_tag_main.get_text(strip=True)
            
            cover_img_tag = soup.select_one('div.poster img.wp-post-image') or soup.select_one('div.poster img')
            if cover_img_tag:
                img_src = (cover_img_tag.get('data-src') or cover_img_tag.get('src'))
                if img_src:
                    details['image'] = urljoin(BASE_URL_ANIMESONLINE, img_src) if not img_src.startswith('http') else img_src
            
            if not details.get('image') or details['image'] == fallback_image:
                gallery_img_tag = soup.select_one('div#dt_galery div.g-item img')
                if gallery_img_tag:
                    img_src = (gallery_img_tag.get('data-src') or gallery_img_tag.get('src'))
                    if img_src:
                        details['image'] = urljoin(BASE_URL_ANIMESONLINE, img_src) if not img_src.startswith('http') else img_src

            synopsis_container = soup.select_one('div.extra div.wp-content')
            if synopsis_container:
                for p_tag in synopsis_container.select('p'):
                    p_text = p_tag.get_text(strip=True)
                    if p_text.lower().startswith('sinopse:'):
                        # Garante que a sinopse não seja vazia após o replace
                        synopsis_text = p_text.replace('Sinopse:', '', 1).strip()
                        details['synopsis'] = synopsis_text if synopsis_text else "Sinopse não disponível."
                        break
            else:
                log.debug(f"[AnimesOnline] Container de sinopse ('div.extra div.wp-content') não encontrado para {anime_url}")

            episode_list_html_items = []
            
            season_episode_lists_containers = soup.select('div#seasons div.se-c ul.episodios')
            if season_episode_lists_containers:
                log.debug(f"[AnimesOnline] Encontrados {len(season_episode_lists_containers)} container(es) de lista de episódios de temporada (div#seasons div.se-c ul.episodios).")
                for ep_list_ul in season_episode_lists_containers:
                    episode_list_html_items.extend(ep_list_ul.select('li'))
            else:
                log.debug("[AnimesOnline] Estrutura de temporadas (div#seasons div.se-c ul.episodios) não encontrada.")

            if not episode_list_html_items:
                log.debug("[AnimesOnline] Tentando seletor mais genérico 'ul.episodios li'.")
                episode_list_html_items = soup.select('ul.episodios li')
                if episode_list_html_items:
                    log.debug(f"[AnimesOnline] Encontrados {len(episode_list_html_items)} itens com 'ul.episodios li'.")
                else:
                    log.debug("[AnimesOnline] Seletor 'ul.episodios li' também não encontrou itens.")
            
            # Tentativa 3: Outro padrão comum se os anteriores falharem
            if not episode_list_html_items:
                log.debug("[AnimesOnline] Tentando seletor 'div.episodioslista ul li'.")
                episode_list_html_items = soup.select('div.episodioslista ul li')
                if episode_list_html_items:
                    log.debug(f"[AnimesOnline] Encontrados {len(episode_list_html_items)} itens com 'div.episodioslista ul li'.")
                else:
                    log.debug("[AnimesOnline] Seletor 'div.episodioslista ul li' também não encontrou itens.")


            if not episode_list_html_items:
                log.warning(f"[AnimesOnline] Nenhum item de episódio (li) encontrado com os seletores testados para {anime_url}.")
            else:
                log.info(f"[AnimesOnline] Encontrados {len(episode_list_html_items)} itens de episódio HTML (li) para processar para {anime_url}.")

            for ep_item_li in episode_list_html_items:
                ep_title_tag = ep_item_li.select_one('div.episodiotitle a')
                if not ep_title_tag:
                    ep_title_tag = ep_item_li.select_one('a') 

                if ep_title_tag:
                    ep_title = ep_title_tag.get_text(strip=True)
                    ep_url_relative = ep_title_tag.get('href')
                    if ep_title and ep_url_relative:
                        details['episodes'].append({
                            'title': ep_title,
                            'url': urljoin(BASE_URL_ANIMESONLINE, ep_url_relative)
                        })
                    else:
                        log.debug(f"[AnimesOnline] Item de episódio HTML encontrado, mas título ou URL ausente: {ep_title_tag.prettify()[:100]}")
                else:
                    log.debug(f"[AnimesOnline] Tag de título do episódio não encontrada no item HTML: {ep_item_li.prettify()[:100]}")
            
            if not details['episodes']:
                log.warning(f"[AnimesOnline] Lista de episódios não encontrada ou seletor incorreto para {anime_url}. Verifique o HTML da página do anime.")

        except requests.exceptions.RequestException as e:
            log.error(f"[AnimesOnline] Erro de rede ao buscar detalhes ({anime_url}): {e}")
        except Exception as e:
            log.error(f"[AnimesOnline] Erro inesperado ao buscar detalhes ({anime_url}): {e}", exc_info=True)
        return details

    def get_video_source(self, episode_page_url: str) -> List[Dict[str, str]]:
        log.info(f"[AnimesOnline] Buscando fontes de vídeo em: {episode_page_url}")
        video_sources = []
        try:
            response = requests.get(episode_page_url, headers=HTTP_HEADERS_ANIMESONLINE, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            player_options = soup.select("ul#playeroptionsul li.dooplay_player_option")
            log.debug(f"[AnimesOnline] Encontradas {len(player_options)} opções de player.")

            for option_li in player_options:
                option_label = option_li.select_one("span.title").get_text(strip=True) if option_li.select_one("span.title") else "Player"
                data_nume = option_li.get("data-nume")
                data_post = option_li.get("data-post")
                data_type = option_li.get("data-type")

                if not all([data_nume, data_post, data_type]):
                    log.warning(f"[AnimesOnline] Opção de player '{option_label}' sem atributos data necessários. Pulando.")
                    continue

                embed_url_from_api = None

                rest_api_url = urljoin(BASE_URL_ANIMESONLINE, f"wp-json/dooplayer/v2/{data_post}/{data_type}/{data_nume}")
                log.debug(f"[AnimesOnline] Tentativa 1: Fazendo requisição GET para API REST: {rest_api_url} para '{option_label}'")
                try:
                    rest_response = requests.get(rest_api_url, headers=HTTP_HEADERS_ANIMESONLINE, timeout=15)
                    if rest_response.status_code == 200:
                        rest_data = rest_response.json()
                        embed_url_from_api = rest_data.get("embed_url")
                        if embed_url_from_api:
                            log.info(f"[AnimesOnline] Tentativa 1 SUCESSO: 'embed_url' obtida via API REST para '{option_label}': {embed_url_from_api}")
                        else:
                            log.warning(f"[AnimesOnline] Tentativa 1: API REST retornou JSON, mas sem 'embed_url' para '{option_label}'.")
                    else:
                        log.warning(f"[AnimesOnline] Tentativa 1 FALHA: API REST retornou status {rest_response.status_code} para '{option_label}'.")
                except requests.exceptions.RequestException as rest_req_err:
                    log.error(f"[AnimesOnline] Tentativa 1 ERRO: Erro na requisição para API REST para '{option_label}': {rest_req_err}")
                except ValueError as rest_json_err:
                    log.error(f"[AnimesOnline] Tentativa 1 ERRO: Erro ao decodificar JSON da API REST para '{option_label}': {rest_json_err}. Resposta: {rest_response.text[:200]}")

                if not embed_url_from_api:
                    log.debug(f"[AnimesOnline] Tentativa 2: Recorrendo à chamada AJAX POST para '{option_label}'")
                    ajax_url = urljoin(BASE_URL_ANIMESONLINE, "wp-admin/admin-ajax.php")
                    payload = {
                        'action': 'dooplay_player_ajax',
                        'post': data_post,
                        'nume': data_nume,
                        'type': data_type
                    }
                    log.debug(f"[AnimesOnline] Fazendo requisição AJAX POST para '{option_label}' com payload: {payload}")
                    try:
                        ajax_response = requests.post(ajax_url, data=payload, headers=HTTP_HEADERS_ANIMESONLINE, timeout=15)
                        ajax_response.raise_for_status()
                        ajax_data = ajax_response.json()
                        embed_url_from_api = ajax_data.get("embed_url")
                        if embed_url_from_api:
                            log.info(f"[AnimesOnline] Tentativa 2 SUCESSO: 'embed_url' obtida via AJAX POST para '{option_label}': {embed_url_from_api}")
                        else:
                            log.warning(f"[AnimesOnline] Tentativa 2: AJAX POST retornou JSON, mas sem 'embed_url' para '{option_label}'.")
                    except requests.exceptions.RequestException as req_err:
                        log.error(f"[AnimesOnline] Tentativa 2 ERRO: Erro na requisição AJAX POST para '{option_label}': {req_err}")
                    except ValueError as json_err:
                        log.error(f"[AnimesOnline] Tentativa 2 ERRO: Erro ao decodificar JSON da AJAX POST para '{option_label}': {json_err}. Resposta: {ajax_response.text[:200]}")

                if embed_url_from_api:
                    parsed_player_url = urlparse(embed_url_from_api)
                    query_params_player = parse_qs(parsed_player_url.query)

                    if 'source' in query_params_player and query_params_player['source']:
                        direct_video_url = query_params_player['source'][0]
                        log.info(f"[AnimesOnline] Link direto encontrado para '{option_label}': {direct_video_url}")
                        video_sources.append({'label': option_label, 'src': direct_video_url})
                    else:
                        log.warning(f"[AnimesOnline] Parâmetro 'source' não encontrado na URL do player '{embed_url_from_api}' para '{option_label}'. Adicionando URL do player como fallback.")
                        video_sources.append({'label': f"{option_label} (Player Page)", 'src': embed_url_from_api})
                else:
                    log.warning(f"[AnimesOnline] Nenhuma 'embed_url' obtida para '{option_label}' após todas as tentativas.")

        except requests.exceptions.RequestException as e:
            log.error(f"[AnimesOnline] Erro de rede ao buscar fontes de vídeo ({episode_page_url}): {e}")
        except Exception as e:
            log.error(f"[AnimesOnline] Erro inesperado ao buscar fontes de vídeo ({episode_page_url}): {e}", exc_info=True)
        
        if not video_sources:
            log.warning(f"[AnimesOnline] Nenhuma fonte de vídeo encontrada para {episode_page_url} pela estratégia principal.")

        if video_sources:
            log.info(f"[AnimesOnline] Fontes de vídeo encontradas para {episode_page_url}: {video_sources}")
        return video_sources
