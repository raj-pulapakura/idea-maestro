## idea-maestro

build your idea with confidence.

### Docs

- `docs/01-product-vision.md` – what Idea Maestro is and who it’s for.
- `docs/02-agents-and-ux.md` – agent personas, living documents, and UX concepts.
- `docs/03-architecture-and-stack.md` – system architecture and low-cost tech stack.
- `docs/04-monetization-and-credits.md` – pure credits model and pricing mechanics.

### Docker dev (live reload)

- Start: `docker compose -f docker-compose.dev.yml up --build`
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000/api/test`
- Env files: `./backend/.env` and `./frontend/.env` are loaded by compose
