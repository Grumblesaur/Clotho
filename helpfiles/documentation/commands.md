# Commands

Clotho has two commands.

- `docs` will provide documentation information for a provided topic, or the quickstart if no matching topic can be found.
- `roll` parses a Dicelang expression and returns a result, possibly creating, changing, or deleting persistent variables in the process.

## Syntax:

The following commands must be preceded by the prefix (default `+`) in your Clotho instance's `clotho.toml` file.
Clotho's  Discord presence message will usually indicate the prefix.

```
roll dicelang_expression

docs topic
```
