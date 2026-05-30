# Example Packed Output

This is a minimal example of the Markdown artifact written by:

```bash
foldermix pack . --out context.md
```

````markdown
# FolderPack Context

- **Root**: `/path/to/project`
- **Files**: 2
- **Total bytes**: 58

## Table of Contents

- [README.md](#readmemd)
- [src/app.py](#srcapppy)

---

## README.md {#readmemd}

```markdown
# Example Project
```

---

## src/app.py {#srcapppy}

```python
print("hello")
```
````

Real bundles include one section per included file, plus metadata controlled by the selected output
format and config.
