#!/bin/bash

# 🚀 Osservatorio Issue Creator - Fast & Intuitive
# Creato per @Gasta88 - Script rapido per automatizzare apertura issues
# Usage: ./create-issue.sh

set -e

# Colors for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🚀 Osservatorio Issue Creator    ║${NC}"
echo -e "${BLUE}║          Fast & Intuitive            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) not installed!${NC}"
    echo -e "${YELLOW}💡 Install with: sudo apt install gh${NC}"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub!${NC}"
    echo -e "${YELLOW}💡 Run: gh auth login${NC}"
    exit 1
fi

echo -e "${GREEN}✅ GitHub CLI ready!${NC}"
echo

# Quick templates for common issues
declare -A TEMPLATES=(
    ["bug"]="🐛 Bug Report"
    ["feature"]="✨ Feature Request"
    ["enhancement"]="🔧 Enhancement"
    ["docs"]="📝 Documentation"
    ["performance"]="⚡ Performance"
    ["security"]="🔐 Security"
    ["test"]="🧪 Testing"
    ["refactor"]="♻️ Refactoring"
)

# Available labels (comprehensive set)
declare -A LABEL_CATEGORIES=(
    ["type"]="bug,feature,enhancement,documentation,performance,security,test,refactor"
    ["priority"]="critical,high,medium,low"
    ["component"]="api,auth,cache,cli,config,database,dashboard,etl,integration,monitoring,security,testing"
    ["status"]="ready,in progress,blocked,review needed,waiting for info"
    ["effort"]="minutes,hours,days,weeks"
    ["scope"]="sprint,backlog,maintenance,research"
    ["impact"]="breaking,major,minor"
    ["platform"]="linux,windows,macos,docker"
    ["experience"]="beginner,intermediate,advanced"
)

# Function to show available labels
show_labels() {
    echo -e "${PURPLE}📋 Available Labels:${NC}"
    for category in "${!LABEL_CATEGORIES[@]}"; do
        echo -e "${CYAN}  $category:${NC} ${LABEL_CATEGORIES[$category]}"
    done
    echo
}

# Quick mode selection
echo -e "${YELLOW}🚀 Quick Mode Selection:${NC}"
echo "1. 📝 Interactive Mode (step-by-step)"
echo "2. ⚡ Express Mode (minimal input)"
echo "3. 📋 Template Mode (pre-filled)"
echo "4. 📖 Show Available Labels"
echo

read -p "Choose mode (1-4): " mode

case $mode in
    4)
        show_labels
        exit 0
        ;;
    2)
        # Express Mode
        echo -e "\n${CYAN}⚡ Express Mode${NC}"
        read -p "📌 Issue Title: " title
        read -p "📝 Brief Description: " description
        read -p "🏷️  Labels (comma-separated): " labels

        # Create issue quickly
        gh issue create --title "$title" --body "$description" --label "$labels"
        echo -e "${GREEN}✅ Issue created successfully!${NC}"
        exit 0
        ;;
    3)
        # Template Mode
        echo -e "\n${PURPLE}📋 Available Templates:${NC}"
        i=1
        for key in "${!TEMPLATES[@]}"; do
            echo "$i. ${TEMPLATES[$key]}"
            ((i++))
        done

        read -p "Select template (1-${#TEMPLATES[@]}): " template_choice

        # Convert choice to template key
        keys=($(echo "${!TEMPLATES[@]}" | tr ' ' '\n' | sort))
        selected_key=${keys[$((template_choice-1))]}

        echo -e "\n${CYAN}Selected: ${TEMPLATES[$selected_key]}${NC}"
        read -p "📌 Issue Title: " title

        # Auto-suggest labels based on template
        case $selected_key in
            "bug")
                suggested_labels="type: bug,priority: high,status: ready"
                ;;
            "feature")
                suggested_labels="type: feature,priority: medium,status: ready"
                ;;
            "performance")
                suggested_labels="type: performance,priority: high,component: database"
                ;;
            "security")
                suggested_labels="type: security,priority: critical,component: security"
                ;;
            *)
                suggested_labels="type: $selected_key,priority: medium"
                ;;
        esac

        echo -e "${YELLOW}💡 Suggested labels: $suggested_labels${NC}"
        read -p "🏷️  Labels (press Enter for suggested): " custom_labels
        labels=${custom_labels:-$suggested_labels}

        read -p "📝 Description: " description

        gh issue create --title "$title" --body "$description" --label "$labels"
        echo -e "${GREEN}✅ Issue created with template!${NC}"
        exit 0
        ;;
