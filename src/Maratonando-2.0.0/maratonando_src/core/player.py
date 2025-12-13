import subprocess
import shutil
import sys
from typing import Optional
import logging

log = logging.getLogger(__name__)

class ExternalMediaPlayer:
    """
    Classe para gerenciar a reprodução de vídeo usando um player externo.
    """
    def __init__(self, player_executable: str = "mpv"):
        self.player_executable = player_executable
        # TODO: Consider making player_executable configurable (e.g., via config file/env var)

    def play_episode(self, video_url: str, title: str = "Maratonando", referer: Optional[str] = None):
        """
        Tenta reproduzir a URL de vídeo fornecida.
        """
        # Verifica se o player está disponível no sistema
        if not shutil.which(self.player_executable):
            log.error(f"Player '{self.player_executable}' não encontrado no seu sistema.")
            log.error("Por favor, instale-o (ex: 'sudo pacman -S mpv' ou 'sudo apt install mpv') ou configure um player diferente.")
            # Levanta erro para a GUI/CLI tratar, em vez de apenas logar.
            raise FileNotFoundError(f"Player '{self.player_executable}' não encontrado.")

        # User-Agent and Referer are not directly passed to mpv anymore as it gets the direct video URL
        # user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        # referer_url = "https://animefire.plus/" # Referer específico do AnimeFire, pode ser generalizado ou removido se não usado

        command = [
            self.player_executable,
            f"--title={title}",
            "--no-terminal",
            "--quiet",
        ]
        # Adicionar opções de cache/buffer se necessário, por exemplo:
        # command.extend(["--cache=yes", "--demuxer-max-bytes=500M", "--demuxer-readahead-secs=300"])
        command.append(video_url)

        log.info(f"Executando: {' '.join(command)}")

        try:
            # Usamos start_new_session=True para tentar desvincular o processo do player do terminal,
            # embora o comportamento exato possa variar. check=False para não dar erro se fechar.
            process = subprocess.run(command, check=False, start_new_session=True)

            # Log if the player exits immediately with an error code
            if process.returncode != 0:
                 log.warning(f"Player '{self.player_executable}' exited with code {process.returncode}. (This might be normal if the window was closed manually)")

        except FileNotFoundError: # Este caso é coberto pelo shutil.which acima, mas mantido por segurança.
            log.critical(f"Erro Crítico: Executável do player '{self.player_executable}' não encontrado durante a execução.", exc_info=True)
            raise # Re-levanta a exceção para que a camada superior possa tratá-la
        except Exception as e:
            log.error(f"Ocorreu um erro inesperado ao tentar tocar o vídeo: {e}", exc_info=True)
            # Considerar re-levantar a exceção ou retornar um status de falha
