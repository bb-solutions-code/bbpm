# bbpm

**BBScript Package Manager** — install block packages (such as [Foblox](https://github.com/bb-solutions-code/foblox)) into a project under `.bbpm/`. Run `.bbs` graphs with **`bbscript run`** (from [bbscript](https://github.com/bb-solutions-code/bbscript)) so package blocks register alongside built-in BBScript blocks.

`bbpm` depends on **[bbscript](https://github.com/bb-solutions-code/bbscript)** (`>=0.2.0`, [PyPI](https://pypi.org/project/bbscript/)); installing `bbpm` pulls in the runtime. **Foblox** is not bundled in the wheel; use `bbpm init` (default) or `bbpm fetch` to clone it from Git.

## Requirements

- Python 3.10+
- **Git** on `PATH` when using `https://` or `git@` sources (for `git clone`)

## Bundled Foblox (installers / env)

Frozen bundles and installers may ship Foblox next to the executable; **`bbscript run`** loads it from the PyInstaller bundle or from **`BBSCRIPT_BUNDLED_PACKAGES`** (implemented in `bbscript.bundled`, no `bbpm` required). When `bbpm` is installed, `prepare_runtime` also loads packages from `.bbpm/`. For local testing without a project `.bbpm`, you can point to a package root:

- `BBSCRIPT_BUNDLED_PACKAGES` — one or more directories (separator: `;` on Windows, `:` on Unix), each a BBScript package root containing a root `.bbpackage` manifest (same layout as Foblox).

See [packaging/README.md](https://github.com/bb-solutions-code/bbscript/blob/main/packaging/README.md) in the **bbscript** repository for frozen installer / PyInstaller build instructions.

## Install

```bash
pip install bbpm
```

Editable install next to a local `bbscript` checkout (monorepo):

```bash
pip install -e path/to/bbscript -e path/to/bbpm
```

## Quick start

From your BBScript project directory:

```bash
bbpm init
```

This creates `.bbpm/bbpm.json` and, unless you pass `--no-foblox`, fetches the default Foblox package from `https://github.com/bb-solutions-code/foblox.git` (branch/tag: `--ref`, default `main`).

Add another package from Git or a local folder that contains a root `.bbpackage` manifest:

```bash
bbpm fetch https://github.com/bb-solutions-code/foblox.git
bbpm fetch ./my-local-package
```

Run a script with all installed packages loaded:

```bash
bbscript run workflow.bbs
```

If `.bbpm` lives above the `.bbs` file, discovery walks parents from the script path; or pass `--path` to the project root.

## CLI

| Command | Description |
|--------|-------------|
| `bbpm init [--path DIR] [--no-foblox] [--ref REF]` | Create `.bbpm/bbpm.json`; optionally fetch Foblox |
| `bbpm fetch <url\|path> [--path DIR] [--ref REF]` | Install a package (Git URL or local directory) under `.bbpm/packages/<name>/` |
| `bbpm reset [--path DIR]` | Delete `.bbpm/packages/*`, keep `bbpm.json`, re-fetch every listed package |
| `bbpm cleanup <name> [--path DIR]` | Remove one package from the manifest and from disk |
| `bbpm list [--path DIR]` | List packages in the manifest |

You can also run the CLI as a module: `python -m bbpm <command> ...`.

## Manifest

`.bbpm/bbpm.json` (schema version `1`) lists packages with `name`, `source` (`git` with `url`/`ref` or `local` with `path`), and install path `packages/<name>`.

## Related projects

- **[bbscript](https://github.com/bb-solutions-code/bbscript)** — core graph runtime and `bbscript` CLI (`bbscript run` executes `.bbs` with optional package loading when `bbpm` is installed).
- **[foblox](https://github.com/bb-solutions-code/foblox)** — default foundation-blocks package (e.g. `variable`, `calculate`, `say`) fetched by `bbpm init`.

## Contributing

1. Open a branch for your change.
2. Use an editable install with **[bbscript](https://github.com/bb-solutions-code/bbscript)** available (see **Install**), then add or update tests under `tests/`.
3. From the repository root, run `python -m pytest -q`.
4. Keep CLI behavior, `.bbpm/bbpm.json` schema, and user-facing messages consistent with existing commands; prefer English for docs and help text.

## License

Apache-2.0 — see [LICENSE](LICENSE).
