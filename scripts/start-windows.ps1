if (-Not (Test-Path .env) -and (Test-Path .env.example)) {
    Copy-Item .env.example .env
    Write-Host "Se ha creado .env a partir de .env.example"
}

docker compose up --build
