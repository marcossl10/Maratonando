#!/usr/bin/env python3
import logging
import sys

from maratonando_src.cli import cli
from animesonline_parser import extrair_animes_animesonline

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                    stream=sys.stderr)

def mostrar_animes_online():
    """Função de exemplo/teste para extrair animes de um parser local."""
    logging.info("Executando extração de teste de 'animesonline_parser.py' local...")
    animes = extrair_animes_animesonline()
    for anime in animes:
        print(anime["titulo"], anime["link"])
    logging.info("Extração de teste concluída.")

if __name__ == "__main__":
    # mostrar_animes_online()

    cli()