from jira import JIRA
import datetime

# --- Configuration ---
# Replace with your Jira instance URL, email, API token, and project key
JIRA_URL = "https://your-jira-instance.atlassian.net"
JIRA_AUTH_EMAIL = "  "
# It's highly recommended to use environment variables or a config file for credentials
# instead of hardcoding them in the script.
JIRA_API_TOKEN = " "
PROJECT_KEY = " "

# Specify custom fields you want to extract by their Jira ID or name
# Example: CUSTOM_FIELD_STORY_POINTS = "customfield_10016"
# You can find custom field IDs by inspecting the Jira API response for an issue
# or by going to Jira Admin -> Issues -> Custom Fields and checking the URL for the field's ID.
CUSTOM_FIELDS_TO_EXTRACT = {
    # "Story Points": "customfield_10016", # Example: Replace with actual ID
    # "Another Custom Field": "customfield_10020", # Example
}

OUTPUT_FILE_NAME = f"{PROJECT_KEY}_SRS_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

# --- Helper Functions ---

def connect_to_jira(url, email, token):
    '''Connects to the Jira instance.'''
    print(f"Connecting to Jira at {url}...")
    try:
        jira_options = {'server': url}
        jira_client = JIRA(options=jira_options, basic_auth=(email, token))
        # Test connection by getting server info
        server_info = jira_client.server_info()
        print(f"Successfully connected to Jira: {server_info['baseUrl']} (Version: {server_info['version']})")
        return jira_client
    except Exception as e:
        print(f"Error connecting to Jira: {e}")
        return None

def get_project_issues(jira_client, project_key):
    '''Fetches all issues for a given project key.'''
    print(f"Fetching issues for project: {project_key}...")
    issues_data = []
    try:
        # Adjust JQL as needed. This fetches all issues in the project.
        # You might want to filter by status, type, etc.
        # e.g., f'project = "{project_key}" AND status = "In Progress"'.
        jql_query = f'project = "{project_key}" ORDER BY issuetype ASC, created DESC'
        block_size = 100
        block_num = 0
        while True:
            start_at = block_num * block_size
            issues = jira_client.search_issues(jql_query, startAt=start_at, maxResults=block_size)
            if not issues:
                break
            issues_data.extend(issues)
            block_num += 1
            print(f"Fetched {len(issues)} issues (total: {len(issues_data)})...")
        print(f"Total issues fetched: {len(issues_data)}")
        return issues_data
    except Exception as e:
        print(f"Error fetching issues for project {project_key}: {e}")
        return []

def extract_issue_details(issue, jira_client):
    '''Extracts relevant details from a Jira issue object.'''
    details = {
        "id": issue.key,
        "type": issue.fields.issuetype.name,
        "summary": issue.fields.summary,
        "description": issue.fields.description if issue.fields.description else "N/A",
        "status": issue.fields.status.name,
        "reporter": issue.fields.reporter.displayName if issue.fields.reporter else "N/A",
        "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "N/A",
        "created": issue.fields.created,
        "updated": issue.fields.updated,
        "priority": issue.fields.priority.name if issue.fields.priority else "N/A",
        "labels": list(issue.fields.labels),
        "parent_link": None, # For epics linked to stories
        "child_issues": [], # For epics or stories with tasks/subtasks
        "linked_issues": [], # For other issue links (e.g., "relates to", "blocks")
        "custom_fields": {}
    }

    # Parent/Epic Link (differs for classic vs next-gen projects)
    # For classic projects, Epic Link is often a custom field like 'customfield_10010' or 'customfield_10014'
    # For next-gen projects, it's usually issue.fields.parent
    try:
        if hasattr(issue.fields, "parent") and issue.fields.parent:
            details["parent_link"] = issue.fields.parent.key
        # Add specific custom field ID for "Epic Link" if you know it
        # elif hasattr(issue.fields, "customfield_XXXXX") and getattr(issue.fields, "customfield_XXXXX"): # Replace XXXXX
        #     details["parent_link"] = getattr(issue.fields, "customfield_XXXXX")
    except AttributeError:
        pass # Field doesn't exist

    # Subtasks (standard field)
    if hasattr(issue.fields, "subtasks") and issue.fields.subtasks:
        details["child_issues"] = [subtask.key for subtask in issue.fields.subtasks]

    # Other issue links
    if hasattr(issue.fields, "issuelinks") and issue.fields.issuelinks:
        for link in issue.fields.issuelinks:
            link_type = link.type.name
            if hasattr(link, "outwardIssue"):
                linked_issue_key = link.outwardIssue.key
                details["linked_issues"].append(f"{link_type} {linked_issue_key}")
            elif hasattr(link, "inwardIssue"):
                linked_issue_key = link.inwardIssue.key
                details["linked_issues"].append(f"{link_type} (inward) {linked_issue_key}")

    # Custom Fields
    for cf_name, cf_id in CUSTOM_FIELDS_TO_EXTRACT.items():
        try:
            cf_value = getattr(issue.fields, cf_id, "N/A")
            if hasattr(cf_value, 'value'): # For fields that are objects (e.g., select lists)
                details["custom_fields"][cf_name] = cf_value.value
            elif isinstance(cf_value, list) and cf_value and hasattr(cf_value[0], 'value'):
                 details["custom_fields"][cf_name] = ', '.join([item.value for item in cf_value])
            else:
                details["custom_fields"][cf_name] = cf_value if cf_value else "N/A"
        except AttributeError:
            details["custom_fields"][cf_name] = "N/A (field not found)"

    return details

