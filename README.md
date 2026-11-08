# Football Play Cutter V4 — Apple Silicon Mac

This is a **build kit**, not a precompiled `.app`. Upload `desktop_app.py`, `play_cutter.py`, `odk_suggest.py`, `requirements.txt`, and `README.md` to the root of your existing GitHub repository, replacing prior versions. Retain the `.github/workflows/build-mac.yml` workflow from V3 (included here as a backup). Run **Actions → Build Mac App** and download the Apple Silicon artifact. Quit V3 before replacing the application.

## ODK prototype

- Scouting team: **Southside**, **white** jerseys; opponent: **blue**; helmet unknown.
- O means Southside offense; D means Southside defense; K means special teams.
- After detecting plays in **Review First**, choose the direction **Southside attacks** on the screen (left/right), then click **Suggest ODK**.
- The software uses coarse jersey-color position and field geometry to suggest **O/D**. These suggestions are **low confidence** and **must be manually verified**. It does not automatically recognize snaps, possession, or special teams. Uncertain clips stay `?`; assign `K` manually.
- The direction can change during the game. **Do not run suggestions across segments with different attacking directions**. If uncertain, keep direction Unknown and label manually.
- Existing manually labeled ODK values are never overwritten by Suggest ODK. Click **Save edits** before export.
- This prototype is not a trained football classifier and may misclassify many plays, especially wide broadcast angles or shots without clear jersey visibility.

## Installation

GitHub builds the standalone Mac app; you do not need Python or Terminal for everyday use. The workflow bundles Python dependencies. Mac Gatekeeper may require user approval for an unsigned app.

## Safety

Keep original footage and your V3 app as backup. The detection and ODK features are experimental. Verify all clips before using ODK in scouting reports.
