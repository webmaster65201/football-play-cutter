# Football Play Cutter — Mac standalone build kit

This package is **source and automated build instructions**, not yet a built Mac app. It creates a double-clickable `.app` with Python and FFmpeg bundled. No Python, Terminal, or FFmpeg is needed on the Mac *after the app is built*. It has not yet been built or tested on a physical Mac.

## Build using a browser (GitHub Actions)

1. Sign in to GitHub and create a **private** repository (e.g. `football-play-cutter`).
2. Upload `desktop_app.py`, `play_cutter.py`, `requirements.txt`, and the `.github/workflows/build-mac.yml` file, preserving the folder structure. GitHub's browser upload interface may hide dotfolders; if so, create `.github/workflows/build-mac.yml` through **Add file → Create new file** and paste its content.
3. Open **Actions → Build Mac App → Run workflow**. It may also start automatically on the first push to `main`.
4. After the job finishes, open the run, download the **Intel** or **Apple-Silicon** artifact, and unzip it. Inside is a ZIP containing `Football Play Cutter.app`.
5. Move the `.app` to Applications. Open it via Finder. As this is **not signed or notarized**, macOS may block the first launch. If you trust your own build, go to **System Settings → Privacy & Security → Open Anyway** after the blocked attempt. Never disable Gatekeeper globally.

**Which download?** Apple Silicon for M1/M2/M3/M4/M5 Macs; Intel for Intel-based Macs. Use Apple menu → About This Mac to check.

**Caveats:** GitHub Actions runner labels and hosted-runner availability may change; the builds can fail, and an unsigned app can trigger security prompts. GitHub Actions usage limits may apply. The software's detector is experimental: it identifies motion segments, not verified snaps. Preserve the original game footage. Only process recordings you have permission to use.

## Everyday use

Open the app, select video(s), choose **Review first** or **Automatic**, and click **Run selected mode**. Review first allows editing candidate start/end times, previewing in the Mac's default video player, and exporting selected clips. Automatic exports all detected candidate segments. Output appears alongside the video. Processing long videos can take time and disk space.

## Notes for future distribution

For smooth sharing with other Mac users, a developer should codesign and notarize the `.app` with an Apple Developer ID. This build is meant for personal testing and is not notarized.
