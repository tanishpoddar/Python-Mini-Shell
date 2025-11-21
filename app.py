#!/usr/bin/env python3
import sys
import os
import subprocess
import readline
import time
from typing import List

# --- Configuration / builtins ------------------------------------------------
builtins = ["echo", "exit", "type", "pwd", "cd", "history"]

# --- History storage and append tracking -------------------------------------
history_list: List[str] = []
last_append_idx = 0  # index in history_list up to which appended to last -a write

# --- Utilities ---------------------------------------------------------------
def find_executable(cmd: str):
    path_env = os.environ.get("PATH", "")
    for directory in path_env.split(os.pathsep):
        if not directory:
            continue
        full_path = os.path.join(directory, cmd)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

_exec_cache = {"names": None, "ts": 0.0, "ttl": 1.0}
def get_path_executables():
    now = time.time()
    if _exec_cache["names"] is not None and (now - _exec_cache["ts"] < _exec_cache["ttl"]):
        return _exec_cache["names"]
    path_env = os.environ.get("PATH", "")
    executable_names = set()
    for directory in path_env.split(os.pathsep):
        if not directory or not os.path.isdir(directory):
            continue
        try:
            for fname in os.listdir(directory):
                fpath = os.path.join(directory, fname)
                if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
                    executable_names.add(fname)
        except Exception:
            continue
    names = sorted(executable_names)
    _exec_cache["names"] = names
    _exec_cache["ts"] = now
    return names

def longest_common_prefix(strs: List[str]) -> str:
    if not strs:
        return ""
    min_len = min(len(s) for s in strs)
    lcp_chars = []
    for i in range(min_len):
        c = strs[0][i]
        if all(s[i] == c for s in strs):
            lcp_chars.append(c)
        else:
            break
    return "".join(lcp_chars)

# --- Command-line parsing ---------------------------------------------------
def parse_command_line(line: str) -> List[str]:
    tokens = []
    current = []
    in_single = False
    in_double = False
    i = 0
    while i < len(line):
        c = line[i]
        if in_single:
            if c == "'":
                in_single = False
            else:
                current.append(c)
            i += 1
            continue
        if in_double:
            if c == '"':
                in_double = False
                i += 1
                continue
            if c == '\\':
                i += 1
                if i < len(line):
                    next_c = line[i]
                    if next_c in ['"', '\\', '$', '`']:
                        current.append(next_c)
                    else:
                        current.append('\\')
                        current.append(next_c)
                    i += 1
                continue
            current.append(c)
            i += 1
            continue
        if c.isspace():
            if current:
                tokens.append(''.join(current))
                current = []
            i += 1
            while i < len(line) and line[i].isspace():
                i += 1
            continue
        if c == "'":
            in_single = True
            i += 1
            continue
        if c == '"':
            in_double = True
            i += 1
            continue
        if c == '\\':
            i += 1
            if i < len(line):
                current.append(line[i])
                i += 1
            continue
        current.append(c)
        i += 1
    if current:
        tokens.append(''.join(current))
    return tokens

def split_redirection(parts: List[str]):
    cmd_args = []
    stdout_redir_file = None
    stdout_append = False
    stderr_redir_file = None
    stderr_append = False
    i = 0
    while i < len(parts):
        part = parts[i]
        if part in ("1>>", ">>"):
            if i + 1 < len(parts):
                stdout_redir_file = parts[i + 1]
                stdout_append = True
                i += 2
                continue
        if part in ("1>", ">"):
            if i + 1 < len(parts):
                stdout_redir_file = parts[i + 1]
                stdout_append = False
                i += 2
                continue
        if part == "2>>":
            if i + 1 < len(parts):
                stderr_redir_file = parts[i + 1]
                stderr_append = True
                i += 2
                continue
        if part == "2>":
            if i + 1 < len(parts):
                stderr_redir_file = parts[i + 1]
                stderr_append = False
                i += 2
                continue
        if part.startswith("1>>"):
            stdout_redir_file = part[3:]
            stdout_append = True
            i += 1
            continue
        if part.startswith(">>"):
            stdout_redir_file = part[2:]
            stdout_append = True
            i += 1
            continue
        if part.startswith("1>"):
            stdout_redir_file = part[2:]
            stdout_append = False
            i += 1
            continue
        if part.startswith("2>>"):
            stderr_redir_file = part[3:]
            stderr_append = True
            i += 1
            continue
        if part.startswith("2>"):
            stderr_redir_file = part[2:]
            stderr_append = False
            i += 1
            continue
        cmd_args.append(part)
        i += 1
    return cmd_args, stdout_redir_file, stdout_append, stderr_redir_file, stderr_append

