# Deploying NEBULA

Two parts: the **website** on Vercel and the **game server** on PythonAnywhere. Saves live on the server.

## Limits (PythonAnywhere free plan)
- The server is web-only (WSGI). The app is adapted with `nebula/wsgi.py`.
- Pygame combat needs a desktop window, which the server lacks. Set `NEBULA_ALLOW_COMBAT=0`; **Command a wing** still resolves sorties. Flying missions works only when you run NEBULA locally.
- Free web apps sleep when idle and have a single outbound allow-list; the game makes no outbound calls.

## 1. Server (PythonAnywhere)
1. Push branch `nebula` to GitHub, then on PythonAnywhere open a Bash console and run:
   `git clone -b nebula <your-repo-url> nebula && cd nebula && python3.13 -m venv ~/venv && ~/venv/bin/pip install -r requirements.txt`
2. Web tab → **Add a new web app** → Manual configuration, Python 3.13.
3. Set the WSGI file to the one that imports `application` from `nebula/wsgi.py` (point it at `/home/<user>/nebula/nebula/wsgi.py` with `sys.path` set to `/home/<user>/nebula`).
4. Set the virtualenv path to `/home/<user>/venv`.
5. Add environment variables in the Web tab (or the WSGI file):
   - `NEBULA_HOSTS=<user>.pythonanywhere.com`
   - `NEBULA_CORS_ORIGINS=https://<your-site>.vercel.app`
   - `NEBULA_ALLOW_COMBAT=0`
6. Reload. Check `https://<user>.pythonanywhere.com/api/world` returns JSON.

## 2. Website (Vercel)
1. Edit `nebula/web/config.js`: set `window.NEBULA_API = "https://<user>.pythonanywhere.com";` and commit.
2. Vercel → New Project → import the repo, branch `nebula`, **Root Directory: `nebula/web`**, no build command.
3. Deploy, then open the Vercel URL and start a campaign.

## Saves
Campaigns persist in `saves/nebula.db` on PythonAnywhere. Keep the file (set `NEBULA_DB` to a path outside the git folder if you prefer). Log out keeps saves; log in restores them.
