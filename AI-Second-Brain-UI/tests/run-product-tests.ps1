[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$testDirectory = Split-Path -Parent $PSCommandPath
$uiDirectory = Split-Path -Parent $testDirectory
$vaultDirectory = Split-Path -Parent $uiDirectory
$temporaryDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ("boujoy-product-tests-" + [guid]::NewGuid().ToString('N'))
$readyFile = Join-Path $temporaryDirectory 'ready.txt'
$stdoutLog = Join-Path $temporaryDirectory 'preview.stdout.log'
$stderrLog = Join-Path $temporaryDirectory 'preview.stderr.log'
$serverProcess = $null
$previousPreviewUrl = [Environment]::GetEnvironmentVariable('BOUJOY_PREVIEW_URL', 'Process')

function Find-Executable {
    param([Parameter(Mandatory = $true)][string[]]$Candidates)

    foreach ($candidate in $Candidates) {
        if (-not $candidate) { continue }
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command -and $command.Source) { return $command.Source }
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }
    return ''
}

$userDirectory = [Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)
$python = Find-Executable -Candidates @(
    (Join-Path $userDirectory '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'),
    (Join-Path $userDirectory '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'),
    '/opt/homebrew/bin/python3',
    '/usr/local/bin/python3',
    '/usr/bin/python3',
    'python3',
    'python.exe'
)
$node = Find-Executable -Candidates @(
    (Join-Path $userDirectory 'Library/Application Support/Boujoy/MademRuntime/node-v24.18.0-darwin-arm64/bin/node'),
    (Join-Path $userDirectory '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'),
    (Join-Path $userDirectory '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node.exe'),
    'C:\MademRuntime\node-v24.18.0-win-x64\node.exe',
    'node',
    'node.exe'
)

if (-not $python) { throw '找不到 Python 3，无法运行产品回归测试。' }
if (-not $node) { throw '找不到 Node.js 24+，无法运行真实浏览器测试。' }

New-Item -ItemType Directory -Path $temporaryDirectory -Force | Out-Null
try {
    Write-Host '[1/3] 接口、安全与数据契约'
    & $python -m unittest discover -s $testDirectory -p 'test_*.py' -v
    if ($LASTEXITCODE -ne 0) { throw "契约测试失败，退出码 $LASTEXITCODE。" }

    Write-Host '[2/3] 启动隔离的本地预览服务'
    $previewScript = Join-Path $uiDirectory 'web_preview.pyw'
    $quotedPreviewScript = '"' + $previewScript.Replace('"', '\"') + '"'
    $quotedReadyFile = '"' + $readyFile.Replace('"', '\"') + '"'
    $serverProcess = Start-Process -FilePath $python `
        -ArgumentList @($quotedPreviewScript, '--server-only', '0', '--ready-file', $quotedReadyFile) `
        -WorkingDirectory $vaultDirectory -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru

    for ($attempt = 0; $attempt -lt 100 -and -not (Test-Path -LiteralPath $readyFile -PathType Leaf); $attempt++) {
        if ($serverProcess.HasExited) { break }
        Start-Sleep -Milliseconds 100
    }
    if (-not (Test-Path -LiteralPath $readyFile -PathType Leaf)) {
        $serverError = if (Test-Path -LiteralPath $stderrLog) { Get-Content -LiteralPath $stderrLog -Raw } else { '' }
        throw "预览服务没有就绪。$serverError"
    }

    $previewUrl = (Get-Content -LiteralPath $readyFile -TotalCount 1).Trim()
    if ($previewUrl -notmatch '^http://127\.0\.0\.1:\d+/$') { throw "预览服务返回无效地址：$previewUrl" }
    [Environment]::SetEnvironmentVariable('BOUJOY_PREVIEW_URL', $previewUrl, 'Process')

    Write-Host '[3/3] Chrome 桌面、窄屏、Bok 工作台、关于我、搜索、编辑与原生入口'
    & $node (Join-Path $testDirectory 'browser-smoke.mjs')
    if ($LASTEXITCODE -ne 0) { throw "浏览器测试失败，退出码 $LASTEXITCODE。" }
    Write-Host 'Boujoy 产品回归测试：PASS'
} finally {
    [Environment]::SetEnvironmentVariable('BOUJOY_PREVIEW_URL', $previousPreviewUrl, 'Process')
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
        $serverProcess.WaitForExit(3000) | Out-Null
    }
    Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force -ErrorAction SilentlyContinue
}
