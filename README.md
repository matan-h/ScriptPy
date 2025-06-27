# scriptpy: Python for Scripting

`scriptpy` is a Python extension that simplifies scripting by seamlessly integrating shell commands and introducing a powerful piping syntax for working with lists and iterables. It aims to make live scripting easier.

## Key Features

* **Shell Command Execution**: Execute shell commands directly within your Python code using the `$(...)` syntax. The output of the command is captured as a string.
* **Piping for Lists/Iterables**: Chain operations using the `|` operator to apply a function or attribute access to *each element* in a list or iterable.
* **Attribute Access Piping**: Access attributes and call methods on elements in a list or iterable using the `|.attribute` syntax.

## Syntax Sugar

### TL;DR

* `$(command)` Run a shell command and return its output as a string (`subprocess.run(command).stdout.read()`).
  **Note**: `$(ls)` will not work, as `ls` is not defined. Wrap it in a string or variable: `$("ls")`.

* `left | right` = `[right(x) for x in left]`

* `left |.right` = `[x.right for x in left]`

* `left |.right(arg1, arg2)` = `[x.right(arg1, arg2) for x in left]`

* Auto-import of fully-qualified functions: for example, `os.path.basename` works without importing `os` (applies to all modules too)

### Shell Command Execution

```python
# Execute a shell command and capture the output
output = $("ls -l")
print(output)
```

### Piping

The `|` operator applies the right-hand-side operation to each element in the list or iterable on the left-hand side. The right-hand side can be:

* A **function**: The function is called with each element as its argument, and the result is a new list.
* An **attribute**: Accesses the attribute of each element, resulting in a new list of those attributes.
* A **method call**: Calls the method on each element with the given arguments, resulting in a list of the return values.

## Designed for Interactive Use

`scriptpy` is designed for interactive use. Like the Python interpreter, it prints the last value of the line if there is one. For example, entering `[1, 2, 3]` will output `[1, 2, 3]`, whereas `a = [1, 2, 3]` will not print anything.

If your code is not syntactically complete (e.g., ends with an open bracket `{`, `(`, or `[`), `scriptpy` will try to auto-complete it for you. For instance, entering `[1, 2, 3` will still result in `[1, 2, 3]`.

## Installation
To install, use:
```bash
pip install scriptpy
```

## Usage
Use from the command line:
```bash
scriptpy '<code>'
scriptpy -s '<script-filename>'
cat anything | scriptpy -d- "<code>" # -d is for data file, -d - is to make the "data" var stdin.read().
# for example:
curl -s 'https://api.github.com/repos/matan-h/Transfer/commits'|scriptpy -d- '"\n".join(json.loads(data) | .get("commit") | .get("message"))' # print all commits from Transfer.
```
> if you want a more complete and interactive way to use this library check out my project `f7`, which is a GUI to manipulate your selection. (you select, press f7 key, then enter a scriptpy expression to change that selection.), also it supports many features such as prefixes and modes
> this originally was built to use in f7.

## Usage as a python library
```python
from scriptpy import custom_eval
# custom_eval(src: str, globals_: dict | None = None,verbose=False)
res:list = custom_eval(
  src='numbers | str |.zfill(3)',
  globals_={"numbers":list(range(40))},verbose=False)

print(res) # [000,001,002,...]
```
## Contributing

Contributions are welcome! If you'd like to suggest a feature, report a bug or an error, or propose any improvements, please  [open an issue](https://github.com/matan-h/scriptpy/issues).

If you'd like to support the project, you can [buy me a coffee](https://www.buymeacoffee.com/matanh) ☕️. Your support helps keep development going and is greatly appreciated.