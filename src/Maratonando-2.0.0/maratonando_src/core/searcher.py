from typing import List, Dict
from . import parsers
import logging

log = logging.getLogger(__name__)

def perform_search(query: str) -> List[Dict[str, str]]:
    """
    Orquestra a busca pela query em diferentes fontes/parsers.
    Retorna uma lista de dicionários, cada um contendo 'title', 'url' e 'source'.
    """
    log.info(f"Iniciando busca por '{query}' nas fontes configuradas...")
    all_results: List[Dict[str, str]] = [] # Adicionar type hint para clareza


    # Lista de parsers a serem usados
    # Considerar carregar dinamicamente ou configurar externamente no futuro
    parsers_list = [
        {'name': 'AnimeFire', 'module': parsers.animefire_parser},
        # {'name': 'Pobreflix', 'module': parsers.pobreflix_parser}, # Removido ou comentado
        {'name': 'MinhaSerie', 'module': parsers.minhaserie_parser},
        # Adicionar outros parsers aqui no futuro
    ]

    for parser_config in parsers_list:
        parser_name = parser_config['name']
        parser_module = parser_config['module']
        try:
            # Verifica se o módulo e a função search existem
            if parser_module and hasattr(parser_module, 'search'):
                log.info(f"Preparando para buscar em {parser_name}...")
                current_results = parser_module.search(query)
                # Adiciona informação da fonte a cada resultado
                for result in current_results:
                    if 'source' not in result:
                        result['source'] = parser_name
                if current_results is not None:
                    all_results.extend(current_results)
                else:
                    log.warning(f"Parser {parser_name} retornou None em vez de uma lista.")
                log.debug(f"Recebidos {len(current_results if current_results is not None else [])} resultados de {parser_name}.")
            else:
                log.warning(f"Parser {parser_name} não possui função 'search' ou módulo não encontrado.")
        except Exception as e:
            log.error(f"Erro ao executar parser {parser_name}: {e}", exc_info=True)


    log.info(f"Busca concluída. Encontrados {len(all_results)} resultados no total.")

    # TODO: Implementar lógica para ordenar ou remover duplicatas aqui
    # Exemplo simples de remoção de duplicatas baseado na URL:
    # unique_results = []
    # seen_urls = set()
    # for result in all_results:
    #     if result.get('url') not in seen_urls:
    #         unique_results.append(result)
    #         seen_urls.add(result.get('url'))
    # return unique_results

    return all_results
