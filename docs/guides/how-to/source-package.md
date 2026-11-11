# Build and verify a source package

Use Python 3.10+, Git, and tar from the repository root. The packager checks an
explicit file set; a working Git checkout contains extra metadata and is not a
valid input. The commands below export committed files without `.git`.
Uncommitted changes are not included. Review and commit the intended candidate,
including matching sizes and hashes in `SOURCE-MANIFEST.json`, before exporting.
Refresh the manifest from the committed file list with
`python3 -S -B -m tools.refresh_manifest`, then commit it.

```sh
package_work=$(mktemp -d)
mkdir "$package_work/source"
git archive HEAD | tar -x -C "$package_work/source"
python3 -S -B "$package_work/source/tools/package_source.py" "$package_work/first.zip"
python3 -S -B "$package_work/source/tools/package_source.py" "$package_work/second.zip"
cmp "$package_work/first.zip" "$package_work/second.zip"
python3 -S -B -m zipfile -e "$package_work/first.zip" "$package_work/extracted"
python3 -S -B "$package_work/extracted/foundation-math/tools/package_source.py" "$package_work/extracted.zip"
cmp "$package_work/first.zip" "$package_work/extracted.zip"
```

Each packaging invocation checks path containment, symlinks, sizes, and SHA-256
pins before creating a fresh output outside the source tree. Existing archive
paths are refused. Community files excluded by `tools/package_source.py` are not
shipped, even though the Git export contains them. The manifest itself is shipped
without a recursive self-pin. These checks verify selected bytes, not publication
approval or mathematical acceptance.

Run the source tests separately:

```sh
python3 -S -B -m unittest discover -s tests -t .
python3 -S -B -O -m unittest discover -s tests -t .
```

Record the candidate SHA (`git rev-parse HEAD`), actual environment, commands,
limits, exits, failures, and omitted checks. Keep the temporary directory as local
evidence outside the checkout. See the [release checklist](../../RELEASE-CHECKLIST.md)
for independent review and promotion requirements.
