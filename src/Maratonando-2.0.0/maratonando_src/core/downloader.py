# /home/marcos/Maratonando/maratonando_src/core/downloader.py
import subprocess
import shutil
import os
import logging # Use logging instead of click
from pathlib import Path

def download_episode(video_url: str, output_path: str = None, filename: str = None):
    """
    Baixa um episódio usando yt-dlp.

    Args:
        video_url: A URL direta do vídeo a ser baixado.
        output_path: O diretório onde salvar o vídeo. Padrão: Diretório 'Downloads' do usuário.
        filename: O nome do arquivo (sem extensão). Padrão: Título do vídeo obtido pelo yt-dlp.
    """
    log = logging.getLogger(__name__) # Get logger
    ytdlp_executable = "yt-dlp"

    # Verifica se o yt-dlp está disponível
    if not shutil.which(ytdlp_executable):
        log.error(f"'{ytdlp_executable}' não encontrado. Instale-o para baixar vídeos.")
        # Consider raising an exception instead of returning False for better error handling upstream
        return False

    # Define o diretório de saída padrão se não for fornecido
    if output_path is None:
        try:
            output_path = str(Path.home() / "Downloads")
            os.makedirs(output_path, exist_ok=True)
        except Exception as e:
            log.warning(f"Não foi possível determinar o diretório de Downloads ({e}). Salvando no diretório atual.")
            output_path = "." # Fallback to current directory

    # Monta o comando para o yt-dlp
    command = [
        ytdlp_executable,
        "--no-playlist",
        "--merge-output-format", "mp4",
        "-o",
    ]

    # Constrói o template de saída completo (caminho + nome)
    if filename:
        output_template = os.path.join(output_path, f"{filename}.%(ext)s")
    else:
        output_template = os.path.join(output_path, "%(title)s.%(ext)s")
    command.append(output_template)

    command.append(video_url)

    log.info(f"Executando download: {' '.join(command)}")

    try:
        # Executa o comando yt-dlp
        # check=True fará o Python levantar um erro (CalledProcessError) se yt-dlp retornar um código de erro
        # capture_output=True pega a saída padrão e erro (útil para depuração)
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        log.info("Download concluído com sucesso!")
        # Tenta mostrar o caminho final (substituindo placeholders do template)
        final_path_guess = output_template.replace('%(title)s', 'VIDEO').replace('%(ext)s', 'mp4')
        log.info(f"Salvo em diretório: {output_path} (nome exato depende do título/extensão)")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"Erro durante o download com yt-dlp:")
        log.error(f"Comando: {' '.join(e.cmd)}")
        log.error(f"Código de saída: {e.returncode}")
        log.error(f"Erro (stderr):\n{e.stderr}")
        return False
    except FileNotFoundError:
         log.critical(f"'{ytdlp_executable}' não encontrado durante a execução.")
         return False
    except Exception as e:
        log.error(f"Ocorreu um erro inesperado ao tentar baixar o vídeo: {e}", exc_info=True)
        return False

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
