# Secrets of this instance (git-ignored)

| File | Content |
|---|---|
| `oidc_client_secret` | client secret of the Keycloak client `{{ cookiecutter.ifdd_keycloak_lab_client_id }}` (`IFDD_KEYCLOAK_LAB_CLIENT_SECRET` in the `.env` of the keycloak instance); `ifdd-meta create` copies it in |

The file is read by the hub at start (mounted read-only). Mode 0600.
