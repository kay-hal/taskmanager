import anthropic
import logging
from typing import List
import datetime
import time
from .models import Task, TaskPriorities

class TaskPrioritizer:
    def __init__(self, api_key: str):
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not found in environment variables")
            raise ValueError("API key not configured")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.logger = logging.getLogger(__name__)

    def _build_prompt(self, tasks: List[Task], rules: List[str]) -> str:
        task_descriptions = "\n".join([
            f"- Task ID {task.id}: {task.description} (Status: {task.status}) \n"
            for task in tasks if task.status != "completed"
        ])
        
        rules_text = "\n".join([f"- {rule}" for rule in rules]) if rules else "No specific rules provided"
        
        # Get current timestamp with system timezone
        current_time = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
        
        return f"""here's a list of task descriptions
                \"\"\"
                {task_descriptions}
                \"\"\"

                and here is the prioritization statement about how to prioritize the tasks
                \"\"\"
                {rules_text}
                \"\"\"

                Current timestamp: {current_time}

                rank the tasks based on the prioritization statement and give me a json list of the specified schema. do not change anything in the task description. only give me the json list and nothing else"""

    def prioritize_tasks(self, tasks: List[Task], rules: List[str]) -> List[Task]:
        self.logger.info("Starting task prioritization with Claude")
        
        prompt = self._build_prompt(tasks, rules)
        self.logger.info(f"Prompt: {prompt}")

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                tools=[{
                    "name": "prioritize_tasks",
                    "description": "rank the tasks based on the prioritization statement strictly ensuring the most important tasks are ranked higher. Return a structured list of task priorities with explanations using the prioritize_tasks tool",
                    "input_schema": TaskPriorities.model_json_schema()
                }],
                tool_choice={"type": "tool", "name": "prioritize_tasks"}
            )

            tool_calls = [content for content in message.content if content.type == "tool_use"]
            if not tool_calls or not tool_calls[0].input:
                return tasks

            priority_data = TaskPriorities(**tool_calls[0].input)
            priority_map = {item.task_id: item.priority for item in priority_data.tasks}
            
            for task in tasks:
                if task.id in priority_map:
                    task.priority = priority_map[task.id]

        except Exception as e:
            self.logger.error(f"Error processing priorities: {str(e)}")
            return tasks

        self.logger.info("Task prioritization completed")
        return tasks 