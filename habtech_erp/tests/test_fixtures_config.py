"""Guards for the customization workflow (see docs/decisions/0003 in the workspace repo).

Every fixture in hooks.py must be filtered to HABTech records, so that
`export-fixtures` can never pull core frappe/erpnext/hrms records into this app.
"""

import json
import os

import frappe
from frappe.tests import UnitTestCase

from habtech_erp import hooks

MODULE = "HABTech ERP"


def _filters(fixture: dict) -> list:
	return list(fixture.get("filters") or []) + list(fixture.get("or_filters") or [])


class TestFixturesConfig(UnitTestCase):
	def test_every_fixture_is_filtered(self):
		for fixture in hooks.fixtures:
			self.assertIsInstance(fixture, dict, f"unfiltered fixture: {fixture!r}")
			doctype = fixture.get("dt") or fixture.get("doctype")
			filters = _filters(fixture)
			self.assertTrue(filters, f"{doctype} fixture has no filters")
			restricted = any(
				(f[0] == "module" and f[1] == "=" and f[2] == MODULE)
				or (f[0] == "name" and f[1] == "like" and str(f[2]).startswith("HABTech"))
				for f in filters
			)
			self.assertTrue(restricted, f"{doctype} fixture is not restricted to {MODULE}")

	def test_exported_fixture_files_belong_to_module(self):
		fixtures_dir = frappe.get_app_path("habtech_erp", "fixtures")
		if not os.path.isdir(fixtures_dir):
			return
		for fname in sorted(os.listdir(fixtures_dir)):
			if not fname.endswith(".json"):
				continue
			with open(os.path.join(fixtures_dir, fname)) as f:
				records = json.load(f)
			for record in records:
				if "module" in record:
					self.assertEqual(record["module"], MODULE, f"{fname}: {record.get('name')}")
				else:
					self.assertTrue(
						str(record.get("name", "")).startswith("HABTech"), f"{fname}: {record.get('name')}"
					)
