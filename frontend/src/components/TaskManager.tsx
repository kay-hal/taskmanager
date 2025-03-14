import React, { useState, useEffect } from 'react';
import { Play, Pause, Check, Edit2, Save, X, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

// Add TypeScript interface for Task
interface Task {
  id: number;
  description: string;
  priority: number;
  status: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  total_time: number;
}

const TaskManager = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskInput, setTaskInput] = useState('');
  const [priorityRules, setPriorityRules] = useState('');
  const [timers, setTimers] = useState<Record<number, number>>({});
  const [intervalIds, setIntervalIds] = useState<Record<number, number>>({});
  const [sortedTasks, setSortedTasks] = useState<Task[]>([]);
  const [completedTasks, setCompletedTasks] = useState<Task[]>([]);
  const [uncompletedTasks, setUncompletedTasks] = useState<Task[]>([]);
  const [editingTaskId, setEditingTaskId] = useState<number | null>(null);
  const [editingTaskValue, setEditingTaskValue] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchTasks();
    // Cleanup intervals on unmount
    return () => {
      Object.values(intervalIds).forEach(id => clearInterval(id));
    };
  }, []);

  useEffect(() => {
    if (sortedTasks && Array.isArray(sortedTasks)) {
      const completed = sortedTasks.filter(task => task.status === 'completed');
      const uncompleted = sortedTasks.filter(task => task.status !== 'completed');
      setCompletedTasks(completed);
      setUncompletedTasks(uncompleted);
    }
  }, [sortedTasks]);

  const sortTasksByPriority = (tasksToSort: Task[]): Task[] => {
    return [...tasksToSort].sort((a, b) => a.priority - b.priority);
  };

  const fetchTasks = async () => {
    try {
      const tasks = await api.get('/tasks');
      const sortedByPriority = sortTasksByPriority(tasks);
      setTasks(sortedByPriority);
      setSortedTasks(sortedByPriority);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    try {
      await api.post('/tasks', { description: taskInput });
      setTaskInput('');
      fetchTasks();
    } catch (error) {
      console.error('Error adding task:', error);
    }
  };

  const duplicateTask = async (taskDescription: string) => {
    try {
      await api.post('/tasks', { description: `[Copy] ${taskDescription}` });
      fetchTasks();
    } catch (error) {
      console.error('Error duplicating task:', error);
    }
  };

  const handleUpdatePriorityRules = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/priorities', { rules: priorityRules });
      setPriorityRules('');
      fetchTasks();
    } catch (error) {
      console.error('Error updating priority rules:', error);
    }
  };

  const startTimer = (taskId) => {
    if (intervalIds[taskId]) return;
    
    const startTime = Date.now() - (timers[taskId] || 0);
    const intervalId = setInterval(() => {
      setTimers(prev => ({
        ...prev,
        [taskId]: Date.now() - startTime
      }));
    }, 1000);

    setIntervalIds(prev => ({
      ...prev,
      [taskId]: intervalId
    }));

    updateTaskTimer(taskId, 'active');
  };

  const pauseTimer = (taskId) => {
    if (intervalIds[taskId]) {
      clearInterval(intervalIds[taskId]);
      setIntervalIds(prev => {
        const newIds = { ...prev };
        delete newIds[taskId];
        return newIds;
      });
      updateTaskTimer(taskId, 'paused');
    }
  };

  const formatTime = (ms) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const updateTaskTimer = async (taskId: number, status: string) => {
    try {
      await api.put(`/tasks/${taskId}/timer`, {
        status,
        time: timers[taskId] || 0
      });
    } catch (error) {
      console.error('Error updating task timer:', error);
    }
  };

  const completeTask = async (taskId) => {
    pauseTimer(taskId);
    try {
      await api.put(`/tasks/${taskId}/timer`, {
        status: 'completed',
        time: timers[taskId] || 0
      });
      fetchTasks();
    } catch (error) {
      console.error('Error completing task:', error);
    }
  };

  const startEditing = (taskId, description) => {
    setEditingTaskId(taskId);
    setEditingTaskValue(description);
  };

  const cancelEditing = () => {
    setEditingTaskId(null);
    setEditingTaskValue('');
  };

  const saveTaskEdit = async (taskId) => {
    if (!editingTaskValue.trim()) {
      return;
    }
    
    try {
      await api.put(`/tasks/${taskId}`, {
        description: editingTaskValue
      });
      setEditingTaskId(null);
      setEditingTaskValue('');
      fetchTasks();
    } catch (error) {
      console.error('Error updating task description:', error);
    }
  };

  const handleEditKeyDown = (e, taskId) => {
    if (e.key === 'Enter') {
      saveTaskEdit(taskId);
    } else if (e.key === 'Escape') {
      cancelEditing();
    }
  };

  const refreshTaskPriorities = async () => {
    try {
      setIsRefreshing(true);
      // Call the backend to trigger re-prioritization without changing rules
      await api.post('/priorities/refresh', {});
      await fetchTasks();
    } catch (error) {
      console.error('Error refreshing task priorities:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto bg-cream dark:bg-anysphere">
      <div className="space-y-8">
        <form onSubmit={handleAddTask} className="space-y-4">
          <input
            type="text"
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            placeholder="Enter new task..."
            className="w-full p-4 border-2 border-coral rounded-lg bg-cream-light dark:bg-anysphere-light
            dark:border-anysphere-accent dark:text-anysphere-text dark:placeholder-anysphere-accent/50
            focus:outline-none focus:ring-2 focus:ring-coral-light focus:border-coral dark:focus:ring-anysphere-accent dark:focus:border-anysphere-accent
            text-forest-dark placeholder-coral/50 text-lg"
          />
          <button 
            type="submit" 
            className="px-6 py-3 bg-coral text-cream rounded-lg hover:bg-coral-dark 
            transition-colors duration-200 font-semibold text-lg shadow-md dark:bg-anysphere-accent dark:hover:bg-anysphere-accent/80"
          >
            Add Task
          </button>
        </form>

        <form onSubmit={handleUpdatePriorityRules} className="space-y-4">
          <input
            type="text"
            value={priorityRules}
            onChange={(e) => setPriorityRules(e.target.value)}
            placeholder="Enter priority rules..."
            className="w-full p-4 border-2 border-forest rounded-lg bg-cream-light dark:bg-anysphere-light
            dark:border-anysphere-blue dark:text-anysphere-text dark:placeholder-anysphere-blue/50
            focus:outline-none focus:ring-2 focus:ring-forest-light focus:border-forest dark:focus:ring-anysphere-blue dark:focus:border-anysphere-blue
            text-forest-dark placeholder-forest/50 text-lg"
          />
          <button 
            type="submit" 
            className="px-6 py-3 bg-forest text-cream rounded-lg hover:bg-forest-dark 
            transition-colors duration-200 font-semibold text-lg shadow-md dark:bg-anysphere-blue dark:hover:bg-anysphere-blue/80"
          >
            Update Priority Rules
          </button>
        </form>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-forest-dark dark:text-anysphere-text">Active Tasks</h2>
            <button 
              onClick={refreshTaskPriorities}
              className="p-2 text-forest hover:text-forest-dark transition-colors duration-200 dark:text-anysphere-accent dark:hover:text-anysphere-accent/80"
              title="Refresh Task Priorities"
              disabled={isRefreshing}
            >
              <RefreshCw size={20} className={isRefreshing ? "animate-spin" : ""} />
            </button>
          </div>
          <div className="overflow-x-auto rounded-lg shadow-lg">
            <table className="min-w-full border-collapse bg-cream-light dark:bg-anysphere-light">
              <thead>
                <tr className="bg-coral text-cream dark:bg-anysphere-dark">
                  <th className="p-4 text-left font-semibold dark:text-anysphere-text">Task</th>
                  <th className="p-4 text-left font-semibold dark:text-anysphere-text">Status</th>
                  <th className="p-4 text-left font-semibold dark:text-anysphere-text">Timer</th>
                  <th className="p-4 text-left font-semibold dark:text-anysphere-text">Actions</th>
                </tr>
              </thead>
              <tbody>
                {uncompletedTasks.length > 0 ? (
                  uncompletedTasks.map((task) => (
                    <tr key={task.id} className="border-t border-coral/20 dark:border-anysphere-accent/20 hover:bg-cream-dark dark:hover:bg-anysphere-selection/40">
                      <td className="p-4 text-forest-dark dark:text-anysphere-text">
                        {editingTaskId === task.id ? (
                          <div className="flex items-center space-x-2">
                            <input
                              type="text"
                              value={editingTaskValue}
                              onChange={(e) => setEditingTaskValue(e.target.value)}
                              onKeyDown={(e) => handleEditKeyDown(e, task.id)}
                              className="p-2 w-full border border-coral/50 dark:border-anysphere-accent/50 rounded bg-cream dark:bg-anysphere-light
                              focus:outline-none focus:ring-1 focus:ring-coral focus:border-coral dark:focus:ring-anysphere-accent dark:focus:border-anysphere-accent"
                              autoFocus
                            />
                            <button
                              onClick={() => saveTaskEdit(task.id)}
                              className="p-1 text-forest dark:text-anysphere-accent hover:text-forest-dark dark:hover:text-anysphere-accent/80"
                              title="Save"
                            >
                              <Save size={16} />
                            </button>
                            <button
                              onClick={cancelEditing}
                              className="p-1 text-coral dark:text-anysphere-purple hover:text-coral-dark dark:hover:text-anysphere-purple/80"
                              title="Cancel"
                            >
                              <X size={16} />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between group">
                            <span>{task.description}</span>
                            <button
                              onClick={() => startEditing(task.id, task.description)}
                              className="hidden group-hover:block ml-2 text-forest/70 dark:text-anysphere-text/70 
                              hover:text-forest dark:hover:text-anysphere-text"
                              title="Edit Task"
                            >
                              <Edit2 size={16} />
                            </button>
                          </div>
                        )}
                      </td>
                      <td className="p-4 text-forest-dark dark:text-anysphere-text">{task.status}</td>
                      <td className="p-4 text-forest-dark dark:text-anysphere-text">{formatTime(timers[task.id] || 0)}</td>
                      <td className="p-4 space-x-2">
                        <button
                          onClick={() => startTimer(task.id)}
                          className="p-2 bg-forest text-cream rounded hover:bg-forest-dark
                          transition-colors duration-200 disabled:opacity-50 dark:bg-anysphere-accent dark:hover:bg-anysphere-accent/80"
                          disabled={task.status === 'active'}
                        >
                          <Play size={16} />
                        </button>
                        <button
                          onClick={() => pauseTimer(task.id)}
                          className="p-2 bg-coral text-cream rounded hover:bg-coral-dark
                          transition-colors duration-200 disabled:opacity-50 dark:bg-anysphere-purple dark:hover:bg-anysphere-purple/80"
                          disabled={task.status !== 'active'}
                        >
                          <Pause size={16} />
                        </button>
                        <button
                          onClick={() => completeTask(task.id)}
                          className="p-2 bg-forest-light text-cream rounded hover:bg-forest
                          transition-colors duration-200 dark:bg-anysphere-blue dark:hover:bg-anysphere-blue/80"
                        >
                          <Check size={16} />
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-forest-dark dark:text-anysphere-text">No active tasks</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="border-t-2 border-forest/30 dark:border-anysphere-accent/30 my-8"></div>

        {completedTasks.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-forest-dark dark:text-anysphere-text">Completed Tasks</h2>
            <div className="overflow-x-auto rounded-lg shadow-lg">
              <table className="min-w-full border-collapse bg-cream-light/80 dark:bg-anysphere-light/80">
                <thead>
                  <tr className="bg-forest text-cream dark:bg-anysphere-accent/70">
                    <th className="p-4 text-left font-semibold dark:text-anysphere-text">Task</th>
                    <th className="p-4 text-left font-semibold dark:text-anysphere-text">Status</th>
                    <th className="p-4 text-left font-semibold dark:text-anysphere-text">Timer</th>
                    <th className="p-4 text-left font-semibold dark:text-anysphere-text">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {completedTasks.map((task) => (
                    <tr key={task.id} className="border-t border-forest/20 dark:border-anysphere-accent/20 hover:bg-cream-dark dark:hover:bg-anysphere-selection/40">
                      <td className="p-4 text-forest-dark/70 dark:text-anysphere-text/70">{task.description}</td>
                      <td className="p-4 text-forest-dark/70 dark:text-anysphere-text/70">{task.status}</td>
                      <td className="p-4 text-forest-dark/70 dark:text-anysphere-text/70">{formatTime(timers[task.id] || 0)}</td>
                      <td className="p-4">
                        <button
                          onClick={() => duplicateTask(task.description)}
                          className="p-2 bg-forest-light text-cream rounded hover:bg-forest
                          transition-colors duration-200 dark:bg-anysphere-blue dark:hover:bg-anysphere-blue/80"
                          title="Duplicate Task"
                        >
                          Duplicate
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskManager;