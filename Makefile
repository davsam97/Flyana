COMPOSE = docker compose -f srcs/docker-compose.yml
COMPOSE_DEV = $(COMPOSE) -f srcs/docker-compose.dev.yml
# id -u/-g peut depasser la plage adressable par le user namespace rootless de
# Podman (comptes LDAP de l'ecole, UID a 8 chiffres) : le build echoue alors
# sur le chown de /srv/media (Invalid argument). Repli sur 1000, la valeur par
# defaut des Dockerfiles, plutot que de faire planter le build.
export UID := $(shell v=$$(id -u); [ "$$v" -le 60000 ] && echo "$$v" || echo 1000)
export GID := $(shell v=$$(id -g); [ "$$v" -le 60000 ] && echo "$$v" || echo 1000)

# Mount points for the named volumes of the web-dev service
DEV_DIRS = srcs/frontend/node_modules srcs/frontend/.nuxt srcs/frontend/.pnpm-store

SECRETS = secrets/POSTGRES_USER secrets/POSTGRES_PASSWORD

# Cle Tailscale du correcteur LLM : jamais generee ici, chacun depose la sienne.
# Presente, elle active le conteneur tailscale ; absente, la stack demarre sans
# et le correcteur passe en auto-evaluation.
TS_AUTHKEY = $(wildcard secrets/TS_AUTHKEY)
export COMPOSE_PROFILES := $(if $(TS_AUTHKEY),tailscale,)

all: up

up: secrets srcs/.env
	$(COMPOSE) up --build -d

dev: secrets srcs/.env | $(DEV_DIRS)
	$(COMPOSE_DEV) up --build

$(DEV_DIRS):
	@mkdir -p $@

# Docker `file:` secrets are not SELinux-relabelled on mount, so on an enforcing
# host (Fedora/RHEL) postgres reads them as EACCES. Create them if missing, then
# relabel to a container-readable type when SELinux is on.
secrets: $(SECRETS)
	@if command -v selinuxenabled >/dev/null 2>&1 && selinuxenabled; then \
		chcon -t container_file_t $(SECRETS) $(TS_AUTHKEY); \
	fi

secrets/POSTGRES_USER:
	@mkdir -p secrets && printf 'flyana' > $@

secrets/POSTGRES_PASSWORD:
	@mkdir -p secrets && openssl rand -hex 24 > $@

srcs/.env:
	@echo "srcs/.env manquant : cp srcs/.env.example srcs/.env puis renseigner SECRET_KEY et TOTP_ENCRYPTION_KEY (openssl rand -hex 32)" >&2; exit 1

down:
	$(COMPOSE_DEV) down

clean:
	$(COMPOSE_DEV) down -v

fclean: clean
	@docker system prune -af

re: fclean all

ps:
	@$(COMPOSE) ps

logs:
	@$(COMPOSE) logs -f

.PHONY: all up dev down clean fclean re ps logs secrets
