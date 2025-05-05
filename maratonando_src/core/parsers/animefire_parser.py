# /home/marcos/Maratonando/maratonando_src/core/parsers/animefire_parser.py
import requests # Voltar a usar requests
# import cloudscraper # Remover cloudscraper
from bs4 import BeautifulSoup
from typing import List, Dict # Optional não é mais usado aqui
import re
import json
from urllib.parse import urljoin, quote, urlparse # Adicionar urlparse
import logging
import sys # Importar sys para usar sys.stderr nos prints de debug
import socket # Importar socket
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.connection import HAS_IPV6


# Configuração básica de logging (deve ser configurado no ponto de entrada principal)
# logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
# # --- PRINT DE TESTE DE IMPORTAÇÃO ---
# print("--- DEBUG: Importando animefire_parser.py ---", file=sys.stderr)
# Log de importação (executa quando o módulo é carregado)
logging.getLogger(__name__).info("[AnimeFire Parser] Módulo importado com sucesso.")

log = logging.getLogger(__name__) # Usar um logger específico para o módulo

# URL base do AnimeFire.plus
BASE_URL = "https://animefire.plus/"
# URL de busca - Voltando para /pesquisar/
SEARCH_URL_TEMPLATE = BASE_URL + "pesquisar/{query}"

# Não precisamos mais da instância do scraper
# scraper = cloudscraper.create_scraper()

# --- Forçar IPv4 ---
# Código adaptado para forçar IPv4 nas conexões do requests

orig_allowed_gai_family = None

def set_ipv4():
    """Força a resolução de nomes para IPv4."""
    global orig_allowed_gai_family
    if HAS_IPV6:
        orig_allowed_gai_family = socket.getaddrinfo.__defaults__[0]
        socket.getaddrinfo.__defaults__ = (socket.AF_INET,) + socket.getaddrinfo.__defaults__[1:]

def unset_ipv4():
    """Restaura a configuração original de resolução de nomes."""
    if HAS_IPV6 and orig_allowed_gai_family is not None:
        socket.getaddrinfo.__defaults__ = (orig_allowed_gai_family,) + socket.getaddrinfo.__defaults__[1:]

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': BASE_URL,
}

