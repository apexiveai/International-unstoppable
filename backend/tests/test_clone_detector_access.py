import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from app.api.clone_detector import _require_trademark_access


class TrademarkAccessTests(unittest.TestCase):
    def test_unassigned_admin_can_use_upload_without_tenant_history(self) -> None:
        admin = SimpleNamespace(is_admin=True, role="ADMIN", tenant_id=None)

        tenant_id = _require_trademark_access(object(), admin)

        self.assertIsNone(tenant_id)

    def test_unassigned_non_admin_cannot_use_trademark_workspace(self) -> None:
        client = SimpleNamespace(is_admin=False, role="USER", tenant_id=None)

        with self.assertRaises(HTTPException) as context:
            _require_trademark_access(object(), client)

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
