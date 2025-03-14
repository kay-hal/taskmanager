import TaskManager from './components/TaskManager'

function App() {
  return (
    <div className="min-h-screen bg-coral-light/20 dark:bg-anysphere">
      <header className="bg-coral shadow-lg dark:bg-anysphere-light">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-cream dark:text-anysphere-text">
            <span className="text-forest bg-cream px-2 py-1 rounded mr-2 dark:text-anysphere-accent dark:bg-anysphere-dark">mindex</span>
            Task Manager
          </h1>
        </div>
      </header>
      <TaskManager />
    </div>
  )
}

export default App