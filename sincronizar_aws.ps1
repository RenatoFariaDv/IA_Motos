$ArquivoLocal = "$PSScriptRoot\interface\anuncios_encontrados.json"
$Destino = "ubuntu@54.233.146.58:/home/ubuntu/IA_Motos/interface/anuncios_encontrados.json"

while ($true) {
    if (Test-Path $ArquivoLocal) {
        scp -i "$env:USERPROFILE\.ssh\IA-Motos-Key.pem" "$ArquivoLocal" "$Destino"

        if ($LASTEXITCODE -eq 0) {
            Write-Host "$(Get-Date) - sincronizado com sucesso"
        } else {
            Write-Host "$(Get-Date) - falha na sincronizacao"
        }
    } else {
        Write-Host "$(Get-Date) - arquivo local nao encontrado"
    }

    Start-Sleep -Seconds 60
}