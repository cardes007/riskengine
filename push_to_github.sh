#!/bin/bash

echo "🚀 GitHub Push Helper"
echo "===================="
echo ""

echo "This script will help you push your code to GitHub."
echo ""
echo "If you get asked for a username and password:"
echo "- Username: your GitHub username (cardes007)"
echo "- Password: use a Personal Access Token (not your GitHub password)"
echo ""

echo "To create a Personal Access Token:"
echo "1. Go to GitHub.com and sign in"
echo "2. Click your profile picture → Settings"
echo "3. Scroll down → Developer settings → Personal access tokens → Tokens (classic)"
echo "4. Generate new token → Generate new token (classic)"
echo "5. Give it a name like 'Company Cohort Web'"
echo "6. Select 'repo' scope"
echo "7. Click 'Generate token'"
echo "8. Copy the token (it looks like: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)"
echo ""

read -p "Press Enter when you're ready to push..."

echo "Pushing to GitHub..."
git push origin main

echo ""
echo "If the push was successful, you should see your code on GitHub!"
echo "If it failed, check the error message above." 