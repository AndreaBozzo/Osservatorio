# PowerShell script to create GitHub issues for 10-day sprint
# Run this script after authenticating with: gh auth login

Write-Host "Creating GitHub issues for 10-day sprint..." -ForegroundColor Green

# Issue 1: Day 3 Query Builder
Write-Host "Creating Issue 1: Day 3 Query Builder..." -ForegroundColor Yellow
gh issue create --title "Day 3: DuckDB Query Builder Pattern Implementation" --body (Get-Content "temp_issue_day3_query_builder.md" -Raw) --label "enhancement,database,high-priority,day-3,query-builder"

# Issue 2: Day 3 Performance Testing
Write-Host "Creating Issue 2: Day 3 Performance Testing..." -ForegroundColor Yellow
gh issue create --title "Day 3: DuckDB Performance Testing & Optimization" --body (Get-Content "temp_issue_day3_performance.md" -Raw) --label "performance,database,testing,high-priority,day-3,optimization"

# Issue 3: Day 4 Docker Setup
Write-Host "Creating Issue 3: Day 4 Docker Setup..." -ForegroundColor Yellow
gh issue create --title "Day 4: PostgreSQL Docker Environment Setup" --body (Get-Content "temp_issue_day4_docker.md" -Raw) --label "infrastructure,database,docker,high-priority,day-4,postgresql"

# Issue 4: Day 4 SQLAlchemy Models
Write-Host "Creating Issue 4: Day 4 SQLAlchemy Models..." -ForegroundColor Yellow
gh issue create --title "Day 4: SQLAlchemy Models for Metadata Management" --body (Get-Content "temp_issue_day4_sqlalchemy.md" -Raw) --label "database,models,sqlalchemy,high-priority,day-4,metadata"

# Issue 5: Day 5 Migrations
Write-Host "Creating Issue 5: Day 5 Migrations..." -ForegroundColor Yellow
gh issue create --title "Day 5: Alembic Migration System Setup" --body (Get-Content "temp_issue_day5_migrations.md" -Raw) --label "database,migrations,alembic,high-priority,day-5,infrastructure"

# Issue 6: Day 5 Integration Testing
Write-Host "Creating Issue 6: Day 5 Integration Testing..." -ForegroundColor Yellow
gh issue create --title "Day 5: PostgreSQL Integration Testing & Production Features" --body (Get-Content "temp_issue_day5_integration.md" -Raw) --label "database,integration,postgresql,high-priority,day-5,production"

# Issue 7: Day 6 Storage Interface
Write-Host "Creating Issue 7: Day 6 Storage Interface..." -ForegroundColor Yellow
gh issue create --title "Day 6: Abstract Storage Interface Design" --body (Get-Content "temp_issue_day6_storage_interface.md" -Raw) --label "architecture,interfaces,storage,high-priority,day-6,foundation"

# Issue 8: Day 6 Concrete Adapters
Write-Host "Creating Issue 8: Day 6 Concrete Adapters..." -ForegroundColor Yellow
gh issue create --title "Day 6: Concrete Storage Adapter Implementations" --body (Get-Content "temp_issue_day6_concrete_adapters.md" -Raw) --label "storage,adapters,implementation,high-priority,day-6,database"

Write-Host "All issues created successfully!" -ForegroundColor Green
Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow

# Clean up temporary files
Remove-Item "temp_issue_day3_query_builder.md" -ErrorAction SilentlyContinue
Remove-Item "temp_issue_day3_performance.md" -ErrorAction SilentlyContinue
Remove-Item "temp_issue_day4_docker.md" -ErrorAction SilentlyContinue
Remove-Item "temp_issue_day4_sqlalchemy.md" -ErrorAction SilentlyContinue
Remove-Item "temp_issue_day5_migrations.md" -ErrorAction SilentlyContinue
Remove-Item "temp_issue_day5_integration.md" -ErrorAction SilentlyContinue
Remove-Item "temp_issue_day6_storage_interface.md" -ErrorAction SilentlyContinue
Remove-Item "temp_issue_day6_concrete_adapters.md" -ErrorAction SilentlyContinue

Write-Host "Temporary files cleaned up!" -ForegroundColor Green
Write-Host "Sprint issues setup complete!" -ForegroundColor Cyan
