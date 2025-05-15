# Maintainer: Marcos <marcosslprado@gmail.com>
pkgname=maratonando
pkgver=2.0.0
pkgrel=1
pkgdesc="Busca e assiste animes."
arch=('any')
url="https://github.com/marcossl10/Maratonando" # URL do projeto, não do git clone
license=('MIT')
depends=(
    'python'
    'python-customtkinter'  # Adicionado para a interface CustomTkinter
    'python-pillow'         # Adicionado para tratamento de imagens (capas, ícones)
    'python-requests'
    'python-beautifulsoup4' # Para parsear HTML
    'python-click'          # Para CLI
    'yt-dlp'                # Para baixar vídeos (usado por alguns parsers)
    'mpv'                   # Player de vídeo externo
)
# makedepends geralmente lista pacotes necessários APENAS para o processo de build (ex: setuptools, wheel)
makedepends=()
# O makepkg irá nomear o diretório fonte como NomeDoRepo-Tag
# Exemplo: Maratonando-2.0.0 ou Maratonando-v2.0.0
source=("${pkgname}-${pkgver}.tar.gz::${url}/archive/refs/tags/v${pkgver}.tar.gz"
        "maratonando.desktop"
        "maratonando.png::${url}/raw/v${pkgver}/icons/maratonando.png" # Baixa da tag específica
        "LICENSE::${url}/raw/v${pkgver}/LICENSE") # Baixa da tag específica
sha256sums=('431af37c850895bd89dc7b4eb663dff623df796820581e99651fa1adc135465c'
            'c8fdc92dc2287224fe982af8ffba37c0d8418dd9ff06ede5e1ecd0be13718ed7'
            '54b8f5958b72d9ebe5ff9bc58a608ca6ad21cad132f6d44f605d6208332365b4'
            'dd6ab43eaab3d3190bc738b25981f07f5c3601712c3d2cbec7b7b0fe4701f04b')


prepare() {
    # Navega para o diretório srcdir primeiro
    cd "${srcdir}"
    # Encontra o diretório extraído (deve haver apenas um após a extração do tarball)
    # e entra nele. O nome pode variar dependendo de como o GitHub nomeia o diretório raiz no tarball.
    # Assumindo que o nome do diretório extraído é "Maratonando-${pkgver}" ou "Maratonando-v${pkgver}"
    # A variável extracted_dir é usada para flexibilidade, caso o nome do diretório mude.
    extracted_dir=$(ls -d Maratonando-${pkgver}/ 2>/dev/null || ls -d Maratonando-v${pkgver}/ 2>/dev/null || ls -d */ | head -n 1 | sed 's/\///')

    if [ -z "${extracted_dir}" ] || [ ! -d "${extracted_dir}" ]; then
        echo "ERRO: Diretório fonte extraído não encontrado em '$(pwd)'!" >&2
        echo "Conteúdo de '$(pwd)':" >&2
        ls -lah "$(pwd)" >&2
        return 1 # Falha o build
    fi
    cd "${extracted_dir}" || return 1

    echo "Entrou em: $(pwd)"
    echo "Conteúdo de $(pwd) após extração:"
    ls -lah
}

package() {
    # Navega para o diretório do código fonte extraído.
    # Usa a mesma lógica de `prepare()` para encontrar o diretório.
    cd "${srcdir}"
    extracted_dir=$(ls -d Maratonando-${pkgver}/ 2>/dev/null || ls -d Maratonando-v${pkgver}/ 2>/dev/null || ls -d */ | head -n 1 | sed 's/\///')

    if [ -z "${extracted_dir}" ] || [ ! -d "${extracted_dir}" ]; then
        echo "ERRO: Diretório fonte extraído não encontrado em '$(pwd)' durante package()!" >&2
        return 1 # Falha o build
    fi
    cd "${extracted_dir}" || return 1


    _pythondir="${pkgdir}/usr/lib/python$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages"

    # Cria o diretório de destino para o módulo Python
    install -d "${_pythondir}/${pkgname}"

    # --- Verificação Essencial ---
    if [ ! -d "maratonando_src" ]; then
        # Verifica se o diretório do módulo Python existe
        echo "ERRO: Diretório fonte 'maratonando_src' não encontrado em '$(pwd)'!" >&2
        echo "Conteúdo de '$(pwd)':" >&2
        ls -lah "$(pwd)" >&2
        return 1 # Falha o build
    fi

    # Instala o módulo Python
    cp -r maratonando_src/* "${_pythondir}/${pkgname}/"
    # O diretório assets e outros subdiretórios dentro de maratonando_src
    # já são copiados pelo 'cp -r maratonando_src/*'.

    # Instala o ícone (baixado do repo ou local)
    install -Dm644 "${srcdir}/maratonando.png" "${pkgdir}/usr/share/pixmaps/${pkgname}.png"

    # Cria o script executável em /usr/bin
    # Garante que o diretório de destino para o script exista
    install -d "${pkgdir}/usr/bin"

    cat > "${pkgdir}/usr/bin/${pkgname}" <<EOF
#!/usr/bin/env bash

# Executa o módulo da GUI CustomTkinter
# Se o módulo ou suas dependências não forem encontrados, 'python -m' lidará com o erro.
exec python -m ${pkgname}.gui "\$@"
EOF
    chmod +x "${pkgdir}/usr/bin/${pkgname}"

    # Instala o arquivo .desktop
    install -Dm644 "${srcdir}/${pkgname}.desktop" "${pkgdir}/usr/share/applications/${pkgname}.desktop"

    # Instala a licença
    install -Dm644 "LICENSE" "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
