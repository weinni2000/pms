# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from pathlib import Path

from odoo.tests import TransactionCase

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_NAME = "pms_application"


class TestPmsApplication(TransactionCase):
    def test_depends_lists_the_modules_of_the_repository(self):
        """The application depends on exactly the modules of the repository."""
        if not (REPO_ROOT / "pms_base" / "__manifest__.py").is_file():
            self.skipTest("The repository checkout is not next to the module.")

        repo_modules = {
            path.name
            for path in REPO_ROOT.iterdir()
            if (path / "__manifest__.py").is_file()
        }
        repo_modules.discard(MODULE_NAME)

        module_id = self.env["ir.module.module"].search([("name", "=", MODULE_NAME)])
        depends = set(module_id.dependencies_id.mapped("name"))

        missing = repo_modules - depends
        self.assertFalse(
            missing,
            f"Modules of the repository that are not installed: {sorted(missing)}",
        )
        stale = depends - repo_modules
        self.assertFalse(
            stale,
            f"Dependencies that are not modules of the repository: {sorted(stale)}",
        )
