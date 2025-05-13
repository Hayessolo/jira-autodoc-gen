# jira-autodoc-gen
'''
This script connects to a Jira instance, extracts project data (epics, stories, tasks, subtasks),
and formats it into a basic structure suitable for a Software Requirements Specification (SRS) document.
'''
'''
**How to Use:**

1.  **Install Python Jira Library:**
    ```bash
    pip install jira
    ```

2.  **Configure the Script:**
    *   Open the script (`jira_srs_generator.py`).
    *   Update `JIRA_URL`, `JIRA_AUTH_EMAIL`, `JIRA_API_TOKEN`, and `PROJECT_KEY` with your Jira details.
    *   **Security Note:** For `JIRA_API_TOKEN`, it's best practice to use environment variables or a configuration file rather than hardcoding it directly in the script, especially if you plan to share or version control this script.
        *   To generate an API token: Go to your Atlassian account settings (usually `https://id.atlassian.com/manage-profile/security/api-tokens`), create an API token, and use that token as your password in the script or when prompted.
    *   Update `CUSTOM_FIELDS_TO_EXTRACT` if you need to pull specific custom field data. You'll need the custom field ID (e.g., `customfield_10016`). You can find this by:
        *   Inspecting the JSON response from the Jira API for an issue that has the field.
        *   Going to Jira Admin > Issues > Custom Fields. Click on the custom field, and the ID is often in the URL.

3.  **Run the Script:**
    ```bash
    python jira_srs_generator.py
    ```

4.  **Output:**
    *   The script will generate a Markdown file (e.g., `PMS_SRS_YYYYMMDD_HHMMSS.md`) in the same directory where the script is run.
    *   This Markdown file will contain the extracted Jira issues formatted in a basic SRS structure.

**Key Features & Customization:**

*   **Authentication:** Uses basic authentication with email and API token.
*   **Issue Fetching:** Retrieves all issues from the specified project.
*   **Field Extraction:** Extracts common fields (ID, type, summary, description, status, reporter, assignee, created, updated, priority, labels).
*   **Relationships:**
    *   Attempts to identify parent/epic links (note: the custom field ID for "Epic Link" might need adjustment for classic Jira projects; next-gen projects use a standard `parent` field).
    *   Lists subtasks.
    *   Lists other linked issues (e.g., "relates to", "blocks").
*   **Custom Fields:** Includes a dictionary `CUSTOM_FIELDS_TO_EXTRACT` to specify custom fields you want to include.
*   **Output Format:** Generates a Markdown file.
    *   The `format_srs_markdown` function can be heavily customized to change the structure, content, and formatting of the output document (e.g., to HTML, DOCX using libraries like `python-docx`, or another format).
*   **Hierarchy:** The script attempts a basic hierarchical ordering (Epics -> Stories -> Tasks/Sub-tasks). This logic in `format_srs_markdown` might need refinement based on your specific project structure and how you link issues.
*   **Error Handling:** Basic error handling for connection and file operations.

**Further Enhancements:**

*   **Configuration File:** Move Jira credentials and custom field mappings to a separate configuration file (e.g., `config.ini` or `config.json`) for better security and manageability.
*   **Advanced JQL:** Allow more complex JQL queries for fetching issues (e.g., filter by specific versions, sprints, or statuses).
*   **Attachment Handling:** Extract and link/embed attachments from Jira issues.
*   **More Sophisticated Templating:** Use a templating engine like Jinja2 for more flexible SRS document generation.
*   **Different Output Formats:** Add support for exporting to HTML, PDF, or DOCX.
*   **GUI:** Create a simple graphical user interface (e.g., using Tkinter, PyQt) for users who are not comfortable with command-line scripts.
*   **Incremental Updates:** Logic to update an existing SRS document instead of always generating a new one.
*   **Detailed Logging:** Implement more comprehensive logging for debugging and tracking.
*   **Recursive Hierarchy:** Improve the hierarchical display to handle arbitrarily nested issues if your project uses them extensively.
'''