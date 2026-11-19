# Portable Node.js Runtime

Folder ini dipakai oleh `build.bat` dan `build_protected.bat` untuk membundel Node.js ke installer.

Isi folder ini dengan hasil ekstrak Node.js Windows x64 sebelum build installer.

Struktur minimal:

```text
tools/node/node.exe
tools/node/node_modules/
tools/node/npm.cmd
tools/node/npx.cmd
```

Cara menyiapkan:

1. Download Node.js Windows x64 ZIP dari situs resmi Node.js.
2. Extract ZIP tersebut.
3. Salin seluruh isi folder hasil extract ke `tools/node/`.
4. Pastikan file `tools/node/node.exe` ada.
5. Jalankan `build.bat` atau `build_protected.bat`.

Catatan: file runtime Node.js sengaja tidak dibuat otomatis oleh aplikasi agar build tetap eksplisit dan mudah diaudit.