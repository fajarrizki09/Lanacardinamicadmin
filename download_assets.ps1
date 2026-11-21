$ErrorActionPreference = "Stop"
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

$baseUrl = Join-Path $PSScriptRoot "api\static\vendor"
New-Item -ItemType Directory -Force -Path "$baseUrl\css" | Out-Null
New-Item -ItemType Directory -Force -Path "$baseUrl\js" | Out-Null
New-Item -ItemType Directory -Force -Path "$baseUrl\webfonts" | Out-Null
New-Item -ItemType Directory -Force -Path "$baseUrl\fonts" | Out-Null

$assets = @(
    @{Url="https://code.jquery.com/jquery-3.7.1.min.js"; Path="$baseUrl\js\jquery.min.js"},
    @{Url="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"; Path="$baseUrl\js\jquery.dataTables.min.js"},
    @{Url="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css"; Path="$baseUrl\css\jquery.dataTables.min.css"},
    @{Url="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"; Path="$baseUrl\css\all.min.css"},
    @{Url="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2"; Path="$baseUrl\webfonts\fa-solid-900.woff2"},
    @{Url="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.ttf"; Path="$baseUrl\webfonts\fa-solid-900.ttf"},
    @{Url="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2"; Path="$baseUrl\webfonts\fa-regular-400.woff2"},
    @{Url="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.ttf"; Path="$baseUrl\webfonts\fa-regular-400.ttf"},
    @{Url="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.woff2"; Path="$baseUrl\webfonts\fa-brands-400.woff2"},
    @{Url="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.ttf"; Path="$baseUrl\webfonts\fa-brands-400.ttf"},
    @{Url="https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-400-normal.woff2"; Path="$baseUrl\fonts\inter-regular.woff2"},
    @{Url="https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-500-normal.woff2"; Path="$baseUrl\fonts\inter-medium.woff2"},
    @{Url="https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-600-normal.woff2"; Path="$baseUrl\fonts\inter-semibold.woff2"},
    @{Url="https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-700-normal.woff2"; Path="$baseUrl\fonts\inter-bold.woff2"}
)

foreach ($asset in $assets) {
    Write-Host "Downloading $($asset.Url)..."
    Invoke-WebRequest -Uri $asset.Url -OutFile $asset.Path -UseBasicParsing
}
Write-Host "Done downloading assets"