esac

# Interactive Mode (default)
echo -e "\n${CYAN}📝 Interactive Mode${NC}"
echo -e "${YELLOW}💡 Tip: Use Ctrl+C to cancel anytime${NC}"
echo

# Step 1: Title
read -p "📌 Issue Title: " title
if [[ -z "$title" ]]; then
    echo -e "${RED}❌ Title cannot be empty!${NC}"
    exit 1
fi

# Step 2: Type selection
echo -e "\n${PURPLE}🏷️  Issue Type:${NC}"
types=("bug" "feature" "enhancement" "documentation" "performance" "security" "test" "refactor")
for i in "${!types[@]}"; do
    echo "$((i+1)). ${types[$i]}"
done

read -p "Select type (1-${#types[@]}): " type_choice
issue_type=${types[$((type_choice-1))]}

# Step 3: Priority
echo -e "\n${PURPLE}⚡ Priority Level:${NC}"
priorities=("critical" "high" "medium" "low")
for i in "${!priorities[@]}"; do
    echo "$((i+1)). ${priorities[$i]}"
done

read -p "Select priority (1-${#priorities[@]}): " priority_choice
priority=${priorities[$((priority_choice-1))]}

# Step 4: Component (optional)
echo -e "\n${PURPLE}🔧 Component (optional):${NC}"
components=("api" "auth" "cache" "cli" "config" "database" "dashboard" "etl" "integration" "monitoring" "security" "testing")
echo "0. Skip"
for i in "${!components[@]}"; do
    echo "$((i+1)). ${components[$i]}"
done

read -p "Select component (0-${#components[@]}): " comp_choice
if [[ $comp_choice -ne 0 ]]; then
    component=${components[$((comp_choice-1))]}
fi

# Step 5: Description
echo -e "\n📝 Issue Description:"
echo -e "${YELLOW}💡 Tip: Use Markdown formatting. Press Ctrl+D when done.${NC}"
description=$(cat)

# Step 6: Effort estimation
echo -e "\n${PURPLE}⏱️  Effort Estimate:${NC}"
efforts=("minutes" "hours" "days" "weeks")
for i in "${!efforts[@]}"; do
    echo "$((i+1)). ${efforts[$i]}"
done

read -p "Select effort (1-${#efforts[@]}): " effort_choice
effort=${efforts[$((effort_choice-1))]}

# Build labels
labels="type: $issue_type,priority: $priority,effort: $effort"
if [[ -n "$component" ]]; then
    labels+=",component: $component"
fi

# Step 7: Additional labels (optional)
echo -e "\n${YELLOW}🏷️  Additional labels (optional):${NC}"
show_labels
read -p "Add more labels (comma-separated): " additional_labels

if [[ -n "$additional_labels" ]]; then
    labels+=",${additional_labels}"
fi

# Step 8: Review and confirm
echo -e "\n${CYAN}📋 Review Issue:${NC}"
echo -e "${YELLOW}Title:${NC} $title"
echo -e "${YELLOW}Labels:${NC} $labels"
echo -e "${YELLOW}Description Preview:${NC}"
echo "$description" | head -3
echo

read -p "Create this issue? (y/N): " confirm

if [[ $confirm =~ ^[Yy]$ ]]; then
    # Create the issue
    issue_url=$(gh issue create --title "$title" --body "$description" --label "$labels")

    echo -e "\n${GREEN}🎉 Success! Issue created:${NC}"
    echo -e "${BLUE}$issue_url${NC}"

    # Optional: Open in browser
    read -p "🌐 Open in browser? (y/N): " open_browser
    if [[ $open_browser =~ ^[Yy]$ ]]; then
        gh issue view --web $(echo $issue_url | grep -o '[0-9]*$')
    fi

else
    echo -e "${YELLOW}❌ Issue creation cancelled${NC}"
fi

echo -e "\n${BLUE}👋 Thanks for using Osservatorio Issue Creator!${NC}"
