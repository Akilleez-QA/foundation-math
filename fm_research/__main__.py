"""Offline standalone ProblemSpec checks."""
import argparse
import json
from pathlib import Path
from .problem import gate, load_spec, run_check


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    child = sub.add_parser('check')
    child.add_argument('spec')
    child.add_argument('--claim')
    child.add_argument('--evidence-out')
    args = parser.parse_args()
    try:
        spec = load_spec(args.spec)
        claims = {c['id']: c for c in spec['claims']}
        selected = [args.claim] if args.claim else list(claims)
        needed = set(selected)
        def include(cid):
            for dep in claims[cid]['depends_on']:
                if dep not in needed:
                    needed.add(dep)
                    include(dep)
        for cid in selected:
            include(cid)
        evidence = {cid: run_check(claims[cid]) for cid in needed if claims[cid]['kind'] == 'computed'}
        statuses = gate(spec, evidence)
        if args.evidence_out:
            Path(args.evidence_out).write_text(''.join(json.dumps(evidence[cid].to_dict()) + '\n' for cid in claims if cid in evidence))
        for cid in selected:
            print(json.dumps(dict(claim_id=cid, status=statuses[cid], evidence=evidence[cid].to_dict() if cid in evidence else None)))
        computed = [cid for cid in selected if claims[cid]['kind'] == 'computed']
        return int(not computed or any(statuses[cid] != 'certified' for cid in computed))
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        parser.exit(2, f'{type(exc).__name__}: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
