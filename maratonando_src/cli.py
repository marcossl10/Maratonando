# /home/marcos/Maratonando/maratonando_src/cli.py
import click

from .core.searcher import perform_search
from .core import parsers
# Importa a classe ExternalMediaPlayer em vez da função play_video inexistente
from .core.player import ExternalMediaPlayer
import traceback

# Mapeamento de nome da fonte para instâncias das classes de parser.
# A chave DEVE corresponder ao valor do campo 'source' nos resultados de `perform_search`.
PARSER_MAP = {
    'AnimeFire': parsers.AnimeFireParser(),
    # Adicione outros parsers aqui conforme necessário.
    # Ex: 'MeuNovoParser': parsers.MeuNovoParser(),
}

# Cria uma instância do player para ser usada pela CLI
PLAYER_INSTANCE = ExternalMediaPlayer()

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
    # No seu searcher.py, a lógica de quais parsers usar já está lá,
    # então não precisamos passar active_parser_instances aqui.
    # A função perform_search já lida com a iteração dos parsers configurados nela.
    results = perform_search(query) # Simplificado: perform_search gerencia seus parsers internos

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

                # Passa o fallback_image para get_details
                item_details = parser_instance.get_details(selected_item['url'], fallback_image=selected_item.get('image', ''))


                if item_details:
                    item_type = item_details.get('type', 'unknown')

                    if item_type == 'series' or 'episodes' in item_details:
                        if 'episodes' in item_details and item_details['episodes']:
                            click.echo("Episódios encontrados:")
                            episodes = item_details['episodes']
                            for i, episode in enumerate(episodes):
                                # Tentativa de obter um número de episódio mais explícito se disponível
                                ep_num_display = episode.get('number_str') or episode.get('number') or f"Item {i+1}"
                                click.echo(f"  {i+1}. {episode.get('title', '???')} (Ep. {ep_num_display})")


                            ep_choice = click.prompt('Digite o número do episódio que deseja assistir', type=int)
                            if 1 <= ep_choice <= len(episodes):
                                selected_episode = episodes[ep_choice - 1]
                                click.echo(f"Selecionado: {selected_episode.get('title')}")
                                click.echo(f"URL do episódio/página: {selected_episode.get('url')}")

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
                                    PLAYER_INSTANCE.play_episode( # Usa o método da instância do player
                                        final_video_url,
                                        title=f"{selected_item.get('title')} - {ep_title}",
                                        referer=None # O método play_episode em player.py não usa referer atualmente
                                    )
                                else:
                                    click.echo("  [CLI] Não foi possível obter fontes de vídeo para o episódio.", err=True)
                            else:
                                click.echo("Número de episódio inválido.", err=True)
                        elif item_type == 'series': # Se for série mas não tiver 'episodes'
                             click.echo("  [CLI] Detalhes da série encontrados, mas sem lista de episódios explícita.", err=True)
                        else: # Não é série e não tem 'episodes'
                             click.echo("  [CLI] Detalhes de série inválidos ou incompletos.", err=True)

                    elif item_type == 'movie' or item_type == 'unknown': # Trata filmes ou tipos desconhecidos
                        click.echo("  [CLI] Item detectado como Filme ou tipo desconhecido.")
                        # Para filmes, a URL do item selecionado geralmente é a página para obter as fontes de vídeo
                        content_url_for_movie = selected_item['url']
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
                            PLAYER_INSTANCE.play_episode( # Usa o método da instância do player
                                final_video_url,
                                title=selected_item.get('title', 'Filme'),
                                referer=None # O método play_episode em player.py não usa referer atualmente
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
        except ValueError: # Para o prompt de número
            click.echo("Entrada inválida. Por favor, digite um número.", err=True)
        except Exception as e:
             click.echo(f"Ocorreu um erro inesperado: {e}", err=True)
             traceback.print_exc() # Mostra o traceback completo para depuração

if __name__ == '__main__':
    cli()
