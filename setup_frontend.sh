# Create a new React project with Vite because Create React App is so 2020
npm create vite@latest frontend -- --template react
cd frontend

# Install dependencies (and pray they're all compatible)
npm install lucide-react tailwindcss postcss autoprefixer

# Initialize Tailwind CSS
npx tailwindcss init -p

# Add Tailwind directives to src/index.css
echo '@tailwind base;
@tailwind components;
@tailwind utilities;' > src/index.css

# Start the development server (and cross your fingers)
npm run dev