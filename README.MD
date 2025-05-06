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

*   **Runtime:** `python`, `tk`, `python-requests`, `python-beautifulsoup4`, `python-click`, `yt-dlp`, `sv-ttk`, `mpv`
*   **Runtime:** `python`, `tk`, `python-requests`, `python-beautifulsoup4`, `python-click`, `yt-dlp`, `python-sv-ttk`, `mpv`
*   **Build-time (for `makepkg`):** `base-devel`, `git`

Most runtime dependencies can be installed using your system's package manager.
`python-sv-ttk` is an exception as it's typically found in the Arch User Repository (AUR). You can install it using an AUR helper such as `yay` (e.g., `yay -S python-sv-ttk`) or `paru` (e.g., `paru -S python-sv-ttk`).

The `PKGBUILD` file, used with the recommended `makepkg -si` installation method, lists all dependencies. `makepkg -si` should attempt to resolve and install these, including AUR packages like `python-sv-ttk` if your system is configured with an AUR helper or if you have pre-installed it.

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
