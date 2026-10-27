# Mathematical source binding, version 2

The `kernel_source_sha256` field is a source-byte identity, not a signature or a
proof. Version 2 binds the explicitly selected mathematical runtime source set:

- Eight `fm_research` modules: initialization, CLI, field arithmetic, formal
  split-bundle API, problem/check/accounting, rank certificates, character API,
  and catalog loader.
- Nine selected v0.14 files: the character package's initialization, contract,
  producer, independent verifier and catalog; and the split-bundle package's
  initialization, contract, producer and independent verifier.

The retained independent verifiers are included conservatively even when the
particular check does not invoke them. `_SOURCE_FILES` in `fm_research/problem.py`
is the explicit path list. The list itself is bound because `problem.py` is bound.
Mapper code, tests, docs, archives and unselected tools do not enter this math
fingerprint. The distribution manifest independently binds every packaged file.

## Construction and gate behavior

First, the existing catalog pin is checked. The SHA-256 state is initialized with
the UTF-8 bytes `fm-research-source/2` followed by a NUL byte. For each selected
path in lexical order, the state receives its repository-relative UTF-8 name,
a NUL byte, and the 32-byte SHA-256 digest of that file's bytes. No host path,
mtime or directory enumeration order enters the identity.

A changed selected Python source makes an older receipt fail the current source
comparison and leaves that computed claim `unchecked`. A missing selected file
raises an I/O error. A changed catalog retains its previous explicit integrity
error rather than silently accepting another table. No kernel algorithm,
expectation comparison, dependency traversal, conditional `certified` behavior,
or `cited`/`argued` treatment changed.

Existing receipts remain bound to their historical bytes and source format.
They are not rewritten, relabeled or automatically promoted. An authorized fresh
check can produce a new receipt; a file copy cannot substitute for that check.

## Narrow baseline observation

In public baseline `e492473632e413504ffe450a604fd4eb33e2a559`, the source hash
covered research modules and the catalog but omitted selected vendor
implementations. In a disposable copy, appending an inert comment to the
character producer changed that file's hash while leaving the old fingerprint
and a fresh synthetic receipt's status unchanged. This demonstrates an omitted
source-identity dependency only. It is not evidence of an exploit, an incorrect
mathematical result, or altered kernel behavior.

## Regression scope and limits

Six new synthetic test methods check the 17-file closure, changed Python sources,
catalog rejection, missing files, deterministic ordering/relocation, legacy
framing rejection and exclusion of unrelated material. Source mutations happen
only in disposable copies; mutated files are neither imported nor executed.

This hashes selected files on disk when requested. It does not authenticate
in-memory modules, detect arbitrary monkey-patching, bind the Python executable
or standard library, provide atomic snapshots across concurrent edits, establish
reviewer honesty, or prove the intended mathematical statement. Run trusted,
stable source trees; hashes alone are not a hostile-code isolation boundary.
