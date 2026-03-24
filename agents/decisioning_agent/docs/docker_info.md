## Docker Commands

---

# ✅ 1. Image commands

### Build image

```bash
docker build -t myapp .
```

👉 `-t` → tag (name:tag)

Example:

```bash
docker build -t kyc-agent:1.0 .
```

---

### List images

```bash
docker images
```

---

### Remove image

```bash
docker rmi image_name
```

Force:

```bash
docker rmi -f image_name
```

---

### Pull image

```bash
docker pull python:3.11
```

---

# ✅ 2. Container run commands (MOST IMPORTANT)

### Run container

```bash
docker run image
```

---

### Run with name

```bash
docker run --name mycontainer image
```

👉 `--name` → container name

---

### Run in background

```bash
docker run -d image
```

👉 `-d` → detached mode

---

### Port mapping

```bash
docker run -p 8000:8000 image
```

👉 `-p host:container`

---

### Environment file

```bash
docker run --env-file .env image
```

---

### Env variable inline

```bash
docker run -e KEY=value image
```

---

### Remove automatically after stop

```bash
docker run --rm image
```

---

### Restart policy (production important)

```bash
docker run --restart always image
```

Other options:

```
no
on-failure
unless-stopped
```

---

# ✅ 3. Container management

### List running containers

```bash
docker ps
```

All containers:

```bash
docker ps -a
```

---

### Stop container

```bash
docker stop container
```

---

### Start container

```bash
docker start container
```

---

### Restart container

```bash
docker restart container
```

---

### Remove container

```bash
docker rm container
```

Force remove:

```bash
docker rm -f container
```

---

# ✅ 4. Logs & debugging (VERY IMPORTANT)

### Logs

```bash
docker logs container
```

Follow logs:

```bash
docker logs -f container
```

Last lines:

```bash
docker logs --tail 100 container
```

---

### Exec into container

```bash
docker exec -it container bash
```

If no bash:

```bash
docker exec -it container sh
```

👉 `-it` = interactive terminal

---

# ✅ 5. Docker inspect & info

```bash
docker inspect container
```

```bash
docker stats
```

```bash
docker info
```

---

# ✅ 6. Volumes (data persistence)

Run with volume:

```bash
docker run -v data:/app/data image
```

Bind mount:

```bash
docker run -v $(pwd):/app image
```

---

# ✅ 7. Network commands

```bash
docker network ls
```

```bash
docker network create mynet
```

Run with network:

```bash
docker run --network mynet image
```

---

# ⭐ Most important run flags (interview + real life)

| Flag         | Meaning              |
| ------------ | -------------------- |
| `-d`         | background           |
| `--name`     | container name       |
| `-p`         | port mapping         |
| `-e`         | env variable         |
| `--env-file` | env file             |
| `-v`         | volume               |
| `--rm`       | auto remove          |
| `--restart`  | restart policy       |
| `-it`        | interactive terminal |

---

# ⭐ Build flags (important)

```bash
docker build -t name .
```

| Flag          | Meaning         |
| ------------- | --------------- |
| `-t`          | tag image       |
| `-f`          | Dockerfile path |
| `--no-cache`  | rebuild fresh   |
| `--build-arg` | build variable  |

Example:

```bash
docker build -t app -f infra/Dockerfile .
```

---

# ⭐ Tag concept (important)

Image format:

```
name:tag
```

Examples:

```
kyc-agent:latest
kyc-agent:1.0
kyc-agent:dev
```

Tag image:

```bash
docker tag kyc-agent kyc-agent:v1
```

---

Run Compose:

```bash
docker compose -f  .\infra\dec_compose.yml  up -d  --build
```
---