def format_srs_markdown(project_key, all_issues_details):
    '''Formats the extracted Jira data into a Markdown string for the SRS.'''
    srs_content = f"# Software Requirements Specification (SRS) for {project_key}\n\n"
    srs_content += f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    srs_content += "## Table of Contents\n"
    srs_content += "- [Introduction](#introduction)\n"
    srs_content += "- [Overall Description](#overall-description)\n"
    srs_content += "- [System Features (Jira Issues)](#system-features-jira-issues)\n"

    # Create a dictionary to hold issues by type for easier processing
    issues_by_type = {}
    for issue_detail in all_issues_details:
        issue_type = issue_detail["type"]
        if issue_type not in issues_by_type:
            issues_by_type[issue_type] = []
        issues_by_type[issue_type].append(issue_detail)

    # Add issue types to ToC
    for issue_type in sorted(issues_by_type.keys()):
        srs_content += f"  - [{issue_type}s](#{issue_type.lower().replace(' ', '-')}s)\n"
    srs_content += "\n"

    srs_content += "## 1. Introduction\n"
    srs_content += "This document outlines the software requirements for the project...\n\n"
    srs_content += "## 2. Overall Description\n"
    srs_content += "Product perspective, product functions, user characteristics...\n\n"
    srs_content += "## 3. System Features (Jira Issues)\n"
    srs_content += "This section details the features, enhancements, and tasks managed in Jira.\n\n"

    # Process Epics first, then stories, then tasks/subtasks
    # This is a simplified hierarchy. You might need more complex logic for deep nesting.

    issue_order = ["Epic", "Story", "Task", "Sub-task"] # Define desired order

    processed_issues = set()

    def format_single_issue(issue_detail, indent_level=0):
        nonlocal processed_issues
        if issue_detail["id"] in processed_issues: # Avoid duplicate printing if linked
            return ""
        processed_issues.add(issue_detail["id"])

        indent = "  " * indent_level
        content = f"{indent}### {issue_detail['type']}: {issue_detail['id']} - {issue_detail['summary']}\n\n"
        content += f"{indent}- **Status:** {issue_detail['status']}\n"
        content += f"{indent}- **Reporter:** {issue_detail['reporter']}\n"
        content += f"{indent}- **Assignee:** {issue_detail['assignee']}\n"
        content += f"{indent}- **Priority:** {issue_detail['priority']}\n"
        content += f"{indent}- **Created:** {issue_detail['created']}\n"
        content += f"{indent}- **Updated:** {issue_detail['updated']}\n"
        if issue_detail["labels"]:
            content += f"{indent}- **Labels:** { ', '.join(issue_detail['labels']) }\n"

        if issue_detail["description"] and issue_detail["description"] != "N/A":
            content += f"{indent}- **Description:**\n{indent}  ```\n{indent}  {issue_detail['description'].replace('\r\n', f'\n{indent}  ') if issue_detail['description'] else 'N/A'}\n{indent}  ```\n"
        else:
            content += f"{indent}- **Description:** N/A\n"

        if issue_detail["parent_link"]:
            content += f"{indent}- **Parent/Epic Link:** {issue_detail['parent_link']}\n"

        if issue_detail["custom_fields"]:
            content += f"{indent}- **Custom Fields:**\n"
            for cf_name, cf_value in issue_detail['custom_fields'].items():
                content += f"{indent}  - **{cf_name}:** {cf_value}\n"

        if issue_detail["linked_issues"]:
            content += f"{indent}- **Linked Issues:**\n"
            for link in issue_detail['linked_issues']:
                content += f"{indent}  - {link}\n"
        content += f"\n"
        return content

    # Hierarchical processing (simplified)
    # 1. Epics
    if "Epic" in issues_by_type:
        srs_content += f"## Epics\n\n"
        for epic in sorted(issues_by_type["Epic"], key=lambda x: x["id"]):
            srs_content += format_single_issue(epic, indent_level=0)
            # Find stories belonging to this epic
            if "Story" in issues_by_type:
                for story in sorted(issues_by_type["Story"], key=lambda x: x["id"]):
                    if story["parent_link"] == epic["id"]:
                        srs_content += format_single_issue(story, indent_level=1)
                        # Find tasks/subtasks belonging to this story
                        for task_type in ["Task", "Sub-task"]:
                            if task_type in issues_by_type:
                                for task in sorted(issues_by_type[task_type], key=lambda x: x["id"]):
                                    if task.get("parent_link") == story["id"] or task["id"] in story.get("child_issues", []):
                                        srs_content += format_single_issue(task, indent_level=2)
                                        # Find subtasks of this task (if applicable)
                                        if task_type == "Task" and "Sub-task" in issues_by_type:
                                            for subtask_item in sorted(issues_by_type["Sub-task"], key=lambda x: x["id"]):
                                                if subtask_item["id"] in task.get("child_issues", []):
                                                    srs_content += format_single_issue(subtask_item, indent_level=3)
    # Orphan stories (not linked to an Epic processed above)
    if "Story" in issues_by_type:
        srs_content += f"## Stories (Orphaned or Standalone)\n\n"
        for story in sorted(issues_by_type["Story"], key=lambda x: x["id"]):
            if story["id"] not in processed_issues:
                srs_content += format_single_issue(story, indent_level=0)
                for task_type in ["Task", "Sub-task"]:
                    if task_type in issues_by_type:
                        for task in sorted(issues_by_type[task_type], key=lambda x: x["id"]):
                            if (task.get("parent_link") == story["id"] or task["id"] in story.get("child_issues", [])) and task["id"] not in processed_issues:
                                srs_content += format_single_issue(task, indent_level=1)
                                if task_type == "Task" and "Sub-task" in issues_by_type:
                                    for subtask_item in sorted(issues_by_type["Sub-task"], key=lambda x: x["id"]):
                                        if subtask_item["id"] in task.get("child_issues", []) and subtask_item["id"] not in processed_issues:
                                            srs_content += format_single_issue(subtask_item, indent_level=2)

    # Other issue types not yet processed (e.g., Tasks not under a story)
    for issue_type in issue_order:
        if issue_type not in ["Epic", "Story"] and issue_type in issues_by_type:
            # Check if we need a header for this type if it hasn't been implicitly created
            # This is a bit simplistic; you might want more robust checking
            if f"## {issue_type}s" not in srs_content and f"## {issue_type} (Orphaned or Standalone)" not in srs_content:
                 srs_content += f"## {issue_type}s (Orphaned or Standalone)\n\n"
            for issue_detail in sorted(issues_by_type[issue_type], key=lambda x: x["id"]):
                if issue_detail["id"] not in processed_issues:
                    srs_content += format_single_issue(issue_detail, indent_level=0)
                    # Handle sub-tasks of these tasks if they are directly fetched and not part of a story hierarchy
                    if issue_type == "Task" and "Sub-task" in issues_by_type:
                        for subtask_item in sorted(issues_by_type["Sub-task"], key=lambda x: x["id"]):
                             if subtask_item["id"] in issue_detail.get("child_issues", []) and subtask_item["id"] not in processed_issues:
                                srs_content += format_single_issue(subtask_item, indent_level=1)

    return srs_content

