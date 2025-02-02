import json

from aleph.core import db, mail
from aleph.settings import SETTINGS
from aleph.model import Role
from aleph.tests.util import TestCase
from aleph.tests.factories.models import RoleFactory


class RolesApiTestCase(TestCase):
    def setUp(self):
        super(RolesApiTestCase, self).setUp()
        self.create_user(foreign_id="user_1")
        self.create_user(foreign_id="user_2")
        self.rolex = self.create_user(foreign_id="user_3")

    def test_suggest(self):
        res = self.client.get("/api/2/roles/_suggest")
        assert res.status_code == 403, res

        _, headers = self.login(foreign_id="jane", email="jane.doe@example.org")
        john, _ = self.login(foreign_id="john", email="john.doe@example.org")

        res = self.client.get(
            "/api/2/roles/_suggest",
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json["total"] == 0
        assert res.json["results"] == []

        res = self.client.get(
            "/api/2/roles/_suggest",
            query_string={"prefix": "john"},
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json["total"] == 0
        assert res.json["results"] == []

        res = self.client.get(
            "/api/2/roles/_suggest",
            query_string={"prefix": "john.doe@example.org"},
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json["total"] == 1
        assert len(res.json["results"]) == 1
        assert res.json["results"][0]["id"] == str(john.id)

        res = self.client.get(
            "/api/2/roles/_suggest",
            query_string={"prefix": "JOHN.DOE@EXAMPLE.org"},
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json["total"] == 1
        assert len(res.json["results"]) == 1
        assert res.json["results"][0]["id"] == str(john.id)

        res = self.client.get(
            "/api/2/roles/_suggest",
            query_string={"prefix": "john.doe@example.org", "exclude:id": john.id},
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json["total"] == 0
        assert len(res.json["results"]) == 0

    def test_view(self):
        res = self.client.get("/api/2/roles/%s" % self.rolex)
        assert res.status_code == 404, res
        role, headers = self.login()
        res = self.client.get("/api/2/roles/%s" % role.id, headers=headers)
        assert res.status_code == 200, res
        # assert res.json['total'] >= 6, res.json

    def test_update(self):
        res = self.client.post("/api/2/roles/%s" % self.rolex)
        assert res.status_code == 404, res
        role, headers = self.login()
        url = "/api/2/roles/%s" % role.id
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, res.json
        data = res.json
        data["name"] = "John Doe"
        res = self.client.post(
            url, data=json.dumps(data), headers=headers, content_type="application/json"
        )
        assert res.status_code == 200, res.json
        assert res.json["name"] == data["name"], res.json

        data["name"] = ""
        res = self.client.post(
            url, data=json.dumps(data), headers=headers, content_type="application/json"
        )
        assert res.status_code == 400, res

    def test_code_when_no_email(self):
        SETTINGS.PASSWORD_LOGIN = True
        with mail.record_messages() as outbox:
            res = self.client.post("/api/2/roles/code")
            assert res.status_code == 400, res
            assert len(outbox) == 0, outbox

    def test_code_has_email(self):
        SETTINGS.PASSWORD_LOGIN = True
        email = self.fake.email()
        with mail.record_messages() as outbox:
            res = self.client.post("/api/2/roles/code", data=dict(email=email))
            assert res.status_code == 200, res
            assert len(outbox) == 1, outbox
            assert email in outbox[0].recipients, outbox[0]

    def test_create_no_payload(self):
        SETTINGS.PASSWORD_LOGIN = True
        res = self.client.post("/api/2/roles")
        assert res.status_code == 400, res

    def test_create_no_pass(self):
        SETTINGS.PASSWORD_LOGIN = True
        payload = dict(password="", code=self.fake.md5())
        res = self.client.post("/api/2/roles", data=payload)
        assert res.status_code == 400, res

    def test_create_no_code(self):
        SETTINGS.PASSWORD_LOGIN = True
        payload = dict(password=self.fake.password(), code="")
        res = self.client.post("/api/2/roles", data=payload)
        assert res.status_code == 400, res

    def test_create_registration_disabled(self):
        SETTINGS.PASSWORD_LOGIN = False
        email = self.fake.email()
        payload = dict(password=self.fake.password(), code=Role.SIGNATURE.dumps(email))
        res = self.client.post("/api/2/roles", data=payload)
        assert res.status_code == 403, res

    def test_create_short_pass(self):
        SETTINGS.PASSWORD_LOGIN = True
        email = self.fake.email()
        payload = dict(
            password=self.fake.password()[:3], code=Role.SIGNATURE.dumps(email)
        )
        res = self.client.post("/api/2/roles", data=payload)
        assert res.status_code == 400, res

    def test_create_bad_code(self):
        SETTINGS.PASSWORD_LOGIN = True
        payload = dict(password=self.fake.password(), code="asdasda")
        res = self.client.post("/api/2/roles", data=payload)
        assert res.status_code == 400, res

    def test_create_success(self):
        SETTINGS.PASSWORD_LOGIN = True
        email = self.fake.email()
        name = self.fake.name()
        password = self.fake.password()
        payload = dict(name=name, password=password, code=Role.SIGNATURE.dumps(email))
        res = self.client.post("/api/2/roles", data=payload)
        db.session.close()

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json.get("email"), email)

        role = Role.by_email(email)
        self.assertIsNotNone(role)
        self.assertTrue(role.check_password(password))
        self.assertEqual(role.name, payload["name"])

    def test_create_on_existing_email(self):
        SETTINGS.PASSWORD_LOGIN = True
        email = self.fake.email()
        password = self.fake.password()
        payload = dict(
            email=email,
            name=self.fake.name(),
            password=password,
            code=Role.SIGNATURE.dumps(email),
        )

        RoleFactory.create(email=email)
        res = self.client.post("/api/2/roles", data=payload)

        self.assertEqual(res.status_code, 409)
