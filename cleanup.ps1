$filesToDelete = @(
    'ACTIVITIES_COORDINATOR_ASSIGNMENT_FIXED.md',
    'ANALYTICS_DATA_FETCHING_FIXED.md',
    'BACKEND_CONNECTION_MAP.txt',
    'COORDINATOR_ASSIGNMENT_GUIDE.md',
    'FINAL_CHECKLIST.txt',
    'FLOW_DIAGRAM.txt',
    'HOD_EDIT_EMAIL_GUIDE.md',
    'HOD_EDIT_SUMMARY.txt',
    'HOD_IMPLEMENTATION_SUMMARY.md',
    'HOD_MANAGEMENT_GUIDE.md',
    'HOD_QUICK_START.md',
    'HOD_SETUP_CHECKLIST.md',
    'HOD_SYSTEM_OVERVIEW.txt',
    'POSTGRESQL_MIGRATION_COMPLETE.md',
    'POSTGRESQL_MIGRATION_SUMMARY.md',
    'QUICK_REFERENCE.txt',
    'QUICK_TEST_GUIDE.txt',
    'REGISTRATION_VALIDATION_COMPLETE.md',
    'SKIP_BUTTONS_REMOVED.md',
    'SUBACTIVITY_IMPLEMENTATION_SUMMARY.md',
    'SUBACTIVITY_TESTING.md',
    'VERIFICATION_CHECKLIST.txt',
    'LOGIN_FIXES_SUMMARY.md',
    'FIX_IMPORT_ERRORS.md'
)

foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "Deleted: $file"
    }
}

Write-Host "`nCleanup complete! Remaining important guides:"
Get-ChildItem *.md, *.txt, *.bat | Select-Object Name
