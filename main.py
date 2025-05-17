#!/usr/bin/env python3
import logging
import sys

# Importa a função principal da CLI do seu pacote
from maratonando_src.cli import cli
# Importa a função principal da GUI do seu pacote
from maratonando_src.gui import main_gui_func

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                    stream=sys.stderr)

if __name__ == "__main__":
    # Verifica se foram passados argumentos de linha de comando além do nome do script
    if len(sys.argv) > 1:
        # Se houver argumentos, assume que é para a CLI e deixa o Click gerenciá-los
        cli()
    else:
        # Se nenhum argumento for fornecido, inicia a interface gráfica
        logging.info("Nenhum argumento CLI fornecido. Iniciando a interface gráfica...")
        main_gui_func()