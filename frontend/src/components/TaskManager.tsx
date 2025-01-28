import React, { useState, useEffect } from 'react';
import { Play, Pause, Check } from 'lucide-react';

const TaskManager = () => {
  const [tasks, setTasks] = useState([]);
  const [taskInput, setTaskInput] = useState('');
  const [priorityRules, setPriorityRules] = useState('');
  const [timers, setTimers] = useState({});
  const [intervalIds, setIntervalIds] = useState({});

  useEffect(() => {
    fetchTasks();
    // Cleanup intervals on unmount
    return () => {
      Object.values(intervalIds).forEach(id => clearInterval(id));
    };
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await fetch('http://localhost:5005/api/tasks', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        // credentials: 'include'
      });
      const data = await response.json();
      console.log('Received tasks:', data);
      setTasks(data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    try {
      await fetch('http://localhost:5005/api/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // credentials: 'include',
        body: JSON.stringify({ description: taskInput }),
      });
      setTaskInput('');
      fetchTasks();
    } catch (error) {
      console.error('Error adding task:', error);
    }
  };

  const handleUpdatePriorityRules = async (e) => {
    e.preventDefault();
    try {
      await fetch('http://localhost:5005/api/priorities', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        // credentials: 'include',
        body: JSON.stringify({ rules: priorityRules }),
      });
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

  const updateTaskTimer = async (taskId, status) => {
    try {
      await fetch(`http://localhost:5005/api/tasks/${taskId}/timer`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        // credentials: 'include',
        body: JSON.stringify({ status, time: timers[taskId] || 0 }),
      });
      fetchTasks();
    } catch (error) {
      console.error('Error updating task timer:', error);
    }
  };

  const completeTask = async (taskId) => {
    pauseTimer(taskId);
    try {
      await fetch(`http://localhost:5005/api/tasks/${taskId}/timer`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        // credentials: 'include',
        body: JSON.stringify({ status: 'completed', time: timers[taskId] || 0 }),
      });
      fetchTasks();
    } catch (error) {
      console.error('Error completing task:', error);
    }
  };

  const sortedTasks = [...tasks].sort((a, b) => a.priority - b.priority);

  return (
    <div className="p-8 max-w-6xl mx-auto bg-cream">
      <div className="space-y-8">
        <form onSubmit={handleAddTask} className="space-y-4">
          <input
            type="text"
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            placeholder="Enter new task..."
            className="w-full p-4 border-2 border-coral rounded-lg bg-cream-light 
            focus:outline-none focus:ring-2 focus:ring-coral-light focus:border-coral
            text-forest-dark placeholder-coral/50 text-lg"
          />
          <button 
            type="submit" 
            className="px-6 py-3 bg-coral text-cream rounded-lg hover:bg-coral-dark 
            transition-colors duration-200 font-semibold text-lg shadow-md"
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
            className="w-full p-4 border-2 border-forest rounded-lg bg-cream-light 
            focus:outline-none focus:ring-2 focus:ring-forest-light focus:border-forest
            text-forest-dark placeholder-forest/50 text-lg"
          />
          <button 
            type="submit" 
            className="px-6 py-3 bg-forest text-cream rounded-lg hover:bg-forest-dark 
            transition-colors duration-200 font-semibold text-lg shadow-md"
          >
            Update Priority Rules
          </button>
        </form>

        <div className="overflow-x-auto rounded-lg shadow-lg">
          <table className="min-w-full border-collapse bg-cream-light">
            <thead>
              <tr className="bg-coral text-cream">
                <th className="p-4 text-left font-semibold">Task</th>
                <th className="p-4 text-left font-semibold">Priority</th>
                <th className="p-4 text-left font-semibold">Status</th>
                <th className="p-4 text-left font-semibold">Timer</th>
                <th className="p-4 text-left font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedTasks && Array.isArray(sortedTasks) ? (
                sortedTasks.map((task) => (
                  <tr key={task.id} className="border-t border-coral/20 hover:bg-cream-dark">
                    <td className="p-4 text-forest-dark">{task.description}</td>
                    <td className="p-4 text-forest-dark">{task.priority}</td>
                    <td className="p-4 text-forest-dark">{task.status}</td>
                    <td className="p-4 text-forest-dark">{formatTime(timers[task.id] || 0)}</td>
                    <td className="p-4 space-x-2">
                      {task.status !== 'completed' && (
                        <>
                          <button
                            onClick={() => startTimer(task.id)}
                            className="p-2 bg-forest text-cream rounded hover:bg-forest-dark
                            transition-colors duration-200 disabled:opacity-50"
                            disabled={task.status === 'active'}
                          >
                            <Play size={16} />
                          </button>
                          <button
                            onClick={() => pauseTimer(task.id)}
                            className="p-2 bg-coral text-cream rounded hover:bg-coral-dark
                            transition-colors duration-200 disabled:opacity-50"
                            disabled={task.status !== 'active'}
                          >
                            <Pause size={16} />
                          </button>
                          <button
                            onClick={() => completeTask(task.id)}
                            className="p-2 bg-forest-light text-cream rounded hover:bg-forest
                            transition-colors duration-200"
                          >
                            <Check size={16} />
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-forest-dark">No tasks available</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TaskManager;