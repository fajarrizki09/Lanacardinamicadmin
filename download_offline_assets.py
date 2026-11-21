import os
import urllib.request

base_dir = os.path.join("api", "static", "vendor")
os.makedirs(os.path.join(base_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(base_dir, "js"), exist_ok=True)
os.makedirs(os.path.join(base_dir, "webfonts"), exist_ok=True)
os.makedirs(os.path.join(base_dir, "fonts"), exist_ok=True)

assets = [
    ("https://code.jquery.com/jquery-3.7.1.min.js", "js/jquery.min.js"),
    ("https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js", "js/jquery.dataTables.min.js"),
    ("https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css", "css/jquery.dataTables.min.css"),
    ("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css", "css/all.min.css"),
    ("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2", "webfonts/fa-solid-900.woff2"),
    ("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.ttf", "webfonts/fa-solid-900.ttf"),
    ("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2", "webfonts/fa-regular-400.woff2"),
    ("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.ttf", "webfonts/fa-regular-400.ttf"),
    ("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.woff2", "webfonts/fa-brands-400.woff2"),
    ("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.ttf", "webfonts/fa-brands-400.ttf"),
]

for url, path in assets:
    full_path = os.path.join(base_dir, path.replace("/", os.sep))
    print(f"Downloading {url} to {full_path}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(full_path, 'wb') as out_file:
        data = response.read()
        out_file.write(data)

inter_css = """
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('../fonts/inter-regular.woff2') format('woff2');
}
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url('../fonts/inter-medium.woff2') format('woff2');
}
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url('../fonts/inter-semibold.woff2') format('woff2');
}
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url('../fonts/inter-bold.woff2') format('woff2');
}
"""
with open(os.path.join(base_dir, "css", "inter.css"), "w") as f:
    f.write(inter_css)

inter_fonts = [
    ("https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-400-normal.woff2", "fonts/inter-regular.woff2"),
    ("https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-500-normal.woff2", "fonts/inter-medium.woff2"),
    ("https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-600-normal.woff2", "fonts/inter-semibold.woff2"),
    ("https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-700-normal.woff2", "fonts/inter-bold.woff2"),
]

for url, path in inter_fonts:
    full_path = os.path.join(base_dir, path.replace("/", os.sep))
    print(f"Downloading {url} to {full_path}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(full_path, 'wb') as out_file:
        data = response.read()
        out_file.write(data)

print("✅ Semua aset offline berhasil didownload.")
