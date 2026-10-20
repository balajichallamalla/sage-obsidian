# Troubleshooting

| Symptom | Fix |
|---|---|
| A command says "open your vault folder" | Cowork: choose the vault as the working folder. Claude Code: `cd` into it. |
| Dashboard shows code blocks | Install Dataview; Settings → Dataview → Enable JavaScript queries; toggle the plugin off/on. |
| Dashboard looks unstyled or doubled | Close and reopen `home.md`; run `doctor`. |
| `todos.md` shows code | Install and enable the Tasks plugin. |
| "run lock held" | Another run is in progress; if it is over 2 hours old: `python3 _system/tools/run_lock.py release`. |
| Sync source fails | Reconnect it under Settings → Connectors; `doctor` shows which one. |
| git "unable to unlink … Operation not permitted" (Cowork) | Allow file deletion for the vault folder when asked, then remove leftover `.git/*.lock` files. |
| Scheduled run didn't happen | The Claude app was closed; it runs at next launch. |
