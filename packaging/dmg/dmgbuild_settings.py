# dmgbuild settings for Crypto Bot Pro DMG
# Docs: https://dmgbuild.readthedocs.io/ :contentReference[oaicite:3]{index=3}

import os

application = "CryptoBotPro.app"
format = "UDZO"
size = None
files = [application]
symlinks = { "Applications": "/Applications" }

# DMG window appearance
icon_size = 128
window_rect = ((100, 100), (820, 520))
background = None  # you can add a background png later

# Layout
icon_locations = {
    application: (180, 260),
    "Applications": (640, 260),
}
