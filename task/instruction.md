The directory `/app/data/example/` is a small source tree for a software project. The file `/app/data/example/MANIFEST.sig` maps each included file to an 8-hex-digit integrity marker computed by the project's proprietary marker algorithm. The binary `/app/marker` implements this algorithm — running `/app/marker <file>` prints the 8-hex-digit marker for that file's contents to stdout.

A second, messier source tree is at `/app/data/example_dirty/` with its own `MANIFEST.sig`.

The release process for this project requires producing a `.tar.gz` artifact whose SHA-256 is byte-identical across machines, users, and build times when given the same source tree and epoch. The artifact must satisfy these properties:

- Filesystem metadata in the archive is normalized: all entries have mtime equal to the epoch, owner and group are 0 (root), no user/group names are embedded, and entries are sorted in C locale order (LC_ALL=C).
- Extended attributes, ACLs, and SELinux contexts are stripped.
- The gzip stream carries no embedded mtime or original filename.
- The archive includes a generated `MANIFEST.sig` at its root, containing the correct 8-hex-digit integrity marker for every file in the archive (except itself), with entries sorted in the same C-locale order as the tar entries. Each line has the format `MARKER archive-path` where MARKER is uppercase hex and archive-path is the file's path within the archive. MANIFEST.sig must end with a trailing newline.

The following must be excluded from the release archive entirely: `.git` (including all contents), `.gitignore`, `.gitattributes`, `node_modules`, `*.swp`, `*~`, `.DS_Store`, `._*`, `__pycache__`, `.venv`, `*.pyc`, `Thumbs.db`, `.idea`, `.vscode`, and any pre-existing `MANIFEST.sig` in the source tree.

Source files may arrive with non-canonical line endings, permissions, and metadata. Before archiving, apply these normalizations in order:

1. Convert CRLF line endings to LF on all files whose name matches `*.txt`, `*.md`, `*.cfg`, `*.ini`, `*.sh`, `*.py`, `*.toml`, `*.yaml`, `*.yml`, `*.json`, `*.xml`, `*.html`, `*.css`, `*.js`, `*.c`, `*.h`, `Makefile`, or `version.txt.in`, plus any file whose first 1024 bytes contain no null bytes.

2. If `version.txt.in` exists in the source root, replace exactly the placeholder `@EPOCH@` with the raw decimal epoch integer (e.g. `1700000000`) and include it in the archive as `version.txt`. Apply this AFTER CRLF normalization.

3. Normalize permissions: regular files become `0644`, directories become `0755`, and any file located inside any directory literally named `bin` or whose name ends with `.sh` or `.bash` becomes `0755`. Apply this AFTER template substitution.

Write a self-contained script at `/app/build.sh` that accepts exactly three arguments:

```
/app/build.sh --source <DIR> --output <FILE> --epoch <N>
```

Your script must produce a `.tar.gz` at the output path that satisfies all the properties above for the given source directory and epoch. The verifier will run your script against the shipped examples and against other source trees from the same project — all in the same format and following the same rules, but with different file contents and edge cases. Your script must not invoke `/app/marker` or any other external binary to compute markers, and must not access the network. `/app/build.sh` will be graded exactly as it exists on disk with no separate submission step.

The verifier checks exact SHA-256 equality against a reference build using this exact toolchain: GNU tar with flags `--sort=name`, `--mtime`, `--clamp-mtime`, `--owner=0`, `--group=0`, `--numeric-owner`, `--format=gnu`, `--no-xattrs`, `--no-acls`, and `--no-selinux`, run with `LC_ALL=C`, changing to the staging directory and archiving `.` (producing entries prefixed with `./`), piped through `gzip -n -9`. Directory entries are included. Your script must produce byte-identical output to this exact toolchain.

/app/marker is available during development for probing the marker algorithm, but it will not be present when your script is graded.
