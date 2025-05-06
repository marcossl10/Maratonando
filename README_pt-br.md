# Maratonando

Um aplicativo simples para buscar e assistir animes, feito em Python com Tkinter.

---

## Funcionalidades

*   Busca de animes (atualmente usando AnimeFire).
*   Listagem de episódios.
*   Reprodução de episódios usando o player MPV.
*   Interface gráfica simples.

---

## Dependências

Certifique-se de ter as seguintes dependências instaladas:

*   **Para Rodar:** `python`, `tk`, `python-requests`, `python-beautifulsoup4`, `python-click`, `yt-dlp`, `python-sv-ttk`, `mpv`
*   **Para Compilar (com `makepkg`):** `base-devel`, `git`

A maioria das dependências de execução pode ser instalada usando o gerenciador de pacotes do seu sistema.
O `python-sv-ttk` é uma exceção, pois geralmente é encontrado no Arch User Repository (AUR). Você pode instalá-lo usando um auxiliar AUR como `yay` (ex: `yay -S python-sv-ttk`) ou `paru` (ex: `paru -S python-sv-ttk`).

O arquivo `PKGBUILD`, usado com o método de instalação recomendado `makepkg -si`, lista todas as dependências. O comando `makepkg -si` deve tentar resolver e instalar estas dependências, incluindo pacotes do AUR como o `python-sv-ttk`, se o seu sistema estiver configurado com um auxiliar AUR ou se você o tiver pré-instalado.

---

## Instalação (Arch Linux)

1.  **Instale as dependências de compilação (se ainda não tiver):**
    ```bash
    sudo pacman -S --needed base-devel git
    ```

2.  **Clone o repositório:**
    ```bash
    git clone https://github.com/marcossl10/Maratonando.git
    cd Maratonando
    ```

3.  **Compile e instale o pacote (Método Recomendado):**
    ```bash
    makepkg -si
    ```
    *   Este comando usa o arquivo `PKGBUILD`.
    *   Ele baixará automaticamente a versão correta do código-fonte da tag de release do GitHub.
    *   Ele lida com as dependências listadas no `PKGBUILD`.
    *   Ele instala a aplicação corretamente integrada ao sistema (entrada de menu, ícone, caminho do executável).

---

## Uso

Após a instalação, você pode encontrar o "Maratonando" no menu de aplicativos do seu sistema ou executá-lo pelo terminal:
```bash
maratonando
 Me pague um café? Pix 83980601072