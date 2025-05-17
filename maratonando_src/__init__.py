import sys
import os

# Obtém o caminho para o diretório 'maratonando_src'
_maratonando_src_dir = os.path.dirname(os.path.abspath(__file__))

# Adiciona o diretório 'maratonando_src' ao sys.path se ainda não estiver lá.
# Isso permite que subpacotes embutidos (como customtkinter) importem outros
# subpacotes embutidos (como darkdetect) usando uma sintaxe de importação de
# nível superior (ex: `import darkdetect`).
if _maratonando_src_dir not in sys.path:
    sys.path.insert(0, _maratonando_src_dir)

# Deixe o restante do arquivo __init__.py vazio se não houver mais nada a adicionar.