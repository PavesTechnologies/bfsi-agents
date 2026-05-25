# Starts all agents and the orchestrator, each in a separate terminal tab/window.
# Run from repo root: .\dev.ps1

$RepoRoot = $PSScriptRoot

$Services = @(
    @{ Name = "intake_agent";      Path = "agents\intake_agent";  Cmd = "poetry run dev" }
    @{ Name = "kyc_agent";         Path = "agents\kyc_agent";     Cmd = "poetry run dev" }
    @{ Name = "decisioning_agent"; Path = "agents\decisioning_agent"; Cmd = "poetry run dev" }
    @{ Name = "disbursment_agent"; Path = "agents\disbursment_agent"; Cmd = "poetry run dev" }
    @{ Name = "orchestrator";      Path = "orchestrator";         Cmd = "poetry run dev" }
    @{ Name = "bank-admin-service"; Path = "bank-admin-service";  Cmd = "poetry run dev" }
    @{ Name = "bank-admin-ui";     Path = "bank-admin-ui";        Cmd = "npm run dev" }
)

$UseWT = Get-Command wt -ErrorAction SilentlyContinue

if ($UseWT) {
    Write-Host "Launching all services in Windows Terminal tabs..."

    $first = $Services[0]
    $firstDir = Join-Path $RepoRoot $first.Path
    $wtArgs = "new-tab --title `"$($first.Name)`" --startingDirectory `"$firstDir`" cmd /k $($first.Cmd)"

    foreach ($svc in $Services[1..($Services.Length - 1)]) {
        $dir = Join-Path $RepoRoot $svc.Path
        $wtArgs += " ; new-tab --title `"$($svc.Name)`" --startingDirectory `"$dir`" cmd /k $($svc.Cmd)"
    }

    Start-Process wt -ArgumentList $wtArgs
} else {
    Write-Host "Windows Terminal not found - opening separate cmd windows..."
    foreach ($svc in $Services) {
        $dir = Join-Path $RepoRoot $svc.Path
        Write-Host "Starting $($svc.Name)..."
        Start-Process cmd -ArgumentList "/k $($svc.Cmd)" -WorkingDirectory $dir
    }
}

Write-Host "All services started."
