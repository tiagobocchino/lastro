# Backup completo do Supabase do Lastro para uma pasta local (Windows, PowerShell).
#
# O que sai:
#   1. lastro.dump       banco inteiro no formato do pg_dump (restaura com pg_restore)
#   2. lastro.sql        o mesmo banco em SQL legível (para conferir ou restaurar com psql)
#   3. storage\tenants\  todos os arquivos do bucket "tenants" (fontes e resultados das demandas de cada empresa)
#
# Nada fica gravado: a conexão do banco e a chave do Storage são pedidas na hora e não vão para arquivo nenhum.
#
# Antes de rodar:
#   - PostgreSQL 17 (só as ferramentas de cliente bastam):  winget install PostgreSQL.PostgreSQL.17
#   - Conexão do banco: Supabase > projeto > Connect > "Session pooler" > URI (com a senha do banco no lugar de [YOUR-PASSWORD]).
#   - Chave do Storage: Supabase > Project Settings > API Keys > secret key (sb_secret_...), a mesma do Render (LASTRO_STORAGE_CHAVE).
#
# Rodar:  powershell -ExecutionPolicy Bypass -File scripts\backup_supabase.ps1

$ErrorActionPreference = "Stop"
$projeto = "dghpdlhztkoyfyqmyjbx"
$destino = Join-Path $HOME ("lastro-backup-" + (Get-Date -Format "yyyy-MM-dd_HHmm"))
New-Item -ItemType Directory -Force -Path $destino | Out-Null

function Achar-PgDump {
    $cmd = Get-Command pg_dump -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $padrao = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\pg_dump.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
    if ($padrao) { return $padrao.FullName }
    throw "pg_dump não encontrado. Instale com: winget install PostgreSQL.PostgreSQL.17"
}

function Ler-Segredo([string]$pergunta) {
    $seguro = Read-Host $pergunta -AsSecureString
    return [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro))
}

# ---- 1 e 2: banco ------------------------------------------------------------------------------------------
$pgdump = Achar-PgDump
$versao = & $pgdump --version
if ($versao -notmatch " 1[7-9]\.") { throw "Precisa do pg_dump 17 ou mais novo (o Supabase está no Postgres 17). Encontrado: $versao" }
$url = Ler-Segredo "Cole a URI do Session pooler (postgresql://...)"
if ($url -notmatch "^postgres(ql)?://") { throw "Isso não parece uma URI do Postgres." }

Write-Host "Exportando o banco (formato pg_dump)..."
& $pgdump --dbname=$url --format=custom --no-owner --no-privileges --file=(Join-Path $destino "lastro.dump")
if ($LASTEXITCODE -ne 0) { throw "pg_dump falhou (formato custom)." }
Write-Host "Exportando o banco (SQL legível)..."
& $pgdump --dbname=$url --format=plain --no-owner --no-privileges --file=(Join-Path $destino "lastro.sql")
if ($LASTEXITCODE -ne 0) { throw "pg_dump falhou (SQL)." }
$url = $null

# ---- 3: Storage --------------------------------------------------------------------------------------------
$chave = Ler-Segredo "Cole a secret key do Supabase (sb_secret_...) para baixar o Storage, ou Enter para pular"
if ($chave) {
    $base = "https://$projeto.supabase.co/storage/v1"
    $cab = @{ apikey = $chave }
    if ($chave.StartsWith("eyJ")) { $cab["Authorization"] = "Bearer $chave" }
    $pastas = New-Object System.Collections.Queue
    $pastas.Enqueue("")
    $baixados = 0
    while ($pastas.Count -gt 0) {
        $prefixo = $pastas.Dequeue()
        $offset = 0
        do {
            $corpo = @{ prefix = $prefixo; limit = 1000; offset = $offset } | ConvertTo-Json
            $itens = Invoke-RestMethod -Method Post -Uri "$base/object/list/tenants" -Headers $cab -ContentType "application/json" -Body $corpo
            foreach ($it in $itens) {
                $caminho = if ($prefixo) { "$prefixo/$($it.name)" } else { $it.name }
                if ($null -eq $it.id) { $pastas.Enqueue($caminho); continue }  # sem id = subpasta
                $local = Join-Path $destino ("storage\tenants\" + ($caminho -replace "/", "\"))
                New-Item -ItemType Directory -Force -Path (Split-Path $local) | Out-Null
                $uri = "$base/object/tenants/" + (($caminho -split "/" | ForEach-Object { [uri]::EscapeDataString($_) }) -join "/")
                Invoke-WebRequest -Uri $uri -Headers $cab -OutFile $local -UseBasicParsing | Out-Null
                $baixados++
            }
            $offset += 1000
        } while ($itens.Count -eq 1000)
    }
    $chave = $null
    Write-Host "Storage: $baixados arquivos baixados."
}

Write-Host ""
Write-Host "Backup pronto em: $destino"
Get-ChildItem $destino | Format-Table Name, Length
Write-Host "Restaurar no projeto novo:  pg_restore --dbname=<URI do projeto novo> --no-owner --no-privileges lastro.dump"
