from dataclasses import dataclass

from app.integrations.bonita import BonitaClient

ROLE_GROUPS = {
    "MUNICIPIO": "/rescuesync/municipio",
    "COORDINADOR": "/rescuesync/coordinador",
    "ONG": "/rescuesync/ong",
    "AUDITOR": "/rescuesync/auditor",
}


@dataclass(frozen=True)
class BonitaMembership:
    group_name: str
    group_parent_path: str
    role_name: str

    @property
    def group_path(self) -> str:
        parent = self.group_parent_path.rstrip("/")
        return f"{parent}/{self.group_name}" if parent else f"/{self.group_name}"


@dataclass(frozen=True)
class BonitaIdentity:
    user_id: str
    username: str
    display_name: str
    memberships: tuple[BonitaMembership, ...]

    @property
    def group_paths(self) -> frozenset[str]:
        return frozenset(membership.group_path for membership in self.memberships)

    @property
    def roles(self) -> frozenset[str]:
        return frozenset(role for role, group in ROLE_GROUPS.items() if group in self.group_paths)

    def has_role(self, role: str) -> bool:
        return role in self.roles


def authenticate(base_url: str, username: str, password: str, timeout: float = 10.0) -> BonitaIdentity:
    client = BonitaClient(base_url, timeout)
    client.login(username, password)
    user_id = client.current_user_id()
    profile = client.get_user(user_id)
    memberships = client.get_user_memberships(user_id)
    resolved_memberships = []
    for membership in memberships:
        group = client.get_group(membership["group_id"])
        role = client.get_role(membership["role_id"])
        resolved_memberships.append(
            BonitaMembership(
                group_name=group["name"],
                group_parent_path=group.get("parent_path", "/"),
                role_name=role["name"],
            )
        )

    return BonitaIdentity(
        user_id=str(user_id),
        username=profile["userName"],
        display_name=" ".join(part for part in (profile.get("firstname"), profile.get("lastname")) if part),
        memberships=tuple(resolved_memberships),
    )