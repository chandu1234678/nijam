#!/bin/bash
# START FRESH - Commands for each person

echo "═══════════════════════════════════════════════════════════"
echo "STEP 1: Delete repository on GitHub first!"
echo "Go to: https://github.com/chandu1234678/NIjam/settings"
echo "Delete it and create a new empty one"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Press Enter when done..."
read

# Remove old git history
rm -rf .git

# Initialize fresh git
git init
git config user.name "Chandu"
git config user.email "bc833498@gmail.com"

# Add only README for first commit
git add README.md
git commit -m "docs: Initialize NIjam project

Co-authored-by: Kaushik <kaushikram51@gmail.com>
Co-authored-by: Abhinav <sb346@gmail.com>"

# Connect to new repository
git remote add origin https://github.com/chandu1234678/NIjam.git
git branch -M main
git push -u origin main

echo ""
echo "✅ DONE! First commit pushed."
echo "Now tell Kaushik to run his commands!"
