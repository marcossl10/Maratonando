import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from urllib.parse import urljoin
import logging
import socket
from requests.packages.urllib3.util.connection import HAS_IPV6

logging.getLogger(__name__).info("[AnimeFire Parser] Módulo importado com sucesso.")
log = logging.getLogger(__name__)

BASE_URL = "https://animefire.io/" # Garantindo o novo domínio
SEARCH_URL_TEMPLATE = BASE_URL + "pesquisar/{query}"

orig_allowed_gai_family = None

def _set_ipv4():
    """Força a resolução de nomes para IPv4."""
    global orig_allowed_gai_family
    if HAS_IPV6:
        orig_allowed_gai_family = socket.getaddrinfo.__defaults__[0]
        socket.getaddrinfo.__defaults__ = (socket.AF_INET,) + socket.getaddrinfo.__defaults__[1:]

def _unset_ipv4():
    """Restaura a configuração original de resolução de nomes."""
    if HAS_IPV6 and orig_allowed_gai_family is not None:
        socket.getaddrinfo.__defaults__ = (orig_allowed_gai_family,) + socket.getaddrinfo.__defaults__[1:]

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': BASE_URL,
}

class AnimeFireParser:
    def __init__(self):
        pass

    def search(self, query: str) -> List[Dict[str, str]]:
        """
        Busca por animes no AnimeFire.io.
        Retorna uma lista de dicionários, cada um contendo 'title', 'url' e 'image'.
        """
        log.info(f"[AnimeFire] Função search iniciada para query: '{query}'")
        formatted_query = query.replace(' ', '-')
        search_query_url = SEARCH_URL_TEMPLATE.format(query=formatted_query)
        results = []
        processed_urls = set()

        _set_ipv4()
        try:
            response = requests.get(search_query_url, headers=HTTP_HEADERS, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            result_items = soup.find_all('div', class_='divCardUltimosEps')

            if not result_items:
                log.warning("[AnimeFire] Nenhum item de resultado ('div.divCardUltimosEps') encontrado na página /pesquisar/.")
                return []

            log.info(f"[AnimeFire] Encontrados {len(result_items)} itens de resultado.")
            for item_div in result_items:
                link_tag = item_div.find('a', href=True)
                title_tag = item_div.find('h3', class_='animeTitle')
                img_tag = item_div.find('img', class_='card-img-top')

                if link_tag and title_tag:
                    title = title_tag.get_text(strip=True)
                    url = link_tag['href']
                    absolute_url = urljoin(BASE_URL, url)
                    image_url = ""
                    if img_tag:
                        image_url = img_tag.get('src') or img_tag.get('data-src') or ""
                        if image_url and not image_url.startswith("http"):
                            image_url = urljoin(BASE_URL, image_url)

                    if absolute_url.startswith(BASE_URL) and "/animes/" in absolute_url and absolute_url not in processed_urls:
                        log.debug(f"    [AnimeFire] Item encontrado: {title} - {absolute_url}")
                        results.append({'title': title, 'url': absolute_url, 'image': image_url})
                        processed_urls.add(absolute_url)
                    else:
                        log.debug(f"    [AnimeFire] Item ignorado (URL inválida ou duplicada): {title} - {absolute_url}")
                else:
                    log.debug(f"    [AnimeFire] Item ignorado (link ou título faltando).")
        except Exception as e:
            log.error(f"[AnimeFire] ERRO na função search: {e}", exc_info=True)
            return []
        finally:
            _unset_ipv4()
            log.debug(f"[AnimeFire] Função search finalizada para query '{query}'. Retornando {len(results)} resultados.")
        return results

    def get_details(self, anime_url: str, fallback_image: str = "") -> Dict:
        """Busca detalhes e lista de episódios de um anime."""
        log.info(f"[AnimeFire] Buscando detalhes de: {anime_url}")
        details = {'episodes': [], 'type': 'series', 'title': 'Desconhecido', 'cover_url': None}

        _set_ipv4()
        try:
            response = requests.get(anime_url, headers=HTTP_HEADERS, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            title_tag = soup.find('h1', class_='aniTitulo')
            if title_tag:
                details['title'] = title_tag.text.strip()
                log.debug(f"    [AnimeFire] Título encontrado: {details['title']}")

            # Tenta encontrar a imagem da capa por vários seletores
            cover_url = None

            # 1. Tenta pelo seletor original
            cover_img_tag = soup.select_one('div.aniCover img.imgAnime')
            if cover_img_tag and cover_img_tag.get('src'):
                cover_url = urljoin(BASE_URL, cover_img_tag['src'])

            # 2. Tenta por qualquer img.imgAnime
            if not cover_url:
                generic_img = soup.find('img', class_='imgAnime')
                if generic_img and generic_img.get('src'):
                    cover_url = urljoin(BASE_URL, generic_img['src'])

            # 3. Tenta por qualquer img com alt parecido com o título
            if not cover_url and 'title' in details:
                alt_img = soup.find('img', alt=re.compile(details['title'], re.I))
                if alt_img and alt_img.get('src'):
                    cover_url = urljoin(BASE_URL, alt_img['src'])

            # 4. Tenta pegar a primeira imagem grande da página
            if not cover_url:
                big_img = soup.find('img', src=re.compile(r'-large\.webp$'))
                if big_img and big_img.get('src'):
                    cover_url = urljoin(BASE_URL, big_img['src'])

            if not cover_url:
                cover_url = fallback_image  # Usa a imagem da busca como fallback

            details['cover_url'] = cover_url
            details['image'] = cover_url or ""

            synopsis_tag = soup.find('div', class_='aniSinopse')
            if synopsis_tag:
                details['synopsis'] = synopsis_tag.text.strip()
                log.debug(f"    [AnimeFire] Sinopse encontrada.")

            episode_links = soup.find_all('a', class_='lEp epT divNumEp smallbox px-2 mx-1 text-left d-flex')
            if episode_links:
                log.info(f"[AnimeFire] Encontrados {len(episode_links)} links de episódios.")
                raw_episodes = []
                for link_tag in episode_links:
                    ep_page_url = urljoin(BASE_URL, link_tag['href'])
                    ep_title_text = link_tag.get_text(strip=True)
                    num_match = re.search(r'\d+', ep_title_text)
                    ep_num = int(num_match.group(0)) if num_match else 9999
                    raw_episodes.append({'num': ep_num, 'title': ep_title_text, 'url': ep_page_url})
                raw_episodes.sort(key=lambda x: x['num'])
                details['episodes'] = [{'title': ep['title'], 'url': ep['url']} for ep in raw_episodes]
            else:
                log.warning("[AnimeFire] Nenhum link de episódio ('a.lEp...') encontrado.")
        except requests.exceptions.RequestException as e:
            log.error(f"[AnimeFire] Erro de rede ao buscar detalhes ({anime_url}): {e}", exc_info=False)
        except Exception as e:
            log.error(f"[AnimeFire] Erro inesperado ao buscar detalhes ({anime_url}): {e}", exc_info=True)
        finally:
            details["image"] = details.get("cover_url", "")
            _unset_ipv4()
        return details

    def get_video_source(self, episode_page_url: str) -> List[Dict[str, str]]:
        """
        Obtém a URL da fonte de vídeo da página do episódio.
        Retorna uma lista de dicionários {'label': 'qualidade', 'src': 'url_video'}
        """
        log.info(f"[AnimeFire] Buscando fontes de vídeo em: {episode_page_url}")
        _set_ipv4()
        try:
            response = requests.get(episode_page_url, headers=HTTP_HEADERS, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            video_tag = soup.find('video', attrs={'data-video-src': True})
            if video_tag:
                intermediate_url = video_tag.get('data-video-src')
                if intermediate_url:
                    absolute_intermediate_url = urljoin(episode_page_url, intermediate_url)
                    log.info(f"[AnimeFire] Encontrada URL intermediária em data-video-src: {absolute_intermediate_url}")
                    try:
                        video_data_response = requests.get(absolute_intermediate_url, headers=HTTP_HEADERS, timeout=15)
                        video_data_response.raise_for_status()
                        video_data = video_data_response.json()
                        sources = []
                        if video_data and 'data' in video_data and isinstance(video_data['data'], list):
                            for item in video_data['data']:
                                if item.get('src') and item.get('label'):
                                    sources.append({'label': item['label'], 'src': item['src']})
                                    log.debug(f"  [AnimeFire] Qualidade encontrada: {item['label']} -> {item['src']}")
                            if sources:
                                log.info(f"[AnimeFire] Extraídas {len(sources)} fontes diretas da URL intermediária.")
                                return sources
                            else:
                                log.warning("[AnimeFire] Resposta da URL intermediária não continha fontes válidas.")
                        else:
                            log.warning("[AnimeFire] Formato inesperado da resposta da URL intermediária.")
                    except Exception as e:
                        log.error(f"[AnimeFire] Erro ao processar URL intermediária ({absolute_intermediate_url}): {e}", exc_info=True)
                else:
                    log.warning("[AnimeFire] Tag <video> encontrada, mas sem atributo 'data-video-src'.")
            # Fallback para iframe
            log.info("[AnimeFire] Estratégia <video> falhou ou não aplicável. Tentando fallback para <iframe>.")
            video_div = soup.find("div", id="div_video")
            iframe = None
            if video_div:
                iframe = video_div.find("iframe")
                log.debug("[AnimeFire] Encontrado div#div_video, procurando iframe dentro.")
            else:
                log.warning("[AnimeFire] div#div_video não encontrado, tentando busca global por iframe.")
                iframe = soup.find("iframe", src=re.compile(r"video|blogger", re.IGNORECASE))
            if iframe and iframe.get("src"):
                iframe_src = iframe["src"]
                absolute_iframe_src = urljoin(episode_page_url, iframe_src)
                log.info(f"[AnimeFire] Encontrada URL de vídeo no src do iframe (fallback): {absolute_iframe_src}")
                return [{"label": "iframe", "src": absolute_iframe_src}]
            else:
                log.warning("[AnimeFire] Nenhum iframe válido encontrado na página (fallback).")
            return []
        except requests.exceptions.RequestException as e:
            log.error(f"[AnimeFire] Erro de rede ao buscar fontes de vídeo ({episode_page_url}): {e}", exc_info=False)
            return []
        except Exception as e:
            log.error(f"[AnimeFire] Erro inesperado ao buscar fontes de vídeo ({episode_page_url}): {e}", exc_info=True)
            return []
        finally:
            _unset_ipv4()