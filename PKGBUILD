# /home/marcos/Maratonando/PKGBUILD

pkgname=maratonando
pkgver=1.1.1
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
    'python-click'          # Para CLI
    'yt-dlp'                # Para baixar vídeos
    'mpv'                   # Player de vídeo externo
)
makedepends=()
source=()
# Nenhum checksum necessário para fontes locais copiadas manualmente
md5sums=()

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

package() {
    cd "$srcdir"

    _pythondir="${pkgdir}/usr/lib/python$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages"

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

    install -Dm644 maratonando_src/core/parsers/*.py "${_pythondir}/${pkgname}/core/parsers/"
    install -Dm644 maratonando_src/core/*.py "${_pythondir}/${pkgname}/core/"
    install -Dm644 maratonando_src/*.py "${_pythondir}/${pkgname}/"

    install -Dm644 "icons/maratonando.png" "${pkgdir}/usr/share/pixmaps/${pkgname}.png"

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
    ls -lah "\${_PYTHON_PKG_DIR}" >&2
    exit 1
fi
EOF
    chmod +x "${pkgdir}/usr/bin/${pkgname}"

    install -Dm644 "LICENSE" "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
    install -Dm644 "maratonando.desktop" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
}
