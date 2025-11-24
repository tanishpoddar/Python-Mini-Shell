<div align="center">

# 🐚 Python-Mini-Shell

### A lightweight Unix-like shell implemented in Python

*Supports built-in commands, pipelines, history, tab completion, and I/O redirection*

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/tanishpoddar/Python-Mini-Shell"><img src="https://img.shields.io/badge/Open%20Source-GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"></a>
  <a href="https://en.wikipedia.org/wiki/Unix_shell"><img src="https://img.shields.io/badge/Shell-Unix%20Like-yellow?style=for-the-badge" alt="Unix Shell"></a>
  <a href="https://pypi.org/project/pyreadline3/"><img src="https://img.shields.io/badge/pyreadline3-support-1192FC?style=for-the-badge" alt="Readline"></a>
</p>

---

</div>


## ✨ Features

### 🔧 Built-in Commands
- **`echo`** - Print arguments to standard output
- **`pwd`** - Show current working directory
- **`cd <dir>`** - Change directory (supports `~`, absolute, and relative paths)
- **`type <cmd>`** - Show if a command is builtin or which executable is found in `$PATH`
- **`history`** - View, load, and save command history
- **`exit`** - Exit the shell

### 🚀 Advanced Features
- **External Commands** - Runs system commands found in `$PATH`
- **Pipelines** - Chain commands with `|` (e.g., `ls | grep py`)
- **I/O Redirection**
  - Standard output: `>`, `>>` (append)
  - Standard error: `2>`, `2>>`
  - Both can be combined
- **Command History** - Persistent or session-based, supports loading from and saving to files
- **Tab Completion** - Completes built-in commands, executables, and file paths


## 🚀 Quickstart

### 📋 Requirements

- **Python 3.x**
- **Windows OS** (uses `pyreadline3` for tab completion and history support)

### 💻 Installation & Usage

**Clone and install dependencies:**

```bash
git clone https://github.com/tanishpoddar/Python-Mini-Shell.git
cd Python-Mini-Shell
pip install -r requirements.txt
python app.py
```

### 📝 Example Session

```bash
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

## 📁 File Structure

```
Python-Mini-Shell/
├── app.py              # Python shell source code
├── README.md           # Project documentation
├── LICENSE             # License (GNU GPL v3.0)
├── requirements.txt    # Python dependencies (pyreadline3)
└── .gitignore          # Git ignore file
```


## ⚙️ How It Works

- **Input Parsing** - Supports quotes, escapes, and pipelines
- **Command Execution** - Built-in commands handled natively; external commands invoke executables from `$PATH`
- **I/O Management** - Redirection and pipelines use file descriptors and subprocesses
- **History Management** - Can be loaded/saved via command or `$HISTFILE`
- **Tab Completion** - Uses `pyreadline3` (Windows-compatible readline) for commands and files

---

<div align="center">

## 📄 License

This project is open source and available under the [GNU General Public License v3.0](LICENSE)

**Made with ❤️ by [Tanish Poddar](https://github.com/tanishpoddar)**

⭐ Star this repo if you find it helpful!

</div>