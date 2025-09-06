#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = ["requests>=2.25.0"]
# ///

"""
TodoWrite Synchronization Hook
Intercepts TodoWrite tool calls and automatically creates persistent Shrimp tasks
"""

import json
import sys
import requests
import uuid
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils.constants import ensure_session_log_dir

class TodoWriteSync:
    def __init__(self):
        self.shrimp_api_url = "http://localhost:4000/api"  # Fixed port to 4000
        self.todo_to_task_map = {}  # Maps todo IDs to Shrimp task IDs
        self.session_todos = {}  # Tracks todos by session ID
    
    def intercept_todowrite(self, tool_call: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Intercept TodoWrite tool calls and create Shrimp tasks
        """
        tool_name = tool_call.get('tool_name', '')
        
        if tool_name != 'TodoWrite':
            return tool_call  # Pass through non-TodoWrite calls
        
        try:
            tool_input = tool_call.get('tool_input', {})
            todos = tool_input.get('todos', [])
            
            if not todos:
                return tool_call  # No todos to sync
            
            print(f"[TodoWriteSync] Intercepting TodoWrite with {len(todos)} todos for session {session_id}", file=sys.stderr)
            
            # Process each todo
            synced_todos = self.sync_todos_to_shrimp(todos, session_id)
            
            # Store session todos for status tracking
            self.session_todos[session_id] = synced_todos
            
            # Log sync operation
            self.log_sync_operation(session_id, synced_todos)
            
            # Return the original tool call (don't modify the behavior)
            return tool_call
            
        except Exception as error:
            print(f"[TodoWriteSync] Sync failed, continuing with original call: {error}", file=sys.stderr)
            return tool_call  # Fail gracefully, don't break TodoWrite
    
    def sync_todos_to_shrimp(self, todos: List[Dict], session_id: str) -> List[Dict]:
        """
        Synchronize todos to Shrimp Task Manager
        """
        synced_todos = []
        
        for todo in todos:
            try:
                todo_id = todo.get('id') or self.generate_todo_id()
                shrimp_task_id = self.todo_to_task_map.get(todo_id)
                
                if not shrimp_task_id:
                    # Create new Shrimp task
                    shrimp_task_id = self.create_shrimp_task_from_todo(todo, session_id)
                    self.todo_to_task_map[todo_id] = shrimp_task_id
                else:
                    # Update existing Shrimp task status
                    self.update_shrimp_task_status(shrimp_task_id, todo.get('status', 'pending'))
                
                synced_todos.append({
                    **todo,
                    'id': todo_id,
                    'shrimpTaskId': shrimp_task_id,
                    'sessionId': session_id
                })
                
            except Exception as error:
                print(f"[TodoWriteSync] Failed to sync todo '{todo.get('content', 'unknown')}': {error}", file=sys.stderr)
                # Continue with other todos even if one fails
                synced_todos.append({
                    **todo,
                    'syncError': str(error)
                })
        
        return synced_todos
    
    def create_shrimp_task_from_todo(self, todo: Dict, session_id: str) -> str:
        """
        Create a Shrimp task from a TodoWrite todo
        """
        task_data = {
            "name": todo.get('content', 'Untitled Todo'),
            "description": f"TodoWrite task: {todo.get('content', '')}\n\nOriginal todo ID: {todo.get('id', '')}\nActiveForm: {todo.get('activeForm', 'Processing todo')}",
            "priority": self.map_todo_priority_to_shrimp(todo.get('priority', 'medium')),
            "status": self.map_todo_status_to_shrimp(todo.get('status', 'pending')),
            "metadata": {
                "source": "TodoWrite",
                "originalTodoId": todo.get('id', ''),
                "sessionId": session_id,
                "activeForm": todo.get('activeForm', 'Processing todo'),
                "createdAt": time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "type": "todo_sync"
            },
            "implementationGuide": f"This task was automatically synced from TodoWrite system.\n\nTodo Content: {todo.get('content', '')}\nSession ID: {session_id}",
            "verificationCriteria": "Mark as completed when the todo task is finished.",
            "relatedFiles": []
        }
        
        try:
            # Use Shrimp split_tasks API to create the task
            response = self.call_shrimp_api('split_tasks', {
                "updateMode": "append",
                "tasksRaw": json.dumps([task_data]),
                "globalAnalysisResult": f"TodoWrite synchronization for session {session_id}"
            })
            
            if response and response.get('tasks') and len(response['tasks']) > 0:
                shrimp_task_id = response['tasks'][0].get('id')
                print(f"[TodoWriteSync] Created Shrimp task {shrimp_task_id} for todo '{todo.get('content', 'unknown')}'", file=sys.stderr)
                return shrimp_task_id
            else:
                raise Exception('Failed to get task ID from Shrimp response')
        
        except Exception as error:
            print(f"[TodoWriteSync] Failed to create Shrimp task: {error}", file=sys.stderr)
            raise error
    
    def update_shrimp_task_status(self, shrimp_task_id: str, todo_status: str):
        """
        Update Shrimp task status based on todo status
        """
        try:
            self.call_shrimp_api('update_task', {
                "taskId": shrimp_task_id,
                "metadata": {
                    "lastTodoSync": time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    "todoStatus": todo_status
                }
            })
            
            # If todo is completed, verify the task in Shrimp
            if todo_status == 'completed':
                self.call_shrimp_api('verify_task', {
                    "taskId": shrimp_task_id,
                    "score": 85,  # Auto-complete synced todos
                    "summary": "TodoWrite task completed - automatically verified through sync middleware"
                })
            
            print(f"[TodoWriteSync] Updated Shrimp task {shrimp_task_id} status to match todo status: {todo_status}", file=sys.stderr)
        
        except Exception as error:
            print(f"[TodoWriteSync] Failed to update Shrimp task {shrimp_task_id}: {error}", file=sys.stderr)
            raise error
    
    def map_todo_status_to_shrimp(self, todo_status: str) -> str:
        """Map TodoWrite status to Shrimp status"""
        status_map = {
            'pending': 'pending',
            'in_progress': 'in_progress',
            'completed': 'completed'
        }
        return status_map.get(todo_status, 'pending')
    
    def map_todo_priority_to_shrimp(self, todo_priority: str) -> str:
        """Map todo priority to Shrimp priority"""
        priority_map = {
            'low': 'low',
            'medium': 'medium', 
            'high': 'high',
            'urgent': 'high'
        }
        return priority_map.get(todo_priority, 'medium')
    
    def call_shrimp_api(self, method: str, params: Dict) -> Optional[Dict]:
        """Call Shrimp Task Manager API"""
        try:
            url = f"{self.shrimp_api_url}/mcp/shrimp-task-manager/{method}"
            response = requests.post(url, json=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as error:
            print(f"[TodoWriteSync] Shrimp API call failed for {method}: {error}", file=sys.stderr)
            raise error
    
    def generate_todo_id(self) -> str:
        """Generate unique todo ID"""
        return f"todo_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    
    def log_sync_operation(self, session_id: str, synced_todos: List[Dict]):
        """Log sync operation to session directory"""
        try:
            log_dir = ensure_session_log_dir(session_id)
            log_path = log_dir / 'todowrite_sync.json'
            
            # Read existing log data or initialize empty list
            if log_path.exists():
                with open(log_path, 'r') as f:
                    try:
                        log_data = json.load(f)
                    except (json.JSONDecodeError, ValueError):
                        log_data = []
            else:
                log_data = []
            
            # Append new sync operation
            log_data.append({
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'sessionId': session_id,
                'syncedTodos': synced_todos,
                'totalSynced': len(synced_todos),
                'successfulSyncs': len([t for t in synced_todos if 'syncError' not in t])
            })
            
            # Write back to file with formatting
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as error:
            print(f"[TodoWriteSync] Failed to log sync operation: {error}", file=sys.stderr)


def main():
    """Main hook execution"""
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        tool_name = input_data.get('tool_name', '')
        session_id = input_data.get('session_id', 'unknown')
        
        # Only process TodoWrite tool calls
        if tool_name == 'TodoWrite':
            sync = TodoWriteSync()
            # Process the tool call
            processed_call = sync.intercept_todowrite(input_data, session_id)
            
            # Output success message for TodoWrite interception
            print(f"[TodoWriteSync] Successfully processed TodoWrite call for session {session_id}", file=sys.stderr)
        
        # Exit with success (allows tool call to proceed)
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Gracefully handle JSON decode errors
        sys.exit(0)
    except Exception as error:
        # Handle any other errors gracefully - don't block tool execution
        print(f"[TodoWriteSync] Hook error: {error}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()