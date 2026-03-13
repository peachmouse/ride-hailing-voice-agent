# Kill ALL python processes that might be LangGraph or LiveKit
Get-Process -Name python* -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Output "Killing python PID $($_.Id)"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

# Also kill anything on port 2024
$conns = Get-NetTCPConnection -LocalPort 2024 -ErrorAction SilentlyContinue
foreach ($c in $conns) {
    if ($c.OwningProcess -gt 0) {
        Write-Output "Killing PID $($c.OwningProcess) on port 2024"
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 2

# Delete the LangGraph API cache
$cachePath = "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent\.langgraph_api"
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force
    Write-Output "Deleted .langgraph_api cache"
}

Write-Output "All clean. Ready to restart."
