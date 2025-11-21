# Python-Mini-Shell

A small Unix-like shell implemented in Python. Supports built-in commands, pipelines, history, tab completion, and I/O redirection.

<p align="left">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/"><img src="https://img.shields.io/badge/Open%20Source-GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"></a>

  <a href="https://en.wikipedia.org/wiki/Unix_shell"><img src="https://img.shields.io/badge/Shell-Unix%20Like-yellow?style=for-the-badge" alt="Unix Shell"></a>
  <a href="https://readline.gnu.org/"><img src="https://img.shields.io/badge/readline-support-1192FC?style=for-the-badge" alt="Readline"></a>
</p>


## Features

- **Built-in commands:**  
  - `echo`: Print arguments to standard output.  
  - `pwd`: Show current working directory.  
  - `cd <dir>`: Change directory (supports `~`, absolute, and relative paths).  
  - `type <cmd>`: Show if a command is builtin or which executable is found in `$PATH`.  
  - `history`: View, load, and save command history.  
  - `exit`: Exit the shell.

- **External commands:**  
  - Runs system commands found in `$PATH`.

- **Pipelines:**  
  - Chain commands with `|` (e.g., `ls | grep py`).

- **Redirection:**  
  - Standard output: `>`, `>>` (append)  
  - Standard error: `2>`, `2>>`  
  - Both can be combined.

- **Command history:**  
  - Persistent or session-based, supports loading from and saving to files.

- **Tab completion:**  
  - Completes built-in commands, executables, and file paths.


## Quickstart

### Requirements

- Python 3.x  
- Unix-like OS (uses `os.fork`; not supported natively on Windows, use WSL if needed).

### Usage

1. **Clone and run:**

    ```
    git clone https://github.com/yourusername/py-mini-shell.git
    cd py-mini-shell
    python3 app.py
    ```

2. **Example session:**

    ```
    $ pwd
    /home/user

    $ echo Hello world!
    Hello world!

    $ cd /tmp
    $ pwd
    /tmp

    $ ls | grep ".log" > logs.txt
    $ cat logs.txt
    app.log
    system.log

    $ history 3
        1  pwd
        2  cd /tmp
        3  ls | grep ".log" > logs.txt

    $ exit
    ```

## File Structure

app.py # Python shell source code
README.md # Project documentation
LICENSE # License (MIT recommended)
requirements.txt# Python dependencies (if any)
.gitignore # (Optional) Git ignore file


## How It Works

- Input is parsed with support for quotes, escapes, and pipelines.
- Built-in commands are handled natively; others invoke executables from `$PATH`.
- Redirection and pipelines use file descriptors and subprocesses.
- History can be loaded/saved via command or `$HISTFILE`.
- Tab completion uses `readline` for commands and files.

## 📄 License

This project is open source and available under the [GNU General Public License v3.0](LICENSE)