# --- Main Execution ---
def main():
    '''Main function to orchestrate the Jira data extraction and SRS generation.'''
    print("Starting Jira to SRS document generation...")

    jira_client = connect_to_jira(JIRA_URL, JIRA_AUTH_EMAIL, JIRA_API_TOKEN)
    if not jira_client:
        print("Exiting due to Jira connection failure.")
        return

    raw_issues = get_project_issues(jira_client, PROJECT_KEY)
    if not raw_issues:
        print(f"No issues found for project {PROJECT_KEY} or error in fetching.")
        return

    print(f"Extracting details for {len(raw_issues)} issues...")
    all_issues_details = []
    for i, issue in enumerate(raw_issues):
        print(f"Processing issue {i+1}/{len(raw_issues)}: {issue.key}")
        details = extract_issue_details(issue, jira_client)
        all_issues_details.append(details)

    print("Formatting data for SRS document...")
    srs_document_content = format_srs_markdown(PROJECT_KEY, all_issues_details)

    try:
        with open(OUTPUT_FILE_NAME, "w", encoding="utf-8") as f:
            f.write(srs_document_content)
        print(f"Successfully generated SRS document: {OUTPUT_FILE_NAME}")
    except IOError as e:
        print(f"Error writing SRS document to file: {e}")

if __name__ == "__main__":
    main()


'''