def search(query: str) -> List[Dict[str, str]]:
    """
    Busca por animes no AnimeFire.plus usando o parâmetro de consulta ?s=.
    Retorna uma lista de dicionários, cada um contendo 'title' e 'url'.
    """
    # # --- PRINT DE TESTE DE CHAMADA DE FUNÇÃO ---
    # print(f"--- DEBUG: Função search chamada com query: '{query}' ---", file=sys.stderr)
    log.info(f"[AnimeFire] Função search iniciada para query: '{query}'") # Log movido para o início
    # Formatar query substituindo espaços por hífens, como no goanime
    formatted_query = query.replace(' ', '-')
    # Usar o template /pesquisar/
    search_query_url = SEARCH_URL_TEMPLATE.format(query=formatted_query)
    results = []
    processed_urls = set()

    set_ipv4() # Força IPv4 antes da requisição
    try:
        # # --- PRINT ANTES DA REQUISIÇÃO ---
        # print(f"--- DEBUG: Tentando requests.get para: {search_query_url} ---", file=sys.stderr)
        # Usar requests.get
        # Usar uma sessão pode ser mais robusto, mas vamos manter requests.get por enquanto
        response = requests.get(search_query_url, headers=HTTP_HEADERS, timeout=20) # Aumentar timeout um pouco
        # print(f"--- DEBUG: Status Code recebido: {response.status_code} ---", file=sys.stderr) # Log do status
        response.raise_for_status()
        # print(f"--- DEBUG: Após raise_for_status ---", file=sys.stderr) # DEBUG POINT 1

        # Parse the HTML
        # print(f"--- DEBUG: Antes de BeautifulSoup ---", file=sys.stderr) # DEBUG POINT 2
        soup = BeautifulSoup(response.text, 'html.parser')
        # print(f"--- DEBUG: Após BeautifulSoup ---", file=sys.stderr) # DEBUG POINT 3


        # Encontrar resultados da busca na página ?s=
        # Os resultados estão em 'div' com a classe 'divCardUltimosEps'
        # print(f"--- DEBUG: Antes de soup.find_all ---", file=sys.stderr) # DEBUG POINT 4
        result_items = soup.find_all('div', class_='divCardUltimosEps')
        # print(f"--- DEBUG: Após soup.find_all (encontrados: {len(result_items)}) ---", file=sys.stderr) # DEBUG POINT 5

        if not result_items:
             log.warning("[AnimeFire] Nenhum item de resultado ('div.divCardUltimosEps') encontrado na página /pesquisar/.")
             # Adicionar print aqui também
             print("[AnimeFire] Nenhum item de resultado ('div.divCardUltimosEps') encontrado.", file=sys.stderr)
             return []

        log.info(f"[AnimeFire] Encontrados {len(result_items)} itens de resultado.")

        # print(f"--- DEBUG: Antes do loop FOR ---", file=sys.stderr) # DEBUG POINT 6
        for i, item_div in enumerate(result_items): # Adiciona índice para debug
            # print(f"--- DEBUG: Loop FOR - Item {i+1} ---", file=sys.stderr) # DEBUG POINT 7
            # print(f"--- DEBUG: Buscando link_tag ---", file=sys.stderr)
            link_tag = item_div.find('a', href=True)
            # print(f"--- DEBUG: link_tag encontrado: {'Sim' if link_tag else 'Não'} ---", file=sys.stderr)
            # O título está dentro de 'h3' com a classe 'animeTitle' dentro do link
            # print(f"--- DEBUG: Buscando title_tag ---", file=sys.stderr)
            title_tag = item_div.find('h3', class_='animeTitle')
            # print(f"--- DEBUG: title_tag encontrado: {'Sim' if title_tag else 'Não'} ---", file=sys.stderr)

            if link_tag and title_tag:
                # print(f"--- DEBUG: Extraindo title/url ---", file=sys.stderr)
                title = title_tag.get_text(strip=True)
                url = link_tag['href']
                absolute_url = urljoin(BASE_URL, url) # Garante URL absoluta

                # Filtra para garantir que é uma URL de anime válida e não duplicada
                if absolute_url.startswith(BASE_URL) and "/animes/" in absolute_url and absolute_url not in processed_urls: # Corrigido para /animes/
                     log.debug(f"    [AnimeFire] Item encontrado: {title} - {absolute_url}")
                     # print(f"--- DEBUG: Adicionando item aos resultados: {title} ---", file=sys.stderr)
                     results.append({'title': title, 'url': absolute_url})
                     processed_urls.add(absolute_url)
                else:
                     log.debug(f"    [AnimeFire] Item ignorado (URL inválida ou duplicada): {title} - {absolute_url}")
                     # print(f"--- DEBUG: Item ignorado (filtro URL): {title} ---", file=sys.stderr)
            else:
                 log.debug(f"    [AnimeFire] Item ignorado (link ou título faltando).")
                 # print(f"--- DEBUG: Item ignorado (tags faltando) ---", file=sys.stderr)

    # Ajustar tratamento de exceção para requests
    except Exception as e:
        # --- PRINT E LOG GENÉRICO DE ERRO ---
        print(f"--- DEBUG: ERRO na função search: {e} ---", file=sys.stderr)
        log.error(f"[AnimeFire] ERRO na função search: {e}", exc_info=True) # Log other errors with traceback
        return [] # Explicitly return empty list on other errors
    finally:
        # # --- PRINT NO FINALLY ---
        # print(f"--- DEBUG: Bloco finally da função search executado ---", file=sys.stderr)
        unset_ipv4() # Restaura configuração de IP no finally
        # This will always run, confirming the function was executed
        log.debug(f"[AnimeFire] Função search finalizada para query '{query}'. Retornando {len(results)} resultados.")
    return results

