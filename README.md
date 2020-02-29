# Update CHANGELOG.md Action

This Action keeps your CHANGELOG.md up to date.

- [Update CHANGELOG.md Action](#update-changelogmd-action)
  - [Getting started](#getting-started)
  - [Examples](#examples)
  - [Variables](#variables)
    - [Inputs](#inputs)
    - [Outputs](#outputs)
  - [Versioning](#versioning)

## Getting started

- Create `CHANGELOG.md` file using [keep a changelog](https://keepachangelog.com/en/1.0.0/) format
- Use the example workflow to create a PR for eash release automatically.
- Use `Keep a changelog` style in your PR notes to automatically include these
  entries to ``CHANGELOG.md` on release

## Examples

```yaml
on:
  release:
    type: published

jobs:
  comment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v1
        with:
          python-version: "3.8"
      - name: Update version
        id: version
        run: |
          echo "GITHUB_REF is a tag you set for the release"
          echo "Your GitHub ref: ${GITHUB_REF}"
          VERSION=`echo "${GITHUB_REF}" | cut -f 3 -d "/"`
          echo "Preparing version ${VERSION}"
          echo "__version__ = \"${VERSION}\"" > __version__.py
          echo "##[set-output name=version;]$(echo ${VERSION})"
      - uses: vemel/update-changelog@0.0.1
        id: changelog
        with:
          version: ${{ steps.version.outputs.version }}
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v2
        with:
          commit-message: Release ${{ steps.version.outputs.version }}
          labels: release, bot
          title: "Release ${{ steps.version.outputs.version }}"
          body: |
            # Release ${{ steps.version.outputs.version }}

            Merge this PR to update your version and changelog!

            ## Included Pull Requests

            ${{ steps.changelog.outputs.pulls_list_md }}
```

## Variables

### Inputs

- `version` - New product version, defaults to env `VERSION`
- `token` - GitHub Token, defaults to env `GITHUB_TOKEN`
- `repository` - GitHub repository name, defaults to env `GITHUB_REPOSITORY`
- `path` - New product version, defaults to `./CHANGELOG.md`

### Outputs

- `pulls_list_md` - Generated included Pull Requests list in MarkDown format

## Versioning

`create_release` version follows [Semantic Versioning](https://semver.org/).
