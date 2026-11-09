FROM docker.io/library/node:26-alpine AS deps

# Same as the backend Dockerfile: match the host user id so the container does not write root-owned files into the repository through the bind mount
ARG UID=1000
ARG GID=1000

WORKDIR /app

# HOME set explicitly: a numeric `user:` in compose doesn't define it and pnpm needs a writable HOME for its caches
ENV CI=true COREPACK_ENABLE_DOWNLOAD_PROMPT=0 HOME=/home/node

# corepack is no longer bundled with node since v25, install it before enabling it
RUN npm install -g corepack@latest && corepack enable

# node:alpine ships a node user with id 1000: getent avoids creating a duplicate when UID is 1000
RUN set -eux; \
    getent group  "$GID" >/dev/null || addgroup -g "$GID" app; \
    getent passwd "$UID" >/dev/null || adduser -u "$UID" -G "$(getent group "$GID" | cut -d: -f1)" \
                                               -h "$HOME" -D app; \
    mkdir -p "$HOME" /app; \
    chown -R "$UID:$GID" "$HOME" /app

# install as the final user: this avoids `chown -R` which would duplicate the store
USER $UID:$GID

COPY --chown=$UID:$GID frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./

# --store-dir: at runtime node_modules is a volume so it lives on a different filesystem than $HOME and pnpm falls back to <project>/.pnpm-store
# Building the store at that same location => the named volume mounted there doesn't redownload all packages on the first install
RUN pnpm install --frozen-lockfile --ignore-scripts --store-dir /app/.pnpm-store

FROM deps AS dev

ARG UID=1000
ARG GID=1000

COPY --chown=$UID:$GID frontend/ ./
RUN pnpm exec nuxt prepare
EXPOSE 3000
CMD ["pnpm", "dev", "--host", "0.0.0.0"]

FROM deps AS build

ARG UID=1000
ARG GID=1000

COPY --chown=$UID:$GID frontend/ ./
RUN pnpm exec nuxt prepare && pnpm run generate

FROM docker.io/library/nginx:1.30-alpine AS runtime

RUN apk add --no-cache openssl
COPY --from=build /app/.output/public /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx/entrypoint.sh /docker-entrypoint.d/40-generate-cert.sh
RUN chmod +x /docker-entrypoint.d/40-generate-cert.sh

# Does not derive from `build`: no `pnpm run generate` on a dev build
FROM docker.io/library/nginx:1.30-alpine AS runtime-dev

RUN apk add --no-cache openssl
COPY nginx/nginx.dev.conf /etc/nginx/conf.d/default.conf
COPY nginx/entrypoint.sh /docker-entrypoint.d/40-generate-cert.sh
RUN chmod +x /docker-entrypoint.d/40-generate-cert.sh
