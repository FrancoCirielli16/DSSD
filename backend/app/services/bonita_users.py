"""Provision RescueSync accounts and role memberships in Bonita."""
from sqlalchemy import select

from app.core.config import Settings
from app.db import SessionLocal
from app.integrations.bonita import BONITA_ROLE_MAP, BonitaClient, BonitaError
from app.models import Usuario

ROOT_GROUP = ("rescuesync", "RescueSync")


def _ensure_role(client: BonitaClient, name: str, display_name: str) -> str:
    role = client.find_identity("role", "name", name)
    if role is None:
        role = client.create_identity(
            "role", {"name": name, "displayName": display_name, "description": display_name}
        )
    return str(role["id"])


def _ensure_group(client: BonitaClient, name: str, display_name: str, parent_path: str | None) -> str:
    path = f"{parent_path}/{name}" if parent_path else f"/{name}"
    group = client.find_identity("group", "path", path)
    if group is None:
        body = {"name": name, "displayName": display_name, "description": display_name}
        if parent_path:
            body["parent_path"] = parent_path
        group = client.create_identity("group", body)
    return str(group["id"])


def _ensure_membership(
    client: BonitaClient, user_id: str, group_id: str, role_id: str, rescue_group_ids: set[str]
) -> None:
    memberships = client.list_identity("membership", "user_id", user_id)
    correct_membership = False
    for item in memberships:
        item_group = str(item["group_id"])
        item_role = str(item["role_id"])
        if item_group not in rescue_group_ids:
            continue
        if item_group == group_id and item_role == role_id:
            correct_membership = True
        else:
            client.delete_membership(str(item["id"]))
    if not correct_membership:
        client.add_membership(user_id, group_id, role_id)


def _ensure_profile(client: BonitaClient, user_id: str) -> None:
    profile = client.find_profile("User")
    if profile is None:
        raise BonitaError("No existe el perfil 'User' en Bonita.")
    if client.find_profile_member(str(profile["id"]), user_id) is None:
        client.add_profile_member(str(profile["id"]), user_id)


def sincronizar_usuarios_bonita(settings: Settings, usuarios: list[Usuario]) -> None:
    client = BonitaClient(settings.bonita_base_url, settings.bonita_timeout_seconds)
    client.login(settings.bonita_username, settings.bonita_password)

    _ensure_group(client, ROOT_GROUP[0], ROOT_GROUP[1], None)
    groups = {}
    roles = {}
    for group_name, role_name, display_name in BONITA_ROLE_MAP.values():
        groups[group_name] = _ensure_group(
            client, group_name, display_name, f"/{ROOT_GROUP[0]}"
        )
        roles[role_name] = _ensure_role(client, role_name, display_name)
    rescue_group_ids = set(groups.values())

    for user in usuarios:
        user_data = client.find_identity("user", "userName", user.username)
        if user_data is None:
            first_name, _, last_name = user.nombre.partition(" ")
            user_data = client.create_identity(
                "user",
                {
                    "userName": user.username,
                    "password": settings.bonita_user_password,
                    "firstName": first_name,
                    "lastName": last_name or first_name,
                    "enabled": True,
                },
            )

        user_id = str(user_data["id"])
        group_name, role_name, _ = BONITA_ROLE_MAP[user.rol.value]
        _ensure_membership(
            client, user_id, groups[group_name], roles[role_name], rescue_group_ids
        )
        _ensure_profile(client, user_id)


def sincronizar_usuarios_existentes(settings: Settings) -> None:
    with SessionLocal() as db:
        usuarios = list(db.scalars(select(Usuario).order_by(Usuario.id)))
    sincronizar_usuarios_bonita(settings, usuarios)