# /home/marcos/Maratonando/PKGBUILD

pkgname=maratonando
pkgver=2.0.0
pkgrel=1
pkgdesc="Busca e assiste animes."
arch=('any')
url="https://github.com/marcossl10/Maratonando.git"
license=('MIT')
depends=(
    'python'
    'python-flet'         # Adicionado para a interface Flet
    'python-requests'
    'python-beautifulsoup4' # Para parsear HTML
    'python-click'          # Para CLI
    'yt-dlp'                # Para baixar vídeos (usado por alguns parsers)
    'mpv'                   # Player de vídeo externo
)
makedepends=()
# O makepkg irá nomear o diretório fonte como $pkgname-$pkgver
# Exemplo: maratonando-2.0.0
source=("${pkgname}-${pkgver}.tar.gz::${url%.git}/archive/refs/tags/v${pkgver}.tar.gz"
        "maratonando.desktop"
        "maratonando.png::${url%.git}/raw/main/icons/maratonando.png" # Assume que o ícone está em /icons no repo
        "LICENSE::${url%.git}/raw/main/LICENSE") # Assume que a licença está na raiz do repo
sha256sums=('SKIP' # Para o tar.gz do código fonte, idealmente você geraria isso após o primeiro download
            'SKIP' # Para maratonando.desktop local
            'SKIP' # Para maratonando.png do repo
            'SKIP') # Para LICENSE do repo

prepare() {
    # Navega para o diretório srcdir primeiro
    cd "${srcdir}"
    # Encontra o diretório extraído (deve haver apenas um após a extração do tarball)
    # e entra nele. O nome pode variar dependendo de como o GitHub nomeia o diretório raiz no tarball.
    # Ex: Maratonando-2.0.0 ou Maratonando-v2.0.0
    extracted_dir=$(ls -d */ | head -n 1 | sed 's/\///') # Pega o primeiro diretório e remove a barra final
    cd "${extracted_dir}"
    echo "Entrou em: $(pwd)"
    echo "Conteúdo de $(pwd) após extração:"
    ls -lah
}

package() {
    _pythondir="${pkgdir}/usr/lib/python$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages"

    install -d "${_pythondir}/${pkgname}/core/parsers"
    # O diretório assets será criado ao copiar a pasta inteira abaixo
    install -d "${pkgdir}/usr/bin"
    install -d "${pkgdir}/usr/share/licenses/${pkgname}"
    install -d "${pkgdir}/usr/share/applications"
    install -d "${pkgdir}/usr/share/pixmaps"

    # --- Verificação Essencial ---
    if [ ! -d "maratonando_src" ]; then
        # Since prepare() cd's into the extracted source, pwd is the extracted source dir
        echo "ERRO: Diretório fonte 'maratonando_src' não encontrado em '$(pwd)'!" >&2
        echo "Conteúdo de '$(pwd)':" >&2
        ls -lah "$(pwd)" >&2
        return 1 # Falha o build
    fi
    # --- Fim Verificação ---

    # Instala o módulo Python
    cp -r maratonando_src/* "${_pythondir}/${pkgname}/"
    # Garante que o diretório assets exista se maratonando_src/assets estiver vazio mas existir
    # ou se for copiado como um diretório vazio.
    # Se maratonando_src/assets tiver conteúdo, o cp acima já o terá copiado.
    # Esta linha é mais uma garantia.
    install -d "${_pythondir}/${pkgname}/assets"

    # Instala o ícone (baixado do repo ou local)
    install -Dm644 "${srcdir}/maratonando.png" "${pkgdir}/usr/share/pixmaps/${pkgname}.png"

    _pythondir_runtime="/usr/lib/python$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages" # Caminho real no sistema
    cat > "${pkgdir}/usr/bin/${pkgname}" <<EOF
#!/bin/bash
_PYTHON_PKG_DIR="${_pythondir_runtime}/${pkgname}"
_FLET_GUI_FILE="\${_PYTHON_PKG_DIR}/flet_gui.py" # Caminho para a GUI Flet
_CLI_FILE="\${_PYTHON_PKG_DIR}/cli.py"

# Prioriza a GUI Flet, se existir
if [ -f "\${_FLET_GUI_FILE}" ]; then
    python -m ${pkgname}.flet_gui "\$@"
# Fallback para a CLI, se nenhuma GUI existir
elif [ -f "\${_CLI_FILE}" ]; then
    python -m ${pkgname}.cli "\$@"
else
    echo "Erro: Não foi possível encontrar um ponto de entrada válido (flet_gui.py, gui.py, ou cli.py) para ${pkgname}." >&2
    echo "Conteúdo de \${_PYTHON_PKG_DIR}:" >&2
    ls -lah "\${_PYTHON_PKG_DIR}" >&2
    exit 1
fi
EOF
    chmod +x "${pkgdir}/usr/bin/${pkgname}"

    # Instala a licença (baixada do repo ou local)
    install -Dm644 "${srcdir}/LICENSE" "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
    install -Dm644 "${srcdir}/maratonando.desktop" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
}
