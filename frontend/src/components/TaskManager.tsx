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

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="space-y-6">
        <form onSubmit={handleAddTask} className="space-y-4">
          <input
            type="text"
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            placeholder="Enter new task..."
            className="w-full p-2 border rounded"
          />
          <button type="submit" className="px-4 py-2 bg-blue-500 text-white rounded">
            Add Task
          </button>
        </form>

        <form onSubmit={handleUpdatePriorityRules} className="space-y-4">
          <input
            type="text"
            value={priorityRules}
            onChange={(e) => setPriorityRules(e.target.value)}
            placeholder="Enter priority rules..."
            className="w-full p-2 border rounded"
          />
          <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded">
            Update Priority Rules
          </button>
        </form>

        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-4 text-left">Task</th>
                <th className="p-4 text-left">Priority</th>
                <th className="p-4 text-left">Status</th>
                <th className="p-4 text-left">Timer</th>
                <th className="p-4 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tasks && Array.isArray(tasks) ? (
                tasks.map((task) => (
                  <tr key={task.id} className="border-t">
                    <td className="p-4">{task.description}</td>
                    <td className="p-4">{task.priority}</td>
                    <td className="p-4">{task.status}</td>
                    <td className="p-4">{formatTime(timers[task.id] || 0)}</td>
                    <td className="p-4 space-x-2">
                      {task.status !== 'completed' && (
                        <>
                          <button
                            onClick={() => startTimer(task.id)}
                            className="p-2 bg-green-500 text-white rounded"
                            disabled={task.status === 'active'}
                          >
                            <Play size={16} />
                          </button>
                          <button
                            onClick={() => pauseTimer(task.id)}
                            className="p-2 bg-yellow-500 text-white rounded"
                            disabled={task.status !== 'active'}
                          >
                            <Pause size={16} />
                          </button>
                          <button
                            onClick={() => completeTask(task.id)}
                            className="p-2 bg-blue-500 text-white rounded"
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
                  <td colSpan={5} className="p-4 text-center">No tasks available</td>
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