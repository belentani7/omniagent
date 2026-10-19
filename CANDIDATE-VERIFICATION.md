# OmniAgent v2.1 — candidate verification (NOT RELEASED)

Source: Google Drive archive `12-omniagent-v2.1-VERIFICADO.tar.gz`
Source SHA-256: `611542c21e68da64965a979b3bf9ad49404f94ef0a16091c08e6dc343cfb1912`

## Verification performed on 2026-10-19
- Archive safety: 65 entries, 220,066 bytes uncompressed, no absolute/traversal paths or symlinks. Archive contents were inspected before running tests; nothing was executed from the archive as a deployment script.
- `python -m compileall -q omniagent tests tools`: passed.
- `python -m pytest -q`: 76 passed.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: 30 files already formatted.
- `python tools/check_web_syntax.py`: all listed JS/inline scripts passed; ecosystem copies matched.
- Installed the local CLI and checked `oa --help` and `oa run --dry-run` in Catalan. The dry run explicitly made no provider/network call.

## Publication boundary
The archive is materially different from the currently public GitHub `main` snapshot (commit `8248ba986d860d70fe3e03910b4c741651eccd6c`). It is preserved as a candidate, not merged over the live repo. GitHub write access was unavailable; no source was pushed.

The Vercel static project was updated separately from the existing public `main`: its root directory is now `docs`; staging checks returned HTTP 200 for `/`, `/index.html`, `/site.css`, and `/site.js`; production deployment completed READY/PROMOTED and the same production paths returned HTTP 200. This deployment does not include the archive's v2.1 code changes.

This is a tested candidate, not a release guarantee. Provider model availability/pricing, real credentials, live provider calls, and visual QA on diverse devices were not tested.
