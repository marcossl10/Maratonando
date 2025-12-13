import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urljoin, quote
import logging

log = logging.getLogger(__name__)

BASE_URL_MINHASERIE = "https://minhaserie.stream/"
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

            # A estrutura correta para os episódios é 'section.episodes-modern-section div.episodes-modern-item'
            episode_list_items = soup.select('section.episodes-modern-section div.episodes-modern-item')
            log.info(f"[MinhaSerie] Encontrados {len(episode_list_items)} itens de episódio com o seletor 'div.episodes-modern-item'.")

            if episode_list_items:
                for ep_item in episode_list_items:
                    link_tag = ep_item.select_one('a.episodes-modern-download-btn')
                    title_tag = ep_item.select_one('h3.episodes-modern-item-title')

                    if link_tag and title_tag and link_tag.get('href'):
                        ep_url = link_tag['href']
                        ep_title = title_tag.get_text(strip=True)
                        details['episodes'].append({'title': ep_title, 'url': urljoin(BASE_URL_MINHASERIE, ep_url)})
                    else:
                        log.warning("[MinhaSerie] Item de episódio encontrado, mas sem link ou título.")
            else:
                log.warning("[MinhaSerie] Seletor 'section.episodes-modern-section div.episodes-modern-item' não encontrou episódios.")

            if not details['episodes']:
                log.warning(f"[MinhaSerie] Nenhum episódio encontrado para {anime_url} após verificar temporadas e página principal.")

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
