# Uploading distexer to GitHub and publishing to PyPI and npm

## 0. One-time setup

1. Install **Git**: https://git-scm.com/downloads
2. Create a **GitHub** account: https://github.com/signup
3. Optional, for publishing: a **PyPI** account (https://pypi.org/account/register/) and an **npm** account (https://www.npmjs.com/signup).

The repository is already live at https://github.com/Saharsh000/distexer, and the author and URLs in these files are set to `Saharsh000`:

- `python/pyproject.toml`
- `typescript/package.json`
- `python/src/distexer/renderer/engine.py` and `typescript/src/renderer.ts` (the User-Agent string)
- `LICENSE`

To work on it locally, run `git clone https://github.com/Saharsh000/distexer.git`. Section 1 is only needed if you ever re-create the repository from scratch.

> Check that the name is still free: https://pypi.org/project/distexer/ and https://www.npmjs.com/package/distexer. If either page exists, choose another name, like `distexer-bot`, and change it in `pyproject.toml` and `package.json`.

---

## 1. Push to GitHub

1. Go to https://github.com/new, name the repository **`distexer`**, and set it to **Public**.
   **Don't** tick "Add a README" (you already have one). Click **Create repository**.
2. Open a terminal inside the unzipped `distexer` folder and run:

```bash
git init
git add .
git commit -m "feat: initial release of distexer 0.1.0"
git branch -M main
git remote add origin https://github.com/Saharsh000/distexer.git
git push -u origin main
```

If it asks for a password, use a **Personal Access Token** instead: GitHub → Settings → Developer settings → Personal access tokens → *Fine-grained* → give it access to the repository with Contents: Read & Write. You can also install GitHub Desktop or the `gh` CLI and run `gh auth login`.

After the push, the **Actions** tab automatically runs the CI workflow (Python tests on 3.9–3.13 and the TypeScript build and tests).

Optional: on the repository page, click ⚙️ next to *About* and add the topics `discord`, `latex`, `discord-bot`, `math`, and `python`.

---

## 2. Publish to PyPI (`pip install distexer`)

### Option A: automatic (recommended, no tokens stored anywhere)

1. On PyPI, open **Your account → Publishing → Add a new pending publisher**, then fill in:
   - PyPI project name: `distexer`
   - Owner: `Saharsh000`, Repository: `distexer`
   - Workflow name: `publish.yml`, Environment: `pypi`
2. On GitHub, go to **Settings → Environments → New environment** and name it `pypi`.
3. Create a release (see section 4). The `publish.yml` workflow builds the package and uploads it.

### Option B: manually from your computer

```bash
cd python
python -m pip install --upgrade build twine
python -m build                 # creates dist/*.whl and dist/*.tar.gz
python -m twine upload dist/*   # username: __token__, password: your PyPI API token
```

---

## 3. Publish to npm (`npm i distexer`)

### Option A: automatic

1. On npmjs.com, open your avatar → **Access Tokens → Generate New Token → Automation**.
2. On GitHub, go to **Settings → Secrets and variables → Actions → New repository secret**, name it `NPM_TOKEN`, and paste the token.
3. Create a release (see section 4).

### Option B: manually

```bash
cd typescript
npm install
npm login
npm publish --access public
```

---

## 4. Releasing a new version

1. Bump the version in **both** `python/pyproject.toml` and `typescript/package.json`, plus `__version__` in `python/src/distexer/__init__.py` and `VERSION` in `typescript/src/index.ts`.
2. Commit and push:
   ```bash
   git commit -am "release: v0.1.1"
   git push
   ```
3. On GitHub, go to **Releases → Draft a new release**, create the tag `v0.1.1`, and click **Publish release**.
   The `publish.yml` workflow then uploads the new version to PyPI and npm.

---

## 5. Use it in your own bot right away (without publishing)

```bash
pip install "git+https://github.com/Saharsh000/distexer.git#subdirectory=python"
# or, from the local folder:
pip install -e "./python[all]"
```

For Node, run `npm install ./typescript` from your bot folder after running `npm run build` in `typescript/`.
