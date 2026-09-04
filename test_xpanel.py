import tempfile
import unittest
from pathlib import Path

import xpanel


class XPanelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "accounts.db"
        self.db = xpanel.connect(self.db_path)

    def tearDown(self): self.db.close(); self.tmp.cleanup()

    def test_clean_handle(self):
        self.assertEqual(xpanel.clean_handle(" @Conta_1 "), "Conta_1")
        with self.assertRaises(ValueError): xpanel.clean_handle("bad-name")

    def test_add_and_status(self):
        args = type("Args", (), {"handle": "conta", "name": "Conta", "owner": "Time", "notes": "", "status": "ativa"})()
        xpanel.add(self.db, args)
        update = type("Args", (), {"handle": "conta", "status": "pausada"})()
        xpanel.set_status(self.db, update)
        self.assertEqual(xpanel.rows(self.db)[0]["status"], "pausada")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], 2)


if __name__ == "__main__": unittest.main()
