# Maratonando

**Maratonando: Encontre e assista animes, diretamente do seu desktop Linux.**

Este aplicativo permite buscar e reproduzir conteúdo de diversas fontes online, utilizando uma interface gráfica amigável construída com CustomTkinter ou uma interface de linha de comando (CLI). Ele se integra com o player MPV para uma experiência de visualização robusta.

---

## Status do Projeto

Em desenvolvimento ativo.

<!-- 
## Capturas de Tela (Opcional)

Adicione aqui capturas de tela da sua GUI.
Exemplo:
![Captura de Tela da GUI Principal](link_para_sua_imagem.png)
-->

---

## Funcionalidades Principais

*   Busca de animes, filmes e séries em diferentes fontes (atualmente AnimeFire e AnimesOnline).
*   Interface gráfica moderna e intuitiva.
*   Interface de Linha de Comando (CLI) para usuários de terminal.
*   Reprodução de vídeo utilizando o player MPV.
*   Histórico de episódios assistidos com opção de favoritos.
*   Cache de imagens para carregamento mais rápido de capas.
*   Seleção de servidor/fonte de conteúdo.

---

## Dependências Gerais

Para o correto funcionamento do Maratonando, as seguintes dependências são geralmente necessárias, independentemente do método de instalação:

*   **Python 3** (versão 3.7 ou superior)
*   **mpv:** Player de mídia.
*   **yt-dlp (opcional, mas recomendado):** Para melhor extração de links de vídeo de algumas fontes.

As dependências Python específicas do aplicativo (como Pillow, Requests, BeautifulSoup4, Click, CustomTkinter, darkdetect, packaging) são gerenciadas de forma diferente dependendo do método de instalação:
*   **Arch Linux:** O `PKGBUILD` tentará obtê-las (algumas dos repositórios oficiais, outras do AUR ou via pip).
*   **Pacote .deb:** A maioria dessas dependências Python (incluindo CustomTkinter e darkdetect) estão embutidas no pacote. As dependências de sistema como `python3-tk`, `python3-pil`, `python3-requests`, `python3-bs4`, `python3-click`, `python3-packaging` serão instaladas via `apt`.

---

## Instalação

### Arch Linux e Derivados

1.  **Clone o repositório (se ainda não o fez):**
    ```bash
    git clone https://github.com/marcossl10/Maratonando.git 
    cd Maratonando
    ```
2.  **Construa e instale o pacote usando `makepkg`:**
    O arquivo `PKGBUILD` (localizado na raiz do projeto ou em uma subpasta dedicada ao Arch) cuidará de baixar as dependências e construir o pacote.
    ```bash
    makepkg -si
    ```
    Isso irá compilar o pacote e instalá-lo no seu sistema. O `makepkg` tentará resolver as dependências listadas no `PKGBUILD`. Algumas, como `python-customtkinter`, podem vir do AUR (Arch User Repository), então você pode precisar de um helper AUR (como `yay` ou `paru`) ou instalá-las manualmente se o `makepkg -s` não as encontrar.

### Debian, Ubuntu, Pop!_OS, Linux Mint e Derivados

1.  **Baixe o pacote `.deb`:**
    Vá para a seção Releases do projeto no GitHub e baixe o arquivo `.deb` mais recente (ex: `python3-maratonando_VERSAO_all.deb`).

2.  **Instale o pacote:**
    Abra um terminal no diretório onde você baixou o arquivo e execute:
    ```bash
    sudo apt update
    sudo apt install ./python3-maratonando_VERSAO_all.deb
    ```
    (Substitua `VERSAO` pela versão correta do arquivo).
    O `apt` tentará instalar automaticamente as dependências necessárias listadas no pacote, como `mpv`, `python3-tk`, `python3-pil`, `python3-requests`, `python3-bs4`, `python3-click` e `python3-packaging`. Se o `mpv` não estiver instalado, você pode precisar instalá-lo separadamente: `sudo apt install mpv`.

---

## Uso

Após a instalação:

*   **Interface Gráfica (GUI):**
    Procure por "Maratonando" no menu de aplicativos do seu sistema ou execute o comando no terminal:
    ```bash
    maratonando
    ```
*   **Interface de Linha de Comando (CLI):**
    Para ver as opções disponíveis, execute:
    ```bash
    maratonando-cli --help
    ```

---

## Apoie o Projeto (Opcional)

Se você gosta deste projeto e quer apoiar o desenvolvimento:
*   **PIX:** `83980601072`

---

## Licença

Este projeto é licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---
*Desenvolvido por Marcos.*