import subprocess
import shutil
# import click # Replaced by logging
import sys
from typing import Optional
import logging # Import logging

# Configure logger for this module
log = logging.getLogger(__name__)

def play_video(video_url: str, title: str = "Maratonando", referer: Optional[str] = None):
    """
    Tenta reproduzir a URL de vídeo fornecida usando um player externo (mpv por padrão).
    Não envia cabeçalhos HTTP customizados, imitando o comportamento do goanime.
    Adiciona opções de cache/buffer mais agressivas para tentar reduzir travamentos.
    """ # --- VOLTANDO PARA MPV (COM ARGUMENTOS CORRETOS) ---
    player_executable = "mpv" # --- VOLTANDO PARA MPV ---
    # TODO: Consider making player_executable configurable (e.g., via config file/env var)

    # Verifica se o player está disponível no sistema
    if not shutil.which(player_executable):
        # Use logging for errors
        log.error(f"Player '{player_executable}' não encontrado no seu sistema.")
        log.error("Por favor, instale-o (ex: 'sudo pacman -S mpv' ou 'sudo apt install mpv') ou configure um player diferente.")
        raise FileNotFoundError(f"Player '{player_executable}' não encontrado.") # Levanta erro para GUI tratar
        return # Keep return for now to match original behavior

    # --- Argumentos para MPV (com yt-dlp) ---
    # Definir User-Agent (o mesmo usado nas requisições)
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    # Definir Referer (URL base do site)
    referer_url = "https://animefire.plus/" # Definir diretamente ou importar

    command = [
        player_executable,
        f"--title={title}", # Argumento CORRETO do mpv para título
        "--no-terminal",
        "--quiet", # Podemos voltar a deixar quieto, pois não esperamos erros do yt-dlp
        # Remover opções do yt-dlp, pois mpv receberá a URL direta do blogger
        # "--ytdl-raw-options-append=header=User-Agent:" + user_agent,
        # "--ytdl-raw-options-append=header=Referer:" + referer_url,
    ]
    command.append(video_url) # URL do vídeo por último

    # Use logging for execution info
    log.info(f"Executando: {' '.join(command)}")

    try:
        # Usamos start_new_session=True para tentar desvincular o processo do player do terminal,
        # embora o comportamento exato possa variar. check=False para não dar erro se fechar.
        # Consider using Popen for more control if needed in the future, but run is simpler here.
        # Remover redirecionamento para ver output do mpv/yt-dlp
        process = subprocess.run(command, check=False, start_new_session=True)

        # Log potential immediate errors from subprocess.run itself (though less likely with check=False)
        if process.returncode != 0:
             log.warning(f"Player '{player_executable}' exited with code {process.returncode}. (This might be normal if the window was closed manually)")

    # CalledProcessError should not happen with check=False
    # except subprocess.CalledProcessError as e:
    #     log.error(f"Erro ao executar o player: {e}", exc_info=True)
    except FileNotFoundError:
        # This case should be caught by shutil.which, but added for extra safety
        log.error(f"Erro Crítico: Executável do player '{player_executable}' não encontrado durante a execução.", exc_info=True)
    except Exception as e:
        log.error(f"Ocorreu um erro inesperado ao tentar tocar o vídeo: {e}", exc_info=True)
