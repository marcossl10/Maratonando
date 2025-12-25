# /home/marcos/Maratonando/maratonando_src/core/searcher.py
from typing import List, Dict, Any
import logging
# Importa as classes de parser diretamente
from .parsers import AnimeFireParser, MinhaSerieParser # Importe aqui todos os seus parsers

log = logging.getLogger(__name__)


# Lista de parsers a serem usados
# Adicione instâncias de todos os seus parsers aqui.
# O nome é usado para identificação nos logs e potencialmente na UI.
# A chave 'instance' deve conter uma instância da classe do parser.
parsers_list: List[Dict[str, Any]] = [
    {'name': 'AnimeFire', 'instance': AnimeFireParser()},
    # {'name': 'MinhaSerie', 'instance': MinhaSerieParser()},
    # Se você adicionar um novo parser (ex: MeuNovoParser em meu_novo_parser.py),
    # importe-o acima e adicione-o aqui:
    # {'name': 'MeuNovoParser', 'instance': MeuNovoParser()},
]

def perform_search(query: str) -> List[Dict[str, str]]:
    """
    Orquestra a busca pela query em diferentes fontes/parsers.
    Retorna uma lista de dicionários, cada um contendo 'title', 'url' e 'source'.
    """
    log.info(f"Iniciando busca por '{query}' nas fontes configuradas...")
    all_results: List[Dict[str, str]] = [] # Adicionar type hint para clareza

    for parser_config in parsers_list:
        parser_instance = parser_config['instance']
        parser_name = parser_config['name']
        try:
            # A verificação hasattr(parser_instance, 'search') é implícita,
            # pois chamaremos o método diretamente. Se não existir, um AttributeError será levantado.
            log.info(f"Preparando para buscar em {parser_name}...")
            current_results = parser_instance.search(query) # Chama o método search da instância

            # Adiciona informação da fonte a cada resultado
            if current_results: # Garante que current_results não é None
                for result in current_results:
                    if 'source' not in result: # Adiciona o nome do parser como a fonte
                        result['source'] = parser_name
                all_results.extend(current_results)
                log.debug(f"Recebidos {len(current_results)} resultados de {parser_name}.")
            else:
                log.warning(f"Parser {parser_name} retornou None ou uma lista vazia.")
                log.debug(f"Recebidos 0 resultados de {parser_name}.")

        except AttributeError:
            # Este erro ocorrerá se o parser_instance não tiver um método 'search'
            log.warning(f"Parser {parser_name} não possui um método 'search'. Pulando.")
        except Exception as e:
            log.error(f"Erro ao executar parser {parser_name}: {e}", exc_info=True)


    log.info(f"Busca concluída. Encontrados {len(all_results)} resultados no total.")

    # TODO: Implementar lógica para ordenar ou remover duplicatas aqui, se necessário.
    # Exemplo simples de remoção de duplicatas baseado na URL (mantendo a primeira ocorrência):
    # unique_results = []
    # seen_urls = set()
    # for result in all_results:
    #     if result.get('url') not in seen_urls:
    #         unique_results.append(result)
    #         seen_urls.add(result.get('url'))
    # return unique_results

    return all_results
