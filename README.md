# Football Play Cutter V5.1 — Generic Team Setup (Mac Build Kit)

No team is prefilled. Enter the home and away team names, choose each jersey color from the expanded dropdown, and select which team you are scouting. ODK labels are relative to that selected team.

## Important detection limitation

The current experimental ODK suggestion algorithm ONLY works for one team labeled **White** and the other labeled **Blue** (exact dropdown values), with a known attacking direction. The expanded color list is useful for recording game details and manual ODK tagging, but it **does not make automatic classification work for the new colors**. Other combinations are not automatically classified. Even White/Blue suggestions are low-confidence and require review. Kicking plays remain manual.

## Build on GitHub without Terminal

Upload/replace `desktop_app.py`, `play_cutter.py`, `odk_suggest.py`, `requirements.txt`, and `README.md` in your existing private repository. Keep the included `.github/workflows/build-mac.yml`. Commit and use Actions > Build Mac App. Download the Apple-Silicon artifact, unzip it, and replace your previous app only after verifying the new one runs.

The existing play cutting, review, export, and manual ODK editing features are retained. Preserve your original recordings and the prior working app.
