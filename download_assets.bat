@echo off
set BASE=api\static\vendor
mkdir %BASE%\css 2>nul
mkdir %BASE%\js 2>nul
mkdir %BASE%\webfonts 2>nul
mkdir %BASE%\fonts 2>nul

echo Downloading jQuery
curl.exe -sS -o %BASE%\js\jquery.min.js https://code.jquery.com/jquery-3.7.1.min.js
echo Downloading DataTables JS
curl.exe -sS -o %BASE%\js\jquery.dataTables.min.js https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js
echo Downloading DataTables CSS
curl.exe -sS -o %BASE%\css\jquery.dataTables.min.css https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css
echo Downloading FontAwesome CSS
curl.exe -sS -o %BASE%\css\all.min.css https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css

echo Downloading FontAwesome Webfonts
curl.exe -sS -o %BASE%\webfonts\fa-solid-900.woff2 https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2
curl.exe -sS -o %BASE%\webfonts\fa-solid-900.ttf https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.ttf
curl.exe -sS -o %BASE%\webfonts\fa-regular-400.woff2 https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2
curl.exe -sS -o %BASE%\webfonts\fa-regular-400.ttf https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.ttf
curl.exe -sS -o %BASE%\webfonts\fa-brands-400.woff2 https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.woff2
curl.exe -sS -o %BASE%\webfonts\fa-brands-400.ttf https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.ttf

echo Downloading Inter Fonts
curl.exe -sS -L -o %BASE%\fonts\inter-regular.woff2 https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-400-normal.woff2
curl.exe -sS -L -o %BASE%\fonts\inter-medium.woff2 https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-500-normal.woff2
curl.exe -sS -L -o %BASE%\fonts\inter-semibold.woff2 https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-600-normal.woff2
curl.exe -sS -L -o %BASE%\fonts\inter-bold.woff2 https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-700-normal.woff2

echo Done.