def fetch_details(anime_url: str) -> Dict:
    """Busca detalhes e lista de episódios de um anime."""
    log.info(f"[AnimeFire] Buscando detalhes de: {anime_url}")
    details = {'episodes': [], 'type': 'series'} # Assume series por padrão

    set_ipv4() # Força IPv4
    try:
        # Usar requests.get
        # print(f"--- DEBUG: Tentando requests.get (IPv4) para detalhes: {anime_url} ---", file=sys.stderr)
        response = requests.get(anime_url, headers=HTTP_HEADERS, timeout=20) # Aumentar timeout
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extrair título
        title_tag = soup.find('h1', class_='aniTitulo')
        if title_tag:
            details['title'] = title_tag.text.strip()
            log.debug(f"    [AnimeFire] Título encontrado: {details['title']}")

        # Extrair sinopse
        synopsis_tag = soup.find('div', class_='aniSinopse')
        if synopsis_tag:
            details['synopsis'] = synopsis_tag.text.strip()
            log.debug(f"    [AnimeFire] Sinopse encontrada.")

        # Encontrar links dos episódios (usando o seletor que funcionava antes)
        episode_links = soup.find_all('a', class_='lEp epT divNumEp smallbox px-2 mx-1 text-left d-flex')

        if episode_links:
            log.info(f"[AnimeFire] Encontrados {len(episode_links)} links de episódios.")
            raw_episodes = []
            for link_tag in episode_links:
                ep_page_url = urljoin(BASE_URL, link_tag['href']) # Garante URL absoluta
                ep_title_text = link_tag.get_text(strip=True)

                num_match = re.search(r'\d+', ep_title_text)
                ep_num = int(num_match.group(0)) if num_match else 9999

                raw_episodes.append({
                    'num': ep_num,
                    'title': ep_title_text,
                    'url': ep_page_url
                })

            raw_episodes.sort(key=lambda x: x['num'])
            details['episodes'] = [{'title': ep['title'], 'url': ep['url']} for ep in raw_episodes]
        else:
             log.warning("[AnimeFire] Nenhum link de episódio ('a.lEp...') encontrado.")

    except requests.exceptions.RequestException as e: # Captura erros de requests
        log.error(f"[AnimeFire] Erro de rede ao buscar detalhes ({anime_url}): {e}", exc_info=False)
    except Exception as e:
        log.error(f"[AnimeFire] Erro inesperado ao buscar detalhes ({anime_url}): {e}", exc_info=True)
    finally:
        unset_ipv4() # Restaura configuração de IP

    return details


