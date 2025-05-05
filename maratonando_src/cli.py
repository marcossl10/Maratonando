# /home/marcos/Maratonando/maratonando/cli.py
import click

# Importar futuras funções de busca, etc.
from .core.searcher import perform_search
# Importa o PACOTE de parsers
from .core import parsers
# Importa a URL base especificamente para o referer (Não mais usada para o player, mas pode ser útil)
# from .core.parsers.animefire_parser import BASE_URL as ANIMEFIRE_BASE_URL
# Importar a função de tocar vídeo
from .core.player import play_video
import traceback # Para imprimir traceback em erros

# Mapeamento de nome da fonte para o módulo do parser
PARSER_MAP = {
    'AnimeFire': parsers.animefire_parser,  # Acessa via pacote
    # 'Pobreflix': parsers.pobreflix_parser, # Removido ou comentado
    'MinhaSerie': parsers.minhaserie_parser, # Adicionado
    # Adicionar outros parsers aqui
}

@click.group()
def cli():
    """
    Maratonando: Encontre e assista animes, filmes e séries via terminal.
    """
    pass

@cli.command()
@click.argument('query', type=str)
def buscar(query):
    """Busca por animes, filmes ou séries."""
    click.echo(f"Buscando por: {query}...")
    results = perform_search(query)

    if not results:
        click.echo("Nenhum resultado encontrado.")
    else:
        click.echo("Resultados encontrados:")
        # Exibe os resultados numerados, indicando a fonte
        for i, result in enumerate(results):
            source_name = result.get('source', 'Desconhecida')
            click.echo(f" {i+1}. {result.get('title', '???')} [{source_name}] ({result.get('url', '???')})")

        # --- Início do Bloco de Seleção ---
        try:
            choice = click.prompt('Digite o número do item que deseja selecionar', type=int)
            if 1 <= choice <= len(results):
                selected_item = results[choice - 1] # Ajusta para índice 0-based
                click.echo("-" * 20) # Linha separadora
                click.echo(f"Você selecionou: {selected_item.get('title')}")
                click.echo(f"URL: {selected_item.get('url')}")

                # Determina qual parser usar baseado na fonte guardada no resultado
                source_name = selected_item.get('source')
                parser_module = PARSER_MAP.get(source_name)

                if not parser_module:
                    click.echo(f"  [CLI] Parser para a fonte '{source_name}' não encontrado no PARSER_MAP.", err=True)
                    return # Sai se não encontrar o parser no mapeamento

                # Verifica se as funções necessárias existem no parser
                if not hasattr(parser_module, 'fetch_details') or not hasattr(parser_module, 'get_video_sources'): # Nome da função mudou
                     click.echo(f"  [CLI] Parser '{source_name}' não implementa 'fetch_details' ou 'get_video_sources'.", err=True)
                     return

                # Chama as funções do parser correto
                item_details = parser_module.fetch_details(selected_item['url'])

                # Processa os detalhes encontrados
                if item_details:
                    item_type = item_details.get('type', 'unknown') # Pega o tipo (series, movie, unknown)

                    # --- Lógica para Séries ---
                    # Ajustado para checar 'seasons' ou 'episodes' dependendo do parser
                    if item_type == 'series' or 'episodes' in item_details:
                        # TODO: Refinar a lógica de seleção de temporada/episódio quando implementado no parser MinhaSerie
                        if 'episodes' in item_details and item_details['episodes']: # Lógica atual para AnimeFire
                            click.echo("Episódios encontrados:")
                            episodes = item_details['episodes']
                            for i, episode in enumerate(episodes):
                                # Adapta a exibição se 'number_str' não existir (AnimeFire)
                                num_str = f" ({episode.get('number_str')})" if episode.get('number_str') else ""
                                click.echo(f"  {i+1}. {episode.get('title', '???')}{num_str}")

                            # Seleção de episódio
                            ep_choice = click.prompt('Digite o número do episódio que deseja assistir', type=int)
                            if 1 <= ep_choice <= len(episodes):
                                selected_episode = episodes[ep_choice - 1]
                                click.echo(f"Selecionado: {selected_episode.get('title')}")
                                click.echo(f"URL do episódio/vídeo: {selected_episode.get('url')}")

                                episode_page_url = selected_episode['url'] # Mantém para get_video_sources

                                # Obtém as fontes de vídeo a partir da URL do episódio
                                video_sources = parser_module.get_video_sources(episode_page_url) # Passa a URL original, recebe lista

                                if video_sources:
                                    final_video_url = None
                                    selected_label = "???"

                                    if len(video_sources) == 1:
                                        # Se só tem uma fonte, usa ela direto
                                        final_video_url = video_sources[0]['src']
                                        selected_label = video_sources[0]['label']
                                        click.echo(f"  [CLI] Encontrada única fonte de vídeo ({selected_label}).")
                                    else:
                                        # Se tem múltiplas fontes, pergunta ao usuário
                                        click.echo("Qualidades disponíveis:")
                                        quality_options = {str(i+1): source for i, source in enumerate(video_sources)}
                                        for i, source in enumerate(video_sources):
                                            click.echo(f"  {i+1}. {source['label']}")

                                        q_choice_str = click.prompt('Digite o número da qualidade desejada', type=click.Choice(quality_options.keys()))
                                        selected_source = quality_options[q_choice_str]
                                        final_video_url = selected_source['src']
                                        selected_label = selected_source['label']

                                    click.echo(f"URL final do vídeo para tocar ({selected_label}): {final_video_url}")
                                    ep_title = selected_episode.get('title', 'Episódio')
                                    play_video(
                                        final_video_url,
                                        title=f"{selected_item.get('title')} - {ep_title}",
                                        referer=None # Não passamos mais referer para o mpv
                                    )
                                else:
                                    click.echo("  [CLI] Não foi possível obter fontes de vídeo para o episódio.", err=True)
                            else:
                                click.echo("Número de episódio inválido.", err=True)
                        elif item_type == 'series': # Caso MinhaSerie retorne 'series' mas episódios não implementados
                             click.echo("  [CLI] Parser para séries deste site ainda não implementado completamente (seleção de episódio).", err=True)
                        else:
                             click.echo("  [CLI] Detalhes de série inválidos ou incompletos.", err=True)

                    # --- Lógica para Filmes (ou item sem episódios/temporadas) ---
                    elif item_type == 'movie' or item_type == 'unknown':
                        click.echo("  [CLI] Item detectado como Filme ou tipo desconhecido.")
                        # Para filmes, a URL do conteúdo geralmente é a própria URL do item
                        # ou uma URL específica retornada em fetch_details
                        content_url_for_movie = item_details.get('content_url', selected_item['url'])

                        video_sources = parser_module.get_video_sources(content_url_for_movie)

                        if video_sources:
                            final_video_url = None
                            selected_label = "???"

                            if len(video_sources) == 1:
                                final_video_url = video_sources[0]['src']
                                selected_label = video_sources[0]['label']
                                click.echo(f"  [CLI] Encontrada única fonte de vídeo ({selected_label}).")
                            else:
                                click.echo("Qualidades/Fontes disponíveis:")
                                quality_options = {str(i+1): source for i, source in enumerate(video_sources)}
                                for i, source in enumerate(video_sources):
                                    click.echo(f"  {i+1}. {source['label']}")
                                q_choice_str = click.prompt('Digite o número da qualidade/fonte desejada', type=click.Choice(quality_options.keys()))
                                selected_source = quality_options[q_choice_str]
                                final_video_url = selected_source['src']
                                selected_label = selected_source['label']

                            click.echo(f"URL final do vídeo para tocar ({selected_label}): {final_video_url}")
                            play_video(
                                final_video_url,
                                title=selected_item.get('title', 'Filme'),
                                referer=None
                            )
                        else:
                            click.echo("  [CLI] Não foi possível obter fontes de vídeo para este item.", err=True)
                    else:
                        # Caso inesperado
                        click.echo(f"  [CLI] Tipo de item desconhecido ou detalhes inválidos: {item_type}", err=True)
                else:
                    click.echo("Não foi possível buscar detalhes para este item.")

            else:
                click.echo("Número inválido.", err=True)
        except click.exceptions.Abort:
            click.echo("\nSeleção cancelada.")
        except ValueError: # Captura se a entrada não for um número inteiro
            click.echo("Entrada inválida. Por favor, digite um número.", err=True)
        except Exception as e: # Captura outros erros inesperados
             click.echo(f"Ocorreu um erro inesperado: {e}", err=True)
             traceback.print_exc() # Imprime o traceback completo para debug
        # --- Fim do Bloco de Seleção ---
