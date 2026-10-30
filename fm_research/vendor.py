"""Load the local pinned v014 character catalog; never fetch external data."""
import hashlib
from pathlib import Path
import sys

VENDOR = next(p / 'vendor/foundation-math-v014' for p in Path(__file__).parents
              if (p / 'vendor/foundation-math-v014').is_dir())
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))
from character_ring.contract import CATALOG_SHA256


def catalog_sha256():
    """Recheck the catalog bytes against the vendor contract on every call."""
    digest = hashlib.sha256((VENDOR / 'character_ring/catalog.json').read_bytes()).hexdigest()
    if digest != CATALOG_SHA256:
        raise RuntimeError('Pinned character catalog SHA256 mismatch')
    return digest


catalog_sha256()
