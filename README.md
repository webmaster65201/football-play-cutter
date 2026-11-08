# Football Play Cutter V3 — Apple Silicon Mac build kit

This update preserves the V2 motion-based candidate cutter and adds **scouting-team-relative ODK labeling**. Default team: Southside. Jersey and helmet colors: unknown.

## What works
- Detect and review motion-based candidate clips, or auto-export them.
- In Review First mode, double-click the **ODK** cell and choose O (scouting team offense), D (scouting team defense), K (special teams), or ? (not classified).
- Save edits. The video-adjacent `*_candidates.csv` contains ODK values and can be used as a starting point for a scouting breakdown. MP4 clips export as before.
- Existing V2 CSV files load with `?` in ODK. **Back up your CSV before running detection again**, which overwrites candidate rows.

## Important limitation
**Automatic ODK recognition is NOT implemented in this version.** Without known jersey colors, verified possession, and labeled sample plays, inferring O/D/K would be guesswork. The program intentionally uses `?` instead of inventing a label. This is a real, editable ODK workflow, not a trained football classifier. The exported CSV is not claimed to match Hudl's proprietary import format.

## Update existing GitHub repository (no Terminal on your Mac)
1. Open your private `football-play-cutter` GitHub repository.
2. Replace the existing `desktop_app.py`, `play_cutter.py`, and `README.md` with these V3 files using GitHub's browser upload or edit tools. `requirements.txt` and `.github/workflows/build-mac.yml` can remain unchanged.
3. Commit changes to `main`. In Actions, open **Build Mac App** and run the workflow if it did not start automatically.
4. When the build is green, download the **Football-Play-Cutter-Apple-Silicon** artifact. Extract both ZIP layers if needed, and move the new `.app` to Applications, replacing the old one after quitting it.
5. Load the five-minute test video, choose Review First, and check the ODK dropdown.

The build runs on GitHub's macOS runner and bundles Python dependencies. No Python or Terminal is needed for normal application use. The new Mac build still needs to be tested on your computer.
