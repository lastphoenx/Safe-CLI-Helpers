# safe-ops-cli

Two small but robust CLI helpers for Linux admins:

- **fsx** – safe file/folder operations (default **DRY-RUN**, explicit `--execute` to apply).
- **gix** – safer everyday Git workflow (branches, push/pull, release) with confirmations and guard rails.

## Quick install

```bash
git clone git@github.com:<USER>/safe-ops-cli.git
cd safe-ops-cli
sudo install -m 0755 tools/fsx.py /usr/local/bin/fsx
sudo install -m 0755 tools/gix.py /usr/local/bin/gix