# --- I/O helpers -------------------------------------------------------------
def write_err(msg: str, stderr_redir_file=None):
    if msg.endswith("\n"):
        msg = msg[:-1]
    if stderr_redir_file:
        try:
            with open(stderr_redir_file, 'a') as f:
                f.write(msg + "\n")
        except Exception:
            sys.stderr.write(msg + "\n")
    else:
        sys.stderr.write(msg + "\n")

def write_out(msg: str, stdout_redir_file=None, append=False, stderr_redir_file=None):
    if msg.endswith("\n"):
        msg = msg[:-1]
    if stdout_redir_file:
        mode = 'a' if append else 'w'
        try:
            with open(stdout_redir_file, mode) as f:
                f.write(msg + "\n")
        except Exception as e:
            write_err(f"{msg}: {e}", stderr_redir_file)
    else:
        print(msg)

# --- Readline completer -----------------------------------------------------
def _complete_filenames(prefix: str) -> List[str]:
    if '/' in prefix:
        dirpart, basepart = prefix.rsplit('/', 1)
        if dirpart == '':
            dirpath = '/'
        else:
            dirpath = dirpart
        try:
            entries = os.listdir(dirpath)
        except Exception:
            return []
        matches = []
        for e in entries:
            if e.startswith(basepart):
                candidate = os.path.join(dirpart, e)
                matches.append(candidate)
        return sorted(matches)
    else:
        try:
            entries = os.listdir(os.getcwd())
        except Exception:
            return []
        matches = [e for e in entries if e.startswith(prefix)]
        return sorted(matches)

def external_and_builtin_completer(text: str, state: int):
    matches = []
    if '/' in text:
        matches = _complete_filenames(text)
    else:
        for cmd in builtins:
            if cmd.startswith(text):
                matches.append(cmd)
        for exec_name in get_path_executables():
            if exec_name.startswith(text) and exec_name not in builtins:
                matches.append(exec_name)
        matches = sorted(matches)
    if not matches:
        return None
    if len(matches) == 1:
        if state == 0:
            return matches[0] + ' '
        else:
            return None
    lcp = longest_common_prefix(matches)
    if state == 0 and lcp and len(lcp) > len(text):
        return lcp
    if state < len(matches):
        return matches[state]
    return None

def setup_readline():
    readline.set_completer(external_and_builtin_completer)
    readline.parse_and_bind('tab: complete')

