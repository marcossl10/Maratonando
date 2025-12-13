# /home/marcos/Documentos/Maratonando1/maratonando_src/core/parsers/__init__.py

# Importa a classe base se você tiver uma (opcional, mas bom para referência)
# from .base_parser import BaseParser

# Importa cada parser individualmente
from .animefire_parser import AnimeFireParser
from .animesonline_parser import MinhaSerieParser # Adiciona o novo parser

# Opcional: você pode definir __all__ para explicitar o que é exportado
# __all__ = [
#     "AnimeFireParser",
# ]
