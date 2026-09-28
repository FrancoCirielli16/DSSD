from app.core.config import get_settings
from app.models import Rol, Usuario
from app.seed import DEMO_USERS
from app.services import bonita_users


class FakeBonita:
    def __init__(self):
        self.users = {}
        self.roles = {}
        self.groups = {}
        self.memberships = []
        self.profiles = {"User": {"id": "profile-user"}}
        self.profile_members = set()
        self.created_users = 0

    def login(self, username, password):
        assert username == get_settings().bonita_username
        assert password == get_settings().bonita_password

    def find_identity(self, resource, field, value):
        if resource == "user":
            return self.users.get(value)
        if resource == "role":
            return self.roles.get(value)
        if resource == "group":
            return self.groups.get(value)
        return None

    def create_identity(self, resource, data):
        if resource == "user":
            self.created_users += 1
            result = {"id": str(self.created_users), "userName": data["userName"]}
            self.users[data["userName"]] = result
            return result
        if resource == "role":
            result = {"id": f"role-{len(self.roles) + 1}", "name": data["name"]}
            self.roles[data["name"]] = result
            return result
        path = f"{data.get('parent_path', '')}/{data['name']}" or f"/{data['name']}"
        result = {"id": f"group-{len(self.groups) + 1}", "path": path}
        self.groups[path] = result
        return result

    def list_identity(self, resource, field, value):
        assert (resource, field) == ("membership", "user_id")
        return [membership for membership in self.memberships if membership["user_id"] == value]

    def add_membership(self, user_id, group_id, role_id):
        self.memberships.append({
            "id": f"membership-{len(self.memberships) + 1}",
            "user_id": user_id,
            "group_id": group_id,
            "role_id": role_id,
        })

    def delete_membership(self, membership_id):
        self.memberships = [m for m in self.memberships if m["id"] != membership_id]

    def find_profile(self, name):
        return self.profiles.get(name)

    def find_profile_member(self, profile_id, user_id):
        return {"id": f"{profile_id}-{user_id}"} if (profile_id, user_id) in self.profile_members else None

    def add_profile_member(self, profile_id, user_id):
        self.profile_members.add((profile_id, user_id))


def test_sincroniza_usuarios_y_roles_de_forma_idempotente(seeded, monkeypatch):
    fake = FakeBonita()
    monkeypatch.setattr(bonita_users, "BonitaClient", lambda *args: fake)
    with seeded() as db:
        usuarios = db.query(Usuario).all()

    bonita_users.sincronizar_usuarios_bonita(get_settings(), usuarios)
    memberships_primera_sync = list(fake.memberships)
    bonita_users.sincronizar_usuarios_bonita(get_settings(), usuarios)

    assert set(fake.users) == {username for username, *_ in DEMO_USERS}
    assert set(fake.groups) == {
        "/rescuesync", "/rescuesync/municipio", "/rescuesync/coordinador",
        "/rescuesync/ong", "/rescuesync/entidad_nacional",
    }
    assert set(fake.roles) == {
        "operador_municipal", "centro_coordinador_regional",
        "organizacion_no_gubernamental", "entidad_nacional",
    }
    assert len(memberships_primera_sync) == len(usuarios) == len(fake.memberships)
    assert len(fake.profile_members) == len(usuarios)
    assert fake.created_users == len(usuarios)

    memberships_by_user = {membership["user_id"]: membership for membership in fake.memberships}
    roles_by_name = {name: role["id"] for name, role in fake.roles.items()}
    groups_by_path = {group["path"]: group["id"] for group in fake.groups.values()}
    for username, _, role, _ in DEMO_USERS:
        group_name, role_name, _ = bonita_users.BONITA_ROLE_MAP[role.value]
        user_id = fake.users[username]["id"]
        membership = memberships_by_user[user_id]
        assert membership["group_id"] == groups_by_path[f"/rescuesync/{group_name}"]
        assert membership["role_id"] == roles_by_name[role_name]