# --- Pipeline / process execution -------------------------------------------
def execute_pipeline(stages_parts: List[List[str]]):
    if not stages_parts:
        return
    parsed = []
    for parts in stages_parts:
        (cmd_args,
         stdout_redir_file, stdout_append,
         stderr_redir_file, stderr_append) = split_redirection(parts)
        if not cmd_args:
            return
        parsed.append({
            "args": cmd_args,
            "stdout_redir": stdout_redir_file,
            "stdout_append": stdout_append,
            "stderr_redir": stderr_redir_file,
            "stderr_append": stderr_append,
            "is_builtin": cmd_args[0] in builtins,
            "exec_path": None,
            "stdout_f": None,
            "stderr_f": None
        })
    for p in parsed:
        if not p["is_builtin"]:
            p["exec_path"] = find_executable(p["args"][0])
            if not p["exec_path"]:
                write_err(f"{p['args'][0]}: command not found", None)
                return
    def open_redir_file(path, append):
        if not path:
            return None
        try:
            mode = 'a' if append else 'w'
            return open(path, mode)
        except Exception as e:
            write_err(f"Error preparing {path}: {e}", None)
            return None
    for p in parsed:
        p["stdout_f"] = open_redir_file(p["stdout_redir"], p["stdout_append"])
        p["stderr_f"] = open_redir_file(p["stderr_redir"], p["stderr_append"])
    n = len(parsed)
    pipes = []
    for i in range(n - 1):
        pipes.append(os.pipe())
    procs = []
    child_pids = []
    def run_builtin_child(cmd, args):
        if cmd == "exit":
            os._exit(0)
        elif cmd == "echo":
            output = " ".join(args)
            sys.stdout.write(output + ("\n" if not output.endswith("\n") else ""))
            sys.stdout.flush()
            os._exit(0)
        elif cmd == "type":
            if len(args) == 0:
                os._exit(0)
            target = args[0]
            if target in builtins:
                sys.stdout.write(f"{target} is a shell builtin\n")
            else:
                executable_path = find_executable(target)
                if executable_path:
                    sys.stdout.write(f"{target} is {executable_path}\n")
                else:
                    sys.stdout.write(f"{target}: not found\n")
            sys.stdout.flush()
            os._exit(0)
        elif cmd == "pwd":
            sys.stdout.write(os.getcwd() + "\n")
            sys.stdout.flush()
            os._exit(0)
        elif cmd == "cd":
            if len(args) == 0:
                os._exit(0)
            directory = args[0]
            try:
                if directory == "~":
                    home = os.environ.get("HOME")
                    if home and os.path.isdir(home):
                        os.chdir(home)
                    else:
                        sys.stderr.write(f"cd: {directory}: No such file or directory\n")
                elif directory.startswith("/"):
                    if os.path.isdir(directory):
                        os.chdir(directory)
                    else:
                        sys.stderr.write(f"cd: {directory}: No such file or directory\n")
                else:
                    target_path = os.path.join(os.getcwd(), directory)
                    if os.path.isdir(target_path):
                        os.chdir(target_path)
                    else:
                        sys.stderr.write(f"cd: {directory}: No such file or directory\n")
            except Exception:
                sys.stderr.write(f"cd: {directory}: No such file or directory\n")
            sys.stderr.flush()
            os._exit(0)
        elif cmd == "history":
            # Print history in child
            n_arg = None
            if args:
                try:
                    n_arg = int(args[0])
                except Exception:
                    n_arg = None
            total = len(history_list)
            if n_arg is None:
                start_idx = 1
            else:
                start_idx = max(1, total - n_arg + 1)
            idx = start_idx
            for entry in history_list[start_idx - 1:]:
                sys.stdout.write(f"    {idx}  {entry}\n")
                idx += 1
            sys.stdout.flush()
            os._exit(0)
        else:
            sys.stderr.write(f"{cmd}: command not found\n")
            sys.stderr.flush()
            os._exit(127)
    for i, p in enumerate(parsed):
        if i == 0:
            stdin_fd = None
        else:
            stdin_fd = pipes[i - 1][0]
        if i == n - 1:
            stdout_fd = None
        else:
            stdout_fd = pipes[i][1]
        stdout_fobj = p["stdout_f"]
        stderr_fobj = p["stderr_f"]
        try:
            if p["is_builtin"]:
                pid = os.fork()
                if pid == 0:
                    if stdin_fd is not None:
                        os.dup2(stdin_fd, 0)
                    if stdout_fobj:
                        os.dup2(stdout_fobj.fileno(), 1)
                    elif stdout_fd is not None:
                        os.dup2(stdout_fd, 1)
                    if stderr_fobj:
                        os.dup2(stderr_fobj.fileno(), 2)
                    for (rfd, wfd) in pipes:
                        try:
                            os.close(rfd)
                        except Exception:
                            pass
                        try:
                            os.close(wfd)
                        except Exception:
                            pass
                    run_builtin_child(p["args"][0], p["args"][1:])
                else:
                    child_pids.append(pid)
            else:
                stdin_param = stdin_fd if stdin_fd is not None else None
                if stdout_fobj:
                    stdout_param = stdout_fobj
                elif stdout_fd is not None:
                    stdout_param = stdout_fd
                else:
                    stdout_param = None
                stderr_param = stderr_fobj if stderr_fobj else None
                proc = subprocess.Popen(
                    [p["exec_path"]] + p["args"][1:],
                    stdin=stdin_param,
                    stdout=stdout_param,
                    stderr=stderr_param,
                    close_fds=False
                )
                procs.append(proc)
        except OSError as e:
            write_err(f"Error starting command {p['args'][0]}: {e}", None)
            for fobj in (stdout_fobj, stderr_fobj):
                if fobj:
                    try:
                        fobj.close()
                    except Exception:
                        pass
            for (rfd, wfd) in pipes:
                try:
                    os.close(rfd)
                except Exception:
                    pass
                try:
                    os.close(wfd)
                except Exception:
                    pass
            return
    for (rfd, wfd) in pipes:
        try:
            os.close(rfd)
        except Exception:
            pass
        try:
            os.close(wfd)
        except Exception:
            pass
    for proc in procs:
        try:
            proc.wait()
        except Exception:
            pass
    for pid in child_pids:
        try:
            os.waitpid(pid, 0)
        except Exception:
            pass
    for p in parsed:
        for f in (p.get("stdout_f"), p.get("stderr_f")):
            if f:
                try:
                    f.close()
                except Exception:
                    pass

