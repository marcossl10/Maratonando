import sys
import logging
from .cli import cli
from .gui import main_gui_func

def start():
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                        stream=sys.stderr)

    if len(sys.argv) > 1:
        cli()
    else:
        logging.info("Iniciando interface gráfica...")
        main_gui_func()