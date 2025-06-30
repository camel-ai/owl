#!/bin/bash

# Git Repository Setup Script for Custom Builds
# Usage: ./setup_repo.sh [project_directory] [project_name] [description]

PROJECT_DIR=${1:-$(pwd)}
PROJECT_NAME=${2:-"custom-build-project"}
DESCRIPTION=${3:-"Custom build project"}

echo "🚀 Setting up Git repository for: $PROJECT_NAME"
echo "📁 Directory: $PROJECT_DIR"

cd "$PROJECT_DIR" || exit 1

# Initialize git if not already done
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "🚫 Creating .gitignore..."
    cat > .gitignore << EOF
# macOS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Temporary files
*.tmp
*.temp
*~

# Log files
*.log

# Editor files
.vscode/
.idea/
*.swp
*.swo

# Personal notes
personal_notes/
scratch/
notes.txt

# Build artifacts (adjust as needed)
dist/
build/
*.zip
*.tar.gz
EOF
    echo "✅ .gitignore created"
fi

# Create README if it doesn't exist
if [ ! -f "README.md" ]; then
    echo "📖 Creating README.md..."
    cat > README.md << EOF
# $PROJECT_NAME

$DESCRIPTION

## Project Overview

Custom build project created on $(date +"%B %d, %Y")

## Structure

\`\`\`
$(find . -type d -name ".git" -prune -o -type d -print | head -10 | sort)
\`\`\`

## Usage

[Add usage instructions here]

## Development

[Add development notes here]

---

**Created**: $(date +"%B %d, %Y")  
**Status**: Active Development
EOF
    echo "✅ README.md created"
fi

# Add all files
echo "📋 Adding files to Git..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    # Commit
    echo "💾 Creating initial commit..."
    git commit -m "Initial commit: $PROJECT_NAME

$DESCRIPTION

Created on $(date +"%B %d, %Y")"
    echo "✅ Initial commit created"
fi

# Show status
echo "📊 Repository status:"
git status --short
git log --oneline -n 3

echo ""
echo "🎉 Repository setup complete!"
echo ""
echo "🔗 To add a remote repository:"
echo "   git remote add origin https://github.com/yourusername/$PROJECT_NAME.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "📈 To continue working:"
echo "   git add ."
echo "   git commit -m 'Your commit message'"
echo "   git push"
