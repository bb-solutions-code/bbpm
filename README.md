# bbpm

**BBScript Package Manager** — install block packages (such as [Foblox](https://github.com/bb-solutions-code/foblox)) into a project, then run `.bbs` graphs with `bbpm run` so package blocks are registered alongside built-in BBScript blocks.

`bbpm` depends on **[bbscript](https://pypi.org/project/bbscript/)** (`>=0.2.0`); installing `bbpm` pulls in the runtime. **Foblox** is not bundled in the wheel; use `bbpm init` (default) or `bbpm fetch` to clone it from Git.

## Requirements

- Python 3.10+
- **Git** on `PATH` when using `https://` or `git@` sources (for `git clone`)

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
bbpm run workflow.bbs
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
| `bbpm run <file.bbs> [--path DIR] ...` | Load builtins + packages, execute the document |

You can also run the CLI as a module: `python -m bbpm <command> ...`.

## Manifest

`.bbpm/bbpm.json` (schema version `1`) lists packages with `name`, `source` (`git` with `url`/`ref` or `local` with `path`), and install path `packages/<name>`.

## License

Apache-2.0 — see [LICENSE](LICENSE).
