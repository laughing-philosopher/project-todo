# app.py
import os
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Define the path for the data file
DATA_FILE = 'project_data.json'

# Default project structure if data file doesn't exist
# Subpoints are now objects with 'text' and 'completed' status
DEFAULT_PROJECT_SECTIONS = [
    {
        "id": "section1",
        "name": "Section 1: Project Initiation & Planning",
        "subpoints": [
            {"text": "Define project scope and objectives", "completed": False},
            {"text": "Identify key stakeholders and roles", "completed": False},
            {"text": "Develop initial project timeline and budget", "completed": False}
        ],
        "progress": 0
    },
    {
        "id": "section2",
        "name": "Section 2: Requirement Gathering & Analysis",
        "subpoints": [
            {"text": "Conduct stakeholder interviews", "completed": False},
            {"text": "Document functional and non-functional requirements", "completed": False},
            {"text": "Analyze and prioritize requirements", "completed": False}
        ],
        "progress": 0
    },
    {
        "id": "section3",
        "name": "Section 3: Design & Prototyping",
        "subpoints": [
            {"text": "Create wireframes and mockups", "completed": False},
            {"text": "Develop database schema and system architecture", "completed": False},
            {"text": "Build and test interactive prototypes", "completed": False}
        ],
        "progress": 0
    },
    {
        "id": "section4",
        "name": "Section 4: Development & Implementation",
        "subpoints": [
            {"text": "Set up development environment", "completed": False},
            {"text": "Code and unit test modules/features", "completed": False},
            {"text": "Integrate components and perform system testing", "completed": False}
        ],
        "progress": 0
    },
    {
        "id": "section5",
        "name": "Section 5: Testing, Deployment & Review",
        "subpoints": [
            {"text": "Conduct User Acceptance Testing (UAT)", "completed": False},
            {"text": "Prepare deployment plan and deploy to production", "completed": False},
            {"text": "Post-implementation review and lessons learned", "completed": False}
        ],
        "progress": 0
    }
]

def load_project_data():
    """Loads project data from DATA_FILE. If not found, initializes with defaults."""
    if not os.path.exists(DATA_FILE):
        save_project_data(DEFAULT_PROJECT_SECTIONS)
        return DEFAULT_PROJECT_SECTIONS
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            # Basic validation/migration: ensure subpoints have 'completed' field
            for section in data:
                if 'subpoints' in section:
                    for i, sp in enumerate(section['subpoints']):
                        if isinstance(sp, str): # Old format
                            section['subpoints'][i] = {"text": sp, "completed": False}
                        elif isinstance(sp, dict) and 'completed' not in sp:
                            sp['completed'] = False # Add missing completed field
            return data
    except (IOError, json.JSONDecodeError):
        # If file is corrupted or unreadable, fallback to defaults and overwrite
        save_project_data(DEFAULT_PROJECT_SECTIONS)
        return DEFAULT_PROJECT_SECTIONS

def save_project_data(data):
    """Saves project data to DATA_FILE."""
    # Note: For hosting platforms like Vercel with ephemeral filesystems,
    # writing to a local file like this won't provide true persistence
    # across deployments or different serverless function invocations.
    # A database (e.g., Vercel Postgres, Supabase, FaunaDB) or a
    # dedicated storage solution (e.g., Vercel KV) would be needed.
    # For platforms like Render with persistent disk options, this approach can work.
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Load data once when the app starts
project_data_store = load_project_data()

@app.route('/')
def index():
    """Renders the main project tracker page with current data."""
    return render_template('index.html', sections=project_data_store)

@app.route('/api/update_task_status', methods=['POST'])
def update_task_status():
    """API endpoint to update a task's completion status."""
    global project_data_store
    try:
        data = request.get_json()
        section_id = data.get('sectionId')
        task_index = data.get('taskIndex')
        is_checked = data.get('isChecked')

        if section_id is None or task_index is None or is_checked is None:
            return jsonify({"success": False, "error": "Missing data"}), 400

        # Find the section and update the task
        section_updated = False
        new_section_progress = 0
        for section in project_data_store:
            if section['id'] == section_id:
                if 0 <= task_index < len(section['subpoints']):
                    section['subpoints'][task_index]['completed'] = is_checked
                    
                    # Recalculate section progress
                    completed_tasks = sum(1 for sp in section['subpoints'] if sp['completed'])
                    total_tasks = len(section['subpoints'])
                    section['progress'] = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
                    new_section_progress = section['progress']
                    section_updated = True
                    break
        
        if section_updated:
            save_project_data(project_data_store)
            return jsonify({"success": True, "newProgress": new_section_progress})
        else:
            return jsonify({"success": False, "error": "Section or task not found"}), 404

    except Exception as e:
        app.logger.error(f"Error updating task status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update_section_progress', methods=['POST'])
def update_section_progress_api():
    """API endpoint to update a section's overall progress and its tasks."""
    global project_data_store
    try:
        data = request.get_json()
        section_id = data.get('sectionId')
        new_progress = data.get('newProgress')

        if section_id is None or new_progress is None:
            return jsonify({"success": False, "error": "Missing data"}), 400
        
        new_progress = int(new_progress)
        if not (0 <= new_progress <= 100):
             return jsonify({"success": False, "error": "Progress out of range"}), 400

        section_updated = False
        for section in project_data_store:
            if section['id'] == section_id:
                section['progress'] = new_progress
                
                # Update task completion based on new progress
                total_tasks = len(section['subpoints'])
                if total_tasks > 0:
                    tasks_to_complete = round((new_progress / 100) * total_tasks)
                    for i, subpoint in enumerate(section['subpoints']):
                        subpoint['completed'] = (i < tasks_to_complete)
                
                section_updated = True
                break
        
        if section_updated:
            save_project_data(project_data_store)
            return jsonify({"success": True, "updatedTasks": section.get('subpoints', [])}) # Return updated tasks for UI sync
        else:
            return jsonify({"success": False, "error": "Section not found"}), 404
            
    except Exception as e:
        app.logger.error(f"Error updating section progress: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