# --- Main loop --------------------------------------------------------------
def main():
    global last_append_idx
    setup_readline()

    # Load history from HISTFILE at startup (if set)
    histfile = os.environ.get("HISTFILE")
    if histfile:
        try:
            with open(histfile, "r") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line == "":
                        continue
                    history_list.append(line)
                    try:
                        readline.add_history(line)
                    except Exception:
                        pass
        except Exception:
            pass

    try:
        while True:
            try:
                line = input("$ ")
            except EOFError:
                # Save history on exit if HISTFILE is set
                if histfile:
                    try:
                        with open(histfile, "w") as f:
                            for entry in history_list:
                                f.write(entry + "\n")
                    except Exception:
                        pass
                break

            if line is None:
                continue

            if line.strip():
                history_list.append(line)
                try:
                    readline.add_history(line)
                except Exception:
                    pass
                # Keep readline synchronized fully
                readline.clear_history()
                for item in history_list:
                    try:
                        readline.add_history(item)
                    except Exception:
                        pass

            if not line:
                continue

            if '|' in line:
                stage_strings = [s.strip() for s in line.split('|')]
                stages = [parse_command_line(s) for s in stage_strings]
                stages = [s for s in stages if s]
                if not stages:
                    continue
                execute_pipeline(stages)
                continue

            parts = parse_command_line(line)
            if not parts:
                continue

            (cmd_parts, stdout_redir_file, stdout_append,
             stderr_redir_file, stderr_append) = split_redirection(parts)
            if not cmd_parts:
                continue

            if stderr_redir_file:
                try:
                    if stderr_append:
                        open(stderr_redir_file, 'a').close()
                    else:
                        open(stderr_redir_file, 'w').close()
                except Exception as e:
                    sys.stderr.write(f"Error preparing {stderr_redir_file}: {e}\n")
            if stdout_redir_file:
                try:
                    if stdout_append:
                        open(stdout_redir_file, 'a').close()
                    else:
                        open(stdout_redir_file, 'w').close()
                except Exception as e:
                    sys.stderr.write(f"Error preparing {stdout_redir_file}: {e}\n")

            command = cmd_parts[0]
            args = cmd_parts[1:]

            if command == "exit":
                # Save history before exiting
                if histfile:
                    try:
                        with open(histfile, "w") as f:
                            for entry in history_list:
                                f.write(entry + "\n")
                    except Exception:
                        pass
                sys.exit(0)

            elif command == "echo":
                output = " ".join(args)
                if stdout_redir_file:
                    write_out(output, stdout_redir_file, append=stdout_append,
                              stderr_redir_file=stderr_redir_file)
                else:
                    print(output)

            elif command == "type":
                if len(args) == 0:
                    continue
                target = args[0]
                if target in builtins:
                    output = f"{target} is a shell builtin"
                else:
                    executable_path = find_executable(target)
                    if executable_path:
                        output = f"{target} is {executable_path}"
                    else:
                        output = f"{target}: not found"
                if stdout_redir_file:
                    write_out(output, stdout_redir_file, append=stdout_append,
                              stderr_redir_file=stderr_redir_file)
                else:
                    print(output)

            elif command == "pwd":
                output = os.getcwd()
                if stdout_redir_file:
                    write_out(output, stdout_redir_file, append=stdout_append,
                              stderr_redir_file=stderr_redir_file)
                else:
                    print(output)

            elif command == "cd":
                if len(args) == 0:
                    continue
                directory = args[0]
                if directory == "~":
                    home = os.environ.get("HOME")
                    if home and os.path.isdir(home):
                        try:
                            os.chdir(home)
                        except Exception:
                            write_err(f"cd: {directory}: No such file or directory",
                                      stderr_redir_file)
                    else:
                        write_err(f"cd: {directory}: No such file or directory",
                                  stderr_redir_file)
                elif directory.startswith("/"):
                    if os.path.isdir(directory):
                        try:
                            os.chdir(directory)
                        except Exception:
                            write_err(f"cd: {directory}: No such file or directory",
                                      stderr_redir_file)
                    else:
                        write_err(f"cd: {directory}: No such file or directory",
                                  stderr_redir_file)
                else:
                    target_path = os.path.join(os.getcwd(), directory)
                    if os.path.isdir(target_path):
                        try:
                            os.chdir(target_path)
                        except Exception:
                            write_err(f"cd: {directory}: No such file or directory",
                                      stderr_redir_file)
                    else:
                        write_err(f"cd: {directory}: No such file or directory",
                                  stderr_redir_file)

            elif command == "history":
                if args and args[0] == "-r" and len(args) > 1:
                    history_file = args[1]
                    try:
                        with open(history_file, "r") as f:
                            for line in f:
                                line = line.rstrip("\n")
                                if line == "":
                                    continue
                                history_list.append(line)
                                try:
                                    readline.add_history(line)
                                except Exception:
                                    pass
                        # sync readline fully
                        readline.clear_history()
                        for item in history_list:
                            try:
                                readline.add_history(item)
                            except Exception:
                                pass
                    except Exception as e:
                        write_err(f"history -r: Cannot read {history_file}: {e}",
                                  stderr_redir_file)
                    continue

                if args and args[0] == "-w" and len(args) > 1:
                    history_file = args[1]
                    try:
                        with open(history_file, "w") as f:
                            for entry in history_list:
                                f.write(entry + "\n")
                    except Exception as e:
                        write_err(f"history -w: Cannot write {history_file}: {e}",
                                  stderr_redir_file)
                    continue

                if args and args[0] == "-a" and len(args) > 1:
                    history_file = args[1]
                    try:
                        # Append only new commands since last_append_idx
                        with open(history_file, "a") as f:
                            for entry in history_list[last_append_idx:]:
                                f.write(entry + "\n")
                        last_append_idx = len(history_list)
                    except Exception as e:
                        write_err(f"history -a: Cannot append {history_file}: {e}",
                                  stderr_redir_file)
                    continue

                # Print history inline (normal history command)
                n_arg = None
                if args:
                    try:
                        n_arg = int(args[0])
                    except Exception:
                        n_arg = None
                total = len(history_list)
                if n_arg is None:
                    start_idx = 1
                else:
                    start_idx = max(1, total - n_arg + 1)
                idx = start_idx
                if stdout_redir_file:
                    try:
                        mode = 'a' if stdout_append else 'w'
                        with open(stdout_redir_file, mode) as f:
                            for entry in history_list[start_idx - 1:]:
                                f.write(f"    {idx}  {entry}\n")
                                idx += 1
                    except Exception as e:
                        write_err(f"Error writing history: {e}", stderr_redir_file)
                else:
                    for entry in history_list[start_idx - 1:]:
                        print(f"    {idx}  {entry}")
                        idx += 1
            else:
                executable_path = find_executable(command)
                if executable_path:
                    try:
                        stdout_f = (open(stdout_redir_file, 'a' if stdout_append else 'w')
                                    if stdout_redir_file else None)
                        stderr_f = (open(stderr_redir_file, 'a' if stderr_append else 'w')
                                    if stderr_redir_file else None)
                        try:
                            subprocess.run(
                                [command] + args,
                                executable=executable_path,
                                stdout=stdout_f if stdout_f else None,
                                stderr=stderr_f if stderr_f else None,
                            )
                        finally:
                            if stdout_f:
                                stdout_f.close()
                            if stderr_f:
                                stderr_f.close()
                    except Exception as e:
                        write_err(f"Error executing {command}: {e}", stderr_redir_file)
                else:
                    write_err(f"{command}: command not found", stderr_redir_file)
    except KeyboardInterrupt:
        if histfile:
            try:
                with open(histfile, "w") as f:
                    for entry in history_list:
                        f.write(entry + "\n")
            except Exception:
                pass
        sys.exit(0)

if __name__ == "__main__":
    main()