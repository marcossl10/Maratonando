# Maratonando

A simple application to search for and watch anime, built with Python and Tkinter.

---

## Features

*   Anime search (currently using AnimeFire).
*   Episode listing.
*   Episode playback using the MPV player.
*   Simple graphical user interface.

---

## Dependencies

Make sure you have the following dependencies installed:

*   **Runtime:** `python`, `tk`, `python-requests`, `python-beautifulsoup4`, `python-click`, `yt-dlp`, `python-sv-ttk`, `mpv`
*   **Build-time (for `makepkg`):** `base-devel`, `git`

You can usually install the runtime dependencies using your package manager. The `PKGBUILD` will list them, and `makepkg -si` should prompt to install missing ones.

---

## Installation (Arch Linux)

1.  **Install build dependencies (if you don't have them):**
    ```bash
    sudo pacman -S --needed base-devel git
    ```

2.  **Clone the repository:**
    ```bash
    git clone https://github.com/marcossl10/Maratonando.git
    cd Maratonando
    ```

3.  **Build and install the package (Recommended Method):**
    ```bash
    makepkg -si
    ```
    *   This command uses the `PKGBUILD` file.
    *   It will automatically download the correct source code version from the GitHub release tag.
    *   It handles dependencies listed in the `PKGBUILD`.
    *   It installs the application correctly integrated with the system (menu entry, icon, executable path).

---

## Usage

After installation, you can find "Maratonando" in your system's application menu or run it from the terminal:
```bash
maratonando
