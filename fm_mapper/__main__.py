"""Local-only CLI. Exit zero means mapping/rendering completed, not claim acceptance."""
import argparse
import json
from pathlib import Path
import sys
from .core import SchemaError, load_bundle, read_artifacts, map_evidence, render_paper


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle', type=Path)
    p.add_argument('--artifact-root', type=Path)
    p.add_argument('--json-out', type=Path)
    p.add_argument('--paper-out', type=Path)
    args = p.parse_args(argv)
    try:
        b = load_bundle(args.bundle)
        data = read_artifacts(b, args.artifact_root or args.bundle.parent)
        result = map_evidence(b, data)
        raw = json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        sources = {args.bundle.resolve()} | {(args.artifact_root or args.bundle.parent).joinpath(a['path']).resolve() for a in b['artifacts']}
        destinations = [x.resolve() for x in (args.json_out, args.paper_out) if x is not None]
        if len(destinations) != len(set(destinations)) or any(x in sources for x in destinations):
            raise SchemaError('Output path would replace an input or duplicate another output')
        for path in (args.json_out, args.paper_out):
            if path is not None and path.exists():
                raise SchemaError('Output already exists; choose a fresh path')
        for path, data in [(args.json_out, raw), (args.paper_out, render_paper(b, data))]:
            if path is not None:
                with path.open('x', encoding='utf-8') as f:
                    f.write(data)
        if args.json_out is None:
            sys.stdout.write(raw)
        else:
            print(json.dumps({'delivery': 'mapped_and_rendered' if args.paper_out else 'mapped', 'scientific_acceptance': False, 'summary': result['summary']}, sort_keys=True))
        return 0
    except (SchemaError, OSError, ValueError, TypeError, RecursionError) as e:
        print('Mapper error (not a scientific refutation): ' + str(e), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
