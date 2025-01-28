import TaskManager from './components/TaskManager'

function App() {
  return (
    <div className="min-h-screen bg-coral-light/20">
      <header className="bg-coral shadow-lg">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-cream">
            <span className="text-forest bg-cream px-2 py-1 rounded mr-2">mindex</span>
            Task Manager
          </h1>
        </div>
      </header>
      <TaskManager />
    </div>
  )
}

export default App