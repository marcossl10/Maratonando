# /home/marcos/Maratonando/maratonando_src/core/downloader.py
import subprocess
import click
import shutil
import os
from pathlib import Path

def download_episode(video_url: str, output_path: str = None, filename: str = None):
    """
    Baixa um episódio usando yt-dlp.

    Args:
        video_url: A URL direta do vídeo a ser baixado.
        output_path: O diretório onde salvar o vídeo. Padrão: Diretório 'Downloads' do usuário.
        filename: O nome do arquivo (sem extensão). Padrão: Título do vídeo obtido pelo yt-dlp.
    """
    ytdlp_executable = "yt-dlp"

    # Verifica se o yt-dlp está disponível
    if not shutil.which(ytdlp_executable):
        click.echo(f"Erro: '{ytdlp_executable}' não encontrado. Instale-o para baixar vídeos.", err=True)
        # Poderia levantar uma exceção ou retornar um status de falha
        return False

    # Define o diretório de saída padrão se não for fornecido
    if output_path is None:
        try:
            # Tenta encontrar o diretório de Downloads padrão do usuário
            output_path = str(Path.home() / "Downloads")
            os.makedirs(output_path, exist_ok=True) # Cria o diretório se não existir
        except Exception as e:
            click.echo(f"Aviso: Não foi possível determinar o diretório de Downloads ({e}). Salvando no diretório atual.", err=True)
            output_path = "." # Salva no diretório atual como fallback

    # Monta o comando para o yt-dlp
    command = [
        ytdlp_executable,
        "--no-playlist",         # Garante que baixe apenas um vídeo, não uma playlist inteira
        "--merge-output-format", "mp4", # Tenta mesclar em mp4 se houver formatos de áudio/vídeo separados
        "-o",                    # Define o template do nome do arquivo de saída
    ]

    # Constrói o template de saída completo (caminho + nome)
    if filename:
        # Usa o nome de arquivo fornecido, adicionando a extensão automaticamente pelo yt-dlp
        output_template = os.path.join(output_path, f"{filename}.%(ext)s")
    else:
        # Usa o título do vídeo como nome de arquivo (padrão do yt-dlp)
        output_template = os.path.join(output_path, "%(title)s.%(ext)s")
    command.append(output_template)

    # Adiciona a URL do vídeo ao comando
    command.append(video_url)

    click.echo(f"Executando download: {' '.join(command)}")

    try:
        # Executa o comando yt-dlp
        # check=True fará o Python levantar um erro (CalledProcessError) se yt-dlp retornar um código de erro
        # capture_output=True pega a saída padrão e erro (útil para depuração)
        # text=True decodifica a saída como texto
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        click.echo("Download concluído com sucesso!")
        # Tenta mostrar o caminho final (substituindo placeholders do template)
        final_path_guess = output_template.replace('%(title)s', 'VIDEO').replace('%(ext)s', 'mp4')
        click.echo(f"Salvo em diretório: {output_path} (nome exato depende do título/extensão)")
        return True # Indica sucesso
    except subprocess.CalledProcessError as e:
        # Erro específico do processo yt-dlp
        click.echo(f"Erro durante o download com yt-dlp:", err=True)
        click.echo(f"Comando: {' '.join(e.cmd)}", err=True)
        click.echo(f"Código de saída: {e.returncode}", err=True)
        # Mostra a saída de erro do yt-dlp, que geralmente contém informações úteis
        click.echo(f"Erro (stderr):\n{e.stderr}", err=True)
        return False # Indica falha
    except FileNotFoundError:
        # Caso raro onde yt-dlp desaparece entre shutil.which e subprocess.run
         click.echo(f"Erro Crítico: '{ytdlp_executable}' não encontrado durante a execução.", err=True)
         return False
    except Exception as e:
        # Outros erros inesperados
        click.echo(f"Ocorreu um erro inesperado ao tentar baixar o vídeo: {e}", err=True)
        return False # Indica falha

# Você pode adicionar um bloco if __name__ == '__main__': aqui para testar a função diretamente
# Exemplo:
# if __name__ == '__main__':
#     test_url = "COLOQUE_UMA_URL_DE_VIDEO_VALIDA_AQUI"
#     if test_url != "COLOQUE_UMA_URL_DE_VIDEO_VALIDA_AQUI":
#         print("Iniciando teste de download...")
#         success = download_episode(test_url, filename="teste_maratonando")
#         if success:
#             print("Teste de download bem-sucedido.")
#         else:
#             print("Teste de download falhou.")
#     else:
#         print("Edite o arquivo downloader.py e adicione uma URL de teste válida.")