def get_video_sources(episode_page_url: str) -> List[Dict[str, str]]:
    """
    Obtém a URL da fonte de vídeo da página do episódio, priorizando o src do iframe.
    """
    log.info(f"[AnimeFire] Buscando fontes de vídeo em: {episode_page_url}")
    set_ipv4() # Força IPv4
    try:
        # Usar requests.get
        # print(f"--- DEBUG: Tentando requests.get (IPv4) para fontes de vídeo: {episode_page_url} ---", file=sys.stderr)
        response = requests.get(episode_page_url, headers=HTTP_HEADERS, timeout=20) # Aumentar timeout
        # print(f"--- DEBUG: Fontes de vídeo - Status Code: {response.status_code} ---", file=sys.stderr) # DEBUG POINT A
        response.raise_for_status()
        # print(f"--- DEBUG: Fontes de vídeo - Após raise_for_status ---", file=sys.stderr) # DEBUG POINT B
        # print(f"--- DEBUG: Fontes de vídeo - Antes de BeautifulSoup ---", file=sys.stderr) # DEBUG POINT C
        soup = BeautifulSoup(response.text, "html.parser")

        # --- Estratégia 1: Tentar método goanime (tag <video> com data-video-src) ---
        video_tag = soup.find('video', attrs={'data-video-src': True})
        if video_tag:
            intermediate_url = video_tag.get('data-video-src')
            if intermediate_url:
                absolute_intermediate_url = urljoin(episode_page_url, intermediate_url)
                log.info(f"[AnimeFire] Encontrada URL intermediária em data-video-src: {absolute_intermediate_url}")
                try:
                    # Faz a requisição para a URL intermediária
                    video_data_response = requests.get(absolute_intermediate_url, headers=HTTP_HEADERS, timeout=15)
                    video_data_response.raise_for_status()
                    video_data = video_data_response.json() # Assume que a resposta é JSON

                    sources = []
                    if video_data and 'data' in video_data and isinstance(video_data['data'], list):
                        for item in video_data['data']:
                            if item.get('src') and item.get('label'):
                                sources.append({'label': item['label'], 'src': item['src']})
                                log.debug(f"  [AnimeFire] Qualidade encontrada: {item['label']} -> {item['src']}")
                        if sources:
                            log.info(f"[AnimeFire] Extraídas {len(sources)} fontes diretas da URL intermediária.")
                            return sources # Retorna as fontes diretas (.mp4, etc.)
                        else:
                            log.warning("[AnimeFire] Resposta da URL intermediária não continha fontes válidas.")
                    else:
                        log.warning("[AnimeFire] Formato inesperado da resposta da URL intermediária.")
                except Exception as e:
                    log.error(f"[AnimeFire] Erro ao processar URL intermediária ({absolute_intermediate_url}): {e}", exc_info=True)
            else:
                log.warning("[AnimeFire] Tag <video> encontrada, mas sem atributo 'data-video-src'.")

        # --- Estratégia 2 (Fallback): Tentar método iframe (Blogger) ---
        log.info("[AnimeFire] Estratégia <video> falhou ou não aplicável. Tentando fallback para <iframe>.")
        # --- Método Melhorado: Buscar iframe dentro do div#div_video ---
        video_div = soup.find("div", id="div_video")
        iframe = None
        if video_div:
            iframe = video_div.find("iframe")
            log.debug("[AnimeFire] Encontrado div#div_video, procurando iframe dentro.")
        else:
            log.warning("[AnimeFire] div#div_video não encontrado, tentando busca global por iframe.")
            # Fallback: Tenta encontrar iframe globalmente se div não existe
            iframe = soup.find("iframe", src=re.compile(r"video|blogger", re.IGNORECASE)) # Busca video OU blogger

        if iframe and iframe.get("src"):
            # print(f"--- DEBUG: Fontes de vídeo - Iframe encontrado ---", file=sys.stderr) # DEBUG POINT D
            iframe_src = iframe["src"]
            # Garante que a URL seja absoluta
            absolute_iframe_src = urljoin(episode_page_url, iframe_src) # Usa a URL da página como base
            log.info(f"[AnimeFire] Encontrada URL de vídeo no src do iframe (fallback): {absolute_iframe_src}")
            # Retorna no formato esperado (lista de dicionários)
            # print(f"--- DEBUG: Fontes de vídeo - Retornando URL do iframe ---", file=sys.stderr) # DEBUG POINT E
            return [{"label": "iframe", "src": absolute_iframe_src}]
        else:
            # print(f"--- DEBUG: Fontes de vídeo - Iframe NÃO encontrado ---", file=sys.stderr) # DEBUG POINT F
            log.warning("[AnimeFire] Nenhum iframe válido encontrado na página (fallback).")


        return []

    except requests.exceptions.RequestException as e: # Captura erros de requests
        log.error(f"[AnimeFire] Erro de rede ao buscar fontes de vídeo ({episode_page_url}): {e}", exc_info=False)
        # print(f"--- DEBUG: Fontes de vídeo - Erro de rede: {e} ---", file=sys.stderr) # DEBUG POINT G
        return []
    except Exception as e:
        log.error(f"[AnimeFire] Erro inesperado ao buscar fontes de vídeo ({episode_page_url}): {e}", exc_info=True)
        # print(f"--- DEBUG: Fontes de vídeo - Erro inesperado: {e} ---", file=sys.stderr) # DEBUG POINT H
    finally:
        # print(f"--- DEBUG: Fontes de vídeo - Bloco finally executado ---", file=sys.stderr) # DEBUG POINT I
        unset_ipv4() # Restaura configuração de IP
        # REMOVER este return [] do finally! Ele sobrescreve o retorno do try.

# Remover fetch_popular_animes se não estiver sendo usado
# def fetch_popular_animes() -> List[Dict[str, str]]: ...
