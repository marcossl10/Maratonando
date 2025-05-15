# Maratonando

Um aplicativo para buscar e assistir animes, feito em Python com a interface gráfica CustomTkinter e Linha de Comando (CLI).

---

## Funcionalidades

*   Busca de animes em diferentes fontes (atualmente AnimeFire e AnimesOnline).
*   Interface gráfica moderna (CustomTkinter) e Linha de Comando (CLI).
*   Seleção de servidor (fonte) na interface gráfica.
*   Listagem de episódios.
*   Obtenção de links diretos de vídeo.
*   Reprodução de episódios usando o player MPV.
*   Histórico de episódios assistidos.
---

## Dependências

Certifique-se de ter as seguintes dependências instaladas:

*   **Para Rodar (com Flet):** `python`, `python-flet`, `python-requests`, `python-beautifulsoup4`, `python-click`, `yt-dlp`, `mpv`
*   **Para Compilar o Pacote Arch (com `makepkg`):** `base-devel`, `git`

As dependências de execução podem ser instaladas usando o gerenciador de pacotes do seu sistema.
Por exemplo, no Arch Linux e derivados:
```bash
sudo pacman -S python python-pillow python-requests python-beautifulsoup4 python-click yt-dlp mpv
```
A dependência `python-customtkinter` pode precisar ser instalada via pip se não estiver nos repositórios oficiais:
```bash
pip install customtkinter
```

O arquivo `PKGBUILD` (para Arch Linux) lista todas as dependências necessárias e o comando `makepkg -si` tentará resolvê-las, incluindo `python-customtkinter` (que pode estar no AUR ou você pode precisar instalá-lo via pip antes, dependendo da sua configuração).

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

"Me pague um café! Pix 83980601072"