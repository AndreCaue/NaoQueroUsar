# Bundled fonts for IG card rendering

These font files are vendored in-repo for deterministic Instagram card rendering (Phase 29, D-08). The renderer **MUST** load these repo-bundled paths only. Do **not** rely on system fonts, runtime download, or optional fallback rendering. If bundled fonts are missing, rendering must fail with a clear internal error.

## Files

- `DejaVuSans.ttf`
- `DejaVuSans-Bold.ttf`

## Font family

- Family: **DejaVu Sans**
- Variant files used: Regular (`DejaVuSans.ttf`), Bold (`DejaVuSans-Bold.ttf`)

## Upstream source / origin

- Project: DejaVu fonts
- Upstream repository: <https://github.com/dejavu-fonts/dejavu-fonts>
- Exact release used: `version_2_37` (DejaVu Fonts 2.37)
- Exact release artifact used: `dejavu-fonts-ttf-2.37.zip`
- Artifact URL: <https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip>
- Files copied from: `dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf`, `dejavu-fonts-ttf-2.37/ttf/DejaVuSans-Bold.ttf`

## License

- License: **Bitstream Vera Fonts Copyright / DejaVu Fonts license** (Bitstream Vera license terms with DejaVu changes in public domain; see `LICENSE` in upstream release).
- The upstream `LICENSE` file from release `version_2_37` applies to these font files.
- Redistribution in this repository is permitted under those terms; keep attribution and license terms when redistributing.

## Operational note

`backend/app/services/social/image_card.py` must resolve fonts via `get_bundled_font_paths()` and pass explicit paths to Pillow. No OS font lookup is allowed.
