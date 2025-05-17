# /home/marcos/Maratonando/setup.py
import os
from setuptools import setup, find_packages

# Função para ler requisitos de um arquivo (opcional, se você tiver um)
# def parse_requirements(filename):
#     """Carrega requisitos de um arquivo requirements.txt."""
#     lineiter = (line.strip() for line in open(filename))
#     return [line for line in lineiter if line and not line.startswith("#")]

# Crie um README.md básico se não existir, para o sdist
if not os.path.exists('README.md'):
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write("Maratonando: Encontre e assista animes, filmes e séries.\n")

setup(
    name='maratonando',
    version='0.2.0',  # Incremente a versão se fez mudanças significativas
    author='Marcos',
    author_email='marcosslprado@gmail.com',
    description='Encontre e assista animes, filmes e séries.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    # url='URL_DO_SEU_PROJETO_SE_TIVER', # Ex: Link do GitHub
    packages=find_packages(include=['maratonando_src', 'maratonando_src.*']), # Encontra maratonando_src e seus subpacotes
    # package_dir={'maratonando_src': 'maratonando_src'}, # Geralmente não necessário com find_packages se a estrutura for padrão
    include_package_data=True, # Importante para incluir arquivos definidos no MANIFEST.in e package_data
    package_data={
        'maratonando_src': ['assets/*.png', 'assets/*.ttf'], # Mantém os assets específicos
        # customtkinter e darkdetect serão incluídos por serem pacotes e include_package_data=True
    },
    install_requires=[
        'click', # Para o cli.py
        # 'customtkinter>=5.2.0', # REMOVIDO - Agora está embutido
        'requests',
        'Pillow', # Para manipulação de imagens
        'beautifulsoup4', # Se algum parser usar diretamente (o seu AnimesOnlineParser usa)
    ],
    entry_points={
        'console_scripts': [
            'maratonando-cli = maratonando_src.cli:cli', # Para a interface de linha de comando
        ],
    },
    scripts=['scripts/maratonando'], # Script lançador para a GUI
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License', # Ou a licença que você escolher
        'Operating System :: POSIX :: Linux',
        'Environment :: X11 Applications', # Indica que é uma aplicação gráfica para X11
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Video :: Display',
    ],
    python_requires='>=3.7', # Verifique a compatibilidade do customtkinter e outras dependências
)
