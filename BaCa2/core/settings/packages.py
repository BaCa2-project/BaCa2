from typing import Dict

import baca2PackageManager as pkg

PACKAGES_DIR = BASE_DIR / 'packages_source'   # noqa: F821
_auto_create_dirs.add_dir(PACKAGES_DIR)   # noqa: F821
UPLOAD_DIR = BASE_DIR / 'uploads'   # noqa: F821
_auto_create_dirs.add_dir(UPLOAD_DIR)   # noqa: F821
TASK_DESCRIPTIONS_DIR = BASE_DIR / 'task_descriptions'   # noqa: F821
_auto_create_dirs.add_dir(TASK_DESCRIPTIONS_DIR)   # noqa: F821
ATTACHMENTS_DIR = BASE_DIR / 'attachments'  # noqa: F821
_auto_create_dirs.add_dir(ATTACHMENTS_DIR)  # noqa: F821

pkg.set_base_dir(PACKAGES_DIR)
pkg.add_supported_extensions('cpp')

PACKAGES: Dict[str, pkg.Package] = {}
