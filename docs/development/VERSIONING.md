# Versioning

Royal Blackwater Fleet uses `MAJOR.MINOR.PATCH`. The highest applicable change class
determines the next version; lower positions reset when a higher position is incremented.

| Class | Form | Use for | Example from `1.0.0` |
| --- | --- | --- | --- |
| Patch | `x.y.Z` | hotfixes, bug, security, and documentation corrections, plus compatible internal improvements | `1.0.1` |
| Minor | `x.Y.0` | backward-compatible features, new optional API fields, and additive functions or migrations | `1.1.0` |
| Major | `X.0.0` | incompatible contracts, configurations, or migrations, plus explicitly large product expansions | `2.0.0` |

A feature that also contains patch-level work remains a minor release; an incompatible change
remains a major release. Size alone does not make a change incompatible, but it may justify a
major jump for an expansion deliberately planned as a product milestone.

Every state intended for rollout through the update mechanism receives a new, higher release
version. A deployable bug fix therefore increments at least `0.0.1`; an already-activated
version number is not reused even for small follow-up patches.

Before every release:

1. Determine the change class from the complete release contents.
2. Verify the next number with `bash .agents/scripts/next-version.sh patch|minor|major`.
3. Change `VERSION` plus Maven, frontend, and API contract versions together; then update
   generated references through their generator.
4. Run the complete release gate, inspect the diff/status, commit the verified tree, push the
   exact release commit, and build/deploy only from that commit.

`patches/` is deliberately a local transfer/download workspace rather than a release archive.
Patch payloads are ignored by Git and must not be committed; only `patches/.gitkeep` keeps the
directory in fresh clones. If historical patch payloads were already tracked, remove them from
the index with `git rm --cached` while leaving the local files in place. The source commits and
`CHANGELOG.md` are the authoritative history, avoiding a second patch-based history that can drift
from the code it once modified.

Before committing a release, verify the four version sources agree and that no local patch payload
is staged:

```bash
cat VERSION
mvn -q -f spring-api/pom.xml help:evaluate -Dexpression=project.version -DforceStdout
node -p "require('./frontend/package.json').version"
python3 - <<'PY'
import json
print(json.load(open('openapi/source/root.json'))['info']['version'])
PY
git status --short
```

Activated or otherwise published release versions and their artifacts are immutable and never
reused. Pre-releases may use SemVer suffixes such as `-rc.1`; production artifacts keep the
three-part version from `VERSION`.
