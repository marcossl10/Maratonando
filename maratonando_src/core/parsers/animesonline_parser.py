import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urljoin, quote
import logging

log = logging.getLogger(__name__)

BASE_URL_MINHASERIE = "https://www.minhaserie.site/"
HTTP_HEADERS_MINHASERIE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": BASE_URL_MINHASERIE,
}

class MinhaSerieParser:
    def __init__(self):
        pass

    def search(self, query: str) -> List[Dict[str, str]]:
        """Busca por conteúdo no minhaserie.site."""
        if not query:
            log.warning("[MinhaSerie] Query de busca vazia recebida.")
            return []
        
        search_term_encoded = quote(query)
        target_url = urljoin(BASE_URL_MINHASERIE, f"search/{search_term_encoded}")
        
        log.info(f"[MinhaSerie] Buscando por query: '{query}' em {target_url}")
        results = []
        try:
            response = requests.get(target_url, headers=HTTP_HEADERS_MINHASERIE, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # A estrutura correta é 'div.card-grid article.card'
            search_result_items = soup.select('div.card-grid article.card')
            log.debug(f"[MinhaSerie] Encontrados {len(search_result_items)} elementos 'div.card-grid article.card' na página de busca.")

            for item_container in search_result_items:
                link_tag = item_container.select_one('a.card-link')
                if not link_tag: continue

                title_tag = item_container.select_one('h3.card-title')
                title = title_tag.get_text(strip=True) if title_tag else "Sem Título"

                link_absolute = link_tag.get('href')

                img_tag = item_container.select_one('img.poster-img')
                img_src = img_tag.get('src') if img_tag else None
                img_src_absolute = urljoin(BASE_URL_MINHASERIE, img_src) if img_src and not img_src.startswith('http') else img_src

                meta_tag = item_container.select_one('p.card-meta')
                year = meta_tag.get_text(strip=True).split('•')[0].strip() if meta_tag else ""

                if title != "Sem Título" and link_absolute:
                    results.append({
                        "title": title,
                        "url": link_absolute,
                        "image": img_src_absolute or "",
                        "year": year,
                    })
            log.info(f"[MinhaSerie] Encontrados {len(results)} resultados para '{query}'.")
        except requests.exceptions.RequestException as e:
            log.error(f"[MinhaSerie] Erro de rede ao buscar '{query}': {e}", exc_info=False)
        except Exception as e:
            log.error(f"[MinhaSerie] Erro inesperado ao buscar '{query}': {e}", exc_info=True)
        return results

    def get_details(self, anime_url: str, fallback_image: str = "") -> Dict:
        """Busca detalhes (título, imagem, sinopse, episódios)."""
        log.info(f"[MinhaSerie] Buscando detalhes de: {anime_url}")
        details = {
            'title': 'Desconhecido',
            'image': fallback_image,
            'episodes': [],
            'type': 'series',
            'synopsis': '',
        }
        try:
            response = requests.get(anime_url, headers=HTTP_HEADERS_MINHASERIE, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            title_tag_main = soup.select_one('div.title-wrapper h1')
            if title_tag_main:
                details['title'] = title_tag_main.get_text(strip=True)
            
            cover_img_tag = soup.select_one('div.poster-wrapper img.poster-img')
            if cover_img_tag:
                img_src = cover_img_tag.get('src')
                if img_src:
                    details['image'] = urljoin(BASE_URL_MINHASERIE, img_src) if not img_src.startswith('http') else img_src

            synopsis_container = soup.select_one('div.synopsis p')
            if synopsis_container:
                details['synopsis'] = synopsis_container.get_text(strip=True)
            else:
                log.debug(f"[MinhaSerie] Container de sinopse ('div.synopsis p') não encontrado para {anime_url}")

            # A estrutura de episódios é uma lista de links
            episode_list_items = soup.select('ul.episode-list a.episode-card')
            if not episode_list_items:
                log.warning(f"[MinhaSerie] Nenhum item de episódio ('ul.episode-list a.episode-card') encontrado para {anime_url}.")

            for ep_link in episode_list_items:
                ep_url = ep_link.get('href')
                ep_title_tag = ep_link.select_one('h3.episode-title')
                ep_title = ep_title_tag.get_text(strip=True) if ep_title_tag else "Episódio"
                
                if ep_url and ep_title:
                    details['episodes'].append({
                        'title': ep_title,
                        'url': urljoin(BASE_URL_MINHASERIE, ep_url)
                    })

        except requests.exceptions.RequestException as e:
            log.error(f"[MinhaSerie] Erro de rede ao buscar detalhes ({anime_url}): {e}")
        except Exception as e:
            log.error(f"[MinhaSerie] Erro inesperado ao buscar detalhes ({anime_url}): {e}", exc_info=True)
        return details

    def get_video_source(self, episode_page_url: str) -> List[Dict[str, str]]:
        """Obtém a URL da fonte de vídeo da página do episódio."""
        log.info(f"[MinhaSerie] Buscando fontes de vídeo em: {episode_page_url}")
        video_sources = []
        try:
            response = requests.get(episode_page_url, headers=HTTP_HEADERS_MINHASERIE, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # O player está dentro de um iframe
            iframe = soup.select_one('div.player-content iframe')
            if iframe and iframe.get('src'):
                iframe_url = iframe['src']
                log.info(f"[MinhaSerie] Iframe do player encontrado: {iframe_url}")
                video_sources.append({'label': 'Player Principal', 'src': iframe_url})

        except requests.exceptions.RequestException as e:
            log.error(f"[MinhaSerie] Erro de rede ao buscar fontes de vídeo ({episode_page_url}): {e}")
        except Exception as e:
            log.error(f"[MinhaSerie] Erro inesperado ao buscar fontes de vídeo ({episode_page_url}): {e}", exc_info=True)

        if not video_sources:
            log.warning(f"[MinhaSerie] Nenhuma fonte de vídeo encontrada para {episode_page_url}.")
        return video_sources
