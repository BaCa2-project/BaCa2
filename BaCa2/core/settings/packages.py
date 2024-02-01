from typing import Dict

import baca2PackageManager as pkg

PACKAGES_DIR = BASE_DIR / 'packages_source'
_auto_create_dirs.add_dir(PACKAGES_DIR)

pkg.set_base_dir(PACKAGES_DIR)
pkg.add_supported_extensions('cpp')

PACKAGES: Dict[str, pkg.Package] = {}

