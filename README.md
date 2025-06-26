# scriptpy: Python for Scripting

`scriptpy` is a Python extension that simplifies scripting by seamlessly integrating shell commands and introducing a powerful piping syntax designed for working with lists and iterables. It aims to make
common scripting tasks more concise and readable.

## Key Features

*   **Shell Command Execution:** Execute shell commands directly within your Python code using the `$(...)` syntax. The output of the command is captured as a string.
*   **Piping for Lists/Iterables:** Chain operations together using the `|` operator to apply a function or attribute access to *each element* in a list or iterable.
*   **Attribute Access Piping:** Access attributes and call methods on elements in a list/iterable using the `|.attribute` syntax.

##  Syntax sugar
### tldr
* `$(command)` = run shell command and return str (`subprocess.run(command).stdout.read()`). NOTE that `$(ls)` will not work, as `ls` is not defined. wrap it in string/varible

* `left | right` = `[right(x) for x in left]`
* `left |.right` (note the dot) = `[x.<right> for x in left]`
* `left |.right(arg1,arg2)` = `[x.<right>(arg1,arg2) for x in left]`
* auto import of qualified functions, so `os.path.basename` work without importing os (and any other available module too)

### Shell Command Execution

```python
# Execute a shell command and capture the output
output = $("ls -l")
print(output)
```

### Piping
The `|` operator applies the right-hand side operation to each element in the list or iterable on the left-hand side. The right-hand side can be:

* A function: The function is called with each element as its argument, and the result is a new list.
* .attribute: Accesses the attribute of each element, and the result is a new list of attributes.
* .method(args): Calls the method on each element with the given arguments, and the result is a new list of the return values.

## Designed for interactive use
scriptPy is designed for interactive use, that means, like python interapeter, it will print the last value of the line if there is one. for example `[1,2,3]` will actually output `[1,2,3]`, and `a=[1,2,3]` wont.

if your code is not syntaxly closed `{([`, scriptpy will try to complete it for you, so code like `[1,2,3` will still output `[1,2,3]`
