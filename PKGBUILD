# /home/marcos/Maratonando/PKGBUILD 

pkgname=maratonando
pkgver=1.1.1
# Incrementa pkgrel para indicar mudança na lógica de build local e dependência
pkgrel=10
pkgdesc="Busca e assiste animes."
arch=('any')
url="https://github.com/marcossl10/Maratonando.git"
license=('MIT')
depends=(
    'python'
    'tk'
    'python-requests'
    'python-beautifulsoup4' # Para parsear HTML
    'python-cloudscraper'   # Para lidar com proteções Cloudflare
    'python-click'          # Para parsers ou CLI
    'yt-dlp'                # Para baixar vídeos
   #'python-sv-ttk'         # Para o tema da GUI - Verifique se está instalado via pip ou se precisa como dependência
    'mpv'                   # Player de vídeo externo
)
makedepends=()
# Nenhuma fonte externa listada, usaremos prepare() para copiar as locais
source=()
# Nenhum checksum necessário para fontes locais copiadas manualmente
md5sums=()

# A função prepare() copia os arquivos locais para o diretório de build ($srcdir)
prepare() {
    # $startdir é o diretório onde o PKGBUILD está localizado
    # $srcdir é o diretório de build temporário do makepkg
    echo "Copiando fontes de $startdir para $srcdir..."
    cp -r "$startdir/maratonando_src" "$srcdir/"
    cp -r "$startdir/icons" "$srcdir/"
    cp "$startdir/LICENSE" "$srcdir/"
    cp "$startdir/maratonando.desktop" "$srcdir/"
    echo "Conteúdo de $srcdir após prepare():"
    ls -lah "$srcdir"
}

# Não precisamos da função build()

package() {
    # O código fonte agora está diretamente em $srcdir
    cd "$srcdir"

    _pythondir="${pkgdir}/usr/lib/python$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages"

    # Cria diretórios de destino
    install -d "${_pythondir}/${pkgname}/core/parsers"
    install -d "${pkgdir}/usr/bin"
    install -d "${pkgdir}/usr/share/licenses/${pkgname}"
    install -d "${pkgdir}/usr/share/applications"
    install -d "${pkgdir}/usr/share/pixmaps"

    # --- Verificação Essencial ---
    if [ ! -d "maratonando_src" ]; then
        echo "ERRO: Diretório fonte '$srcdir/maratonando_src' não encontrado após prepare()!" >&2
        echo "Conteúdo de $srcdir:" >&2
        ls -lah "$srcdir" >&2
        return 1 # Falha o build
    fi
    # --- Fim Verificação ---

    # Copia o código usando install
    # Copia o conteúdo de core/parsers
    install -Dm644 maratonando_src/core/parsers/*.py "${_pythondir}/${pkgname}/core/parsers/"
    # Copia o conteúdo de core (exceto parsers)
    install -Dm644 maratonando_src/core/*.py "${_pythondir}/${pkgname}/core/"
    # Copia arquivos .py da raiz de maratonando_src (cli.py, gui.py, etc.)
    install -Dm644 maratonando_src/*.py "${_pythondir}/${pkgname}/"

    # Instala o ícone da subpasta 'icons'
    install -Dm644 "icons/maratonando.png" "${pkgdir}/usr/share/pixmaps/${pkgname}.png"

    # Cria o script executável em /usr/bin (sem DEBUG)
    _pythondir_runtime="/usr/lib/python$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages" # Caminho real no sistema
    cat > "${pkgdir}/usr/bin/${pkgname}" <<EOF
#!/bin/bash
_PYTHON_PKG_DIR="${_pythondir_runtime}/${pkgname}"
_GUI_FILE="\${_PYTHON_PKG_DIR}/gui.py"
_CLI_FILE="\${_PYTHON_PKG_DIR}/cli.py"

# Tenta chamar a GUI primeiro, se existir
if [ -f "\${_GUI_FILE}" ]; then
    python -m ${pkgname}.gui "\$@"
# Senão, chama a CLI
elif [ -f "\${_CLI_FILE}" ]; then
    python -m ${pkgname}.cli "\$@"
else
    echo "Erro: Não foi possível encontrar o ponto de entrada (gui.py ou cli.py) para ${pkgname}." >&2
    echo "Conteúdo de \${_PYTHON_PKG_DIR}:" >&2
    ls -lah "\${_PYTHON_PKG_DIR}" >&2 # Lista o conteúdo do diretório em caso de erro
    exit 1
fi
EOF
    chmod +x "${pkgdir}/usr/bin/${pkgname}"

    # Instala os arquivos LICENSE e .desktop que estão no $srcdir (copiados do diretório atual)
    install -Dm644 "LICENSE" "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
    install -Dm644 "maratonando.desktop" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
}


