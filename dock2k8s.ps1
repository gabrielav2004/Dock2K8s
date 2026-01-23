# Dock2K8s - Docker Compose to Kubernetes Converter
# PowerShell wrapper script

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$cliPath = Join-Path $scriptDir "cli.py"

# Run the CLI with all arguments
python $cliPath @Arguments

# Preserve exit code
exit $LASTEXITCODE
