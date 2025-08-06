#!/bin/bash

echo "🚀 Company Cohort Web Deployment Helper"
echo "========================================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    echo ""
    exit 1
fi

# Check if remote is set
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "⚠️  No remote repository found. Please add your GitHub repository:"
    echo "   git remote add origin https://github.com/yourusername/your-repo.git"
    echo ""
fi

echo "📋 Deployment Options:"
echo "1. Vercel (Frontend) + Railway (Backend) - Recommended"
echo "2. Netlify (Frontend) + Render (Backend)"
echo "3. Heroku (Full Stack)"
echo ""

read -p "Choose deployment option (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🎯 Deploying to Vercel + Railway"
        echo ""
        echo "📝 Steps:"
        echo "1. Push your code to GitHub"
        echo "2. Deploy backend to Railway:"
        echo "   - Go to railway.app"
        echo "   - Create new project from GitHub"
        echo "   - Set root directory to 'backend/'"
        echo "3. Deploy frontend to Vercel:"
        echo "   - Go to vercel.com"
        echo "   - Import your GitHub repository"
        echo "   - Add environment variable: VITE_BACKEND_URL=https://your-railway-url.railway.app"
        echo ""
        echo "🔗 Useful links:"
        echo "- Railway: https://railway.app"
        echo "- Vercel: https://vercel.com"
        ;;
    2)
        echo ""
        echo "🎯 Deploying to Netlify + Render"
        echo ""
        echo "📝 Steps:"
        echo "1. Push your code to GitHub"
        echo "2. Deploy backend to Render:"
        echo "   - Go to render.com"
        echo "   - Create new Web Service from GitHub"
        echo "   - Set root directory to 'backend/'"
        echo "   - Build command: pip install -r requirements.txt"
        echo "   - Start command: uvicorn main:app --host 0.0.0.0 --port \$PORT"
        echo "3. Deploy frontend to Netlify:"
        echo "   - Go to netlify.com"
        echo "   - Create new site from Git"
        echo "   - Build command: npm run build"
        echo "   - Publish directory: dist"
        echo "   - Add environment variable: VITE_BACKEND_URL=https://your-render-url.onrender.com"
        echo ""
        echo "🔗 Useful links:"
        echo "- Render: https://render.com"
        echo "- Netlify: https://netlify.com"
        ;;
    3)
        echo ""
        echo "🎯 Deploying to Heroku"
        echo ""
        echo "📝 Steps:"
        echo "1. Install Heroku CLI:"
        echo "   brew tap heroku/brew && brew install heroku"
        echo "2. Login to Heroku:"
        echo "   heroku login"
        echo "3. Create Heroku app:"
        echo "   heroku create your-app-name"
        echo "4. Deploy backend:"
        echo "   cd backend"
        echo "   git add ."
        echo "   git commit -m 'Deploy backend'"
        echo "   git push heroku main"
        echo "5. Deploy frontend (separate repository recommended)"
        echo ""
        echo "🔗 Useful links:"
        echo "- Heroku: https://heroku.com"
        ;;
    *)
        echo "❌ Invalid option. Please choose 1, 2, or 3."
        exit 1
        ;;
esac

echo ""
echo "✅ Configuration files created:"
echo "- vercel.json (for Vercel deployment)"
echo "- backend/Procfile (for backend deployment)"
echo "- backend/runtime.txt (Python version)"
echo "- DEPLOYMENT.md (detailed instructions)"
echo ""
echo "📝 Next steps:"
echo "1. Update CORS origins in backend/main.py with your actual frontend domain"
echo "2. Push changes to GitHub"
echo "3. Follow the deployment steps above"
echo ""
echo "🎉 Happy deploying!" 