#!/bin/bash

echo "🚀 Risk Engine GitHub Push Helper"
echo "================================="
echo ""

echo "This script will help you push your Risk Engine code to GitHub."
echo ""
echo "When prompted for authentication:"
echo "- Username: cardes007"
echo "- Password: Use your Personal Access Token (not your GitHub password)"
echo ""

echo "If you don't have a Personal Access Token yet:"
echo "1. Go to GitHub.com and sign in"
echo "2. Click your profile picture → Settings"
echo "3. Scroll down → Developer settings → Personal access tokens → Tokens (classic)"
echo "4. Generate new token → Generate new token (classic)"
echo "5. Give it a name like 'Risk Engine'"
echo "6. Select 'repo' scope"
echo "7. Click 'Generate token'"
echo "8. Copy the token (it looks like: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)"
echo ""

read -p "Press Enter when you're ready to push..."

echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "If the push was successful, you should see your code at:"
echo "https://github.com/cardes007/riskengine"
echo ""
echo "If it failed, check the error message above." 