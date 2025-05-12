# /home/marcos/Maratonando/maratonando_src/cli.py
import click

from .core.searcher import perform_search
from .core import parsers
from .core.player import play_video
import traceback

# Mapeamento de nome da fonte para instâncias das classes de parser.
# A chave DEVE corresponder ao valor do campo 'source' nos resultados de `perform_search`.
PARSER_MAP = {
    'AnimeFire': parsers.AnimeFireParser(),
    'AnimesOnline': parsers.AnimesOnlineParser(),
    # Adicione outros parsers aqui conforme necessário.
    # Ex: 'MeuNovoParser': parsers.MeuNovoParser(),
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

    # Cria uma lista de instâncias de parsers ativos a partir do PARSER_MAP.
    active_parser_instances = [parser_instance for parser_instance in PARSER_MAP.values() if parser_instance is not None]

    results = perform_search(query, active_parser_instances)

    if not results:
        click.echo("Nenhum resultado encontrado.")
    else:
        click.echo("Resultados encontrados:")
        for i, result in enumerate(results):
            source_name = result.get('source', 'Desconhecida')
            click.echo(f" {i+1}. {result.get('title', '???')} [{source_name}] ({result.get('url', '???')})")

        try:
            choice = click.prompt('Digite o número do item que deseja selecionar', type=int)
            if 1 <= choice <= len(results):
                selected_item = results[choice - 1]
                click.echo("-" * 20)
                click.echo(f"Você selecionou: {selected_item.get('title')}")
                click.echo(f"URL: {selected_item.get('url')}")

                source_name = selected_item.get('source')
                parser_instance = PARSER_MAP.get(source_name)

                if not parser_instance:
                    click.echo(f"  [CLI] Parser para a fonte '{source_name}' não encontrado no PARSER_MAP.", err=True)
                    return

                if not hasattr(parser_instance, 'get_details') or \
                   not hasattr(parser_instance, 'get_video_source'):
                     click.echo(f"  [CLI] Parser '{source_name}' não implementa 'get_details' ou 'get_video_source'.", err=True)
                     return

                item_details = parser_instance.get_details(selected_item['url'], fallback_image=selected_item.get('image', ''))

                if item_details:
                    item_type = item_details.get('type', 'unknown')

                    if item_type == 'series' or 'episodes' in item_details:
                        if 'episodes' in item_details and item_details['episodes']:
                            click.echo("Episódios encontrados:")
                            episodes = item_details['episodes']
                            for i, episode in enumerate(episodes):
                                num_str = f" ({episode.get('number_str')})" if episode.get('number_str') else ""
                                click.echo(f"  {i+1}. {episode.get('title', '???')}{num_str}")

                            ep_choice = click.prompt('Digite o número do episódio que deseja assistir', type=int)
                            if 1 <= ep_choice <= len(episodes):
                                selected_episode = episodes[ep_choice - 1]
                                click.echo(f"Selecionado: {selected_episode.get('title')}")
                                click.echo(f"URL do episódio/vídeo: {selected_episode.get('url')}")

                                episode_page_url = selected_episode['url']
                                video_sources = parser_instance.get_video_source(episode_page_url)

                                if video_sources:
                                    final_video_url = None
                                    selected_label = "???"

                                    if len(video_sources) == 1:
                                        final_video_url = video_sources[0]['src']
                                        selected_label = video_sources[0]['label']
                                        click.echo(f"  [CLI] Encontrada única fonte de vídeo ({selected_label}).")
                                    else:
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
                                        referer=None
                                    )
                                else:
                                    click.echo("  [CLI] Não foi possível obter fontes de vídeo para o episódio.", err=True)
                            else:
                                click.echo("Número de episódio inválido.", err=True)
                        elif item_type == 'series':
                             click.echo("  [CLI] Parser para séries deste site ainda não implementado completamente (seleção de episódio).", err=True)
                        else:
                             click.echo("  [CLI] Detalhes de série inválidos ou incompletos.", err=True)

                    elif item_type == 'movie' or item_type == 'unknown':
                        click.echo("  [CLI] Item detectado como Filme ou tipo desconhecido.")
                        content_url_for_movie = item_details.get('content_url', selected_item['url'])
                        video_sources = parser_instance.get_video_source(content_url_for_movie)

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
                        click.echo(f"  [CLI] Tipo de item desconhecido ou detalhes inválidos: {item_type}", err=True)
                else:
                    click.echo("Não foi possível buscar detalhes para este item.")

            else:
                click.echo("Número inválido.", err=True)
        except click.exceptions.Abort:
            click.echo("\nSeleção cancelada.")
        except ValueError:
            click.echo("Entrada inválida. Por favor, digite um número.", err=True)
        except Exception as e:
             click.echo(f"Ocorreu um erro inesperado: {e}", err=True)
             traceback.print_exc()
