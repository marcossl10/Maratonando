# Maintainer: Marcos <marcosslprado@gmail.com>
pkgname=maratonando
pkgver=1.0.0
pkgrel=1
pkgdesc="Assista animes e séries via CLI ou GUI"
arch=('any')
url="https://github.com/marcossl10/Maratonando"
license=('GPL')
depends=('python' 'python-requests' 'python-beautifulsoup4' 'python-pillow' 'python-click' 'yt-dlp' 'mpv' 'tk')
makedepends=('git')
provides=('maratonando')
conflicts=('maratonando')
source=("git+https://github.com/marcossl10/Maratonando.git")
md5sums=('SKIP')

pkgver() {
	cd "Maratonando"
	printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package() {
	cd "Maratonando"
	
	_install_dir="/usr/share/$pkgname"
	
	install -d "$pkgdir$_install_dir"
	install -d "$pkgdir/usr/bin"
	install -d "$pkgdir/usr/share/applications"
	install -d "$pkgdir/usr/share/icons/hicolor/256x256/apps"

	# Copia o código fonte e recursos
	cp -r maratonando_src "$pkgdir$_install_dir/"
	cp -r icons "$pkgdir$_install_dir/"
	install -m644 main.py "$pkgdir$_install_dir/"
	
	# Instala o ícone para o sistema
	if [ -f "icons/maratonando.png" ]; then
		install -m644 "icons/maratonando.png" "$pkgdir/usr/share/icons/hicolor/256x256/apps/$pkgname.png"
	fi

	# Cria o script de execução no /usr/bin
	echo "#!/bin/sh" > "$pkgdir/usr/bin/$pkgname"
	echo "exec python3 $_install_dir/main.py \"\$@\"" >> "$pkgdir/usr/bin/$pkgname"
	chmod 755 "$pkgdir/usr/bin/$pkgname"

	# Cria o atalho .desktop
	cat > "$pkgdir/usr/share/applications/$pkgname.desktop" <<EOF
[Desktop Entry]
Name=Maratonando
Comment=Assista animes e séries
Exec=$pkgname
Icon=$pkgname
Terminal=false
Type=Application
Categories=Video;AudioVideo;
StartupNotify=true
EOF
}