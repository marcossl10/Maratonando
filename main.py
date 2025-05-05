#!/usr/bin/env python3
from maratonando.cli import cli
import logging
import sys

# Configuração básica de logging para exibir INFO e acima no stderr
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                    stream=sys.stderr)

if __name__ == "__main__":
    cli()