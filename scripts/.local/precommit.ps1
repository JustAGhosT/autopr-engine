# Local helper to run volume-aware pre-commit across the full repo with background fixing

$env:AUTOPR_PRECOMMIT_VOLUME = '300'
$env:AUTOPR_PRECOMMIT_QUEUE_ISSUES = '1'
$env:AUTOPR_BG_FIX = '1'
$env:AUTOPR_ENABLE_AUTOFIX = '1'
$env:AUTOPR_AUTOFIX_MIN_VOLUME = '0'
$env:AUTOPR_BG_BATCH = '50'
$env:AUTOPR_BG_TYPES = 'E302,F401,F841'

pre-commit run volume-precommit --all-files --hook-stage manual


