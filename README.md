# free-genai-bootcamp-2025

## Week 1 notes:

### Resetting the Git Repository

#### Overview
This is my first project maintaining a Git repository, and as part of the bootcamp, the backend version control became a bit messy due to the removal of the API. To improve documentation and tracking of changes, I decided to reset the repository. This reset aims to make it easier to review the process and ensure smoother development moving forward.

This document outlines the steps I took to reset the Git repository and my rationale.

### Steps Taken to Reset Git
1. Added Back the Original lang-portal to Establish v1.0

To preserve a stable version of the code before any significant changes, I started by adding the original lang-portal back into the repository. This allowed me to establish a clean version, marking it as v1.0.

2. Replaced the backend-flask Folder

I replaced the existing backend-flask folder with a new one provided by the bootcamp, which had some APIs removed. This was done so that I could rewrite the APIs for the bootcamp's specific requirements.

3. Staged, Committed, and Pushed the Changes

After replacing the folder, I staged the changes to ensure Git tracked the deletion of the old folder and the addition of the new one. Once staged, I committed the changes locally, marking the point where the old backend was replaced with the new version. I then pushed these updates to the remote repository to synchronize it with the new version, making the changes accessible to collaborators.

4. Tagged the New Version

To mark this milestone, I tagged the new version (v2.0), allowing easy reference in the future.

### Fixing the API
Used Cursor Chat to analyse the system and propose plans.
Used GitHub Copilot for work (free access as a student) to refine plans and prompts for Cursor Composer.
Needed to split the task into two steps as Cursor was not able to handle the full task at once.


Step 1: Ask Cursor to implement the fixing plan provided in api_Fix.md:

> The API in the provided .py files has been modified, causing the backend in the backend-flask folder to no longer work properly with the frontend in the frontend-react folder.

> Task:

> Implement the fixing plan provided in api_Fix.md to restore API functionality.
> Document any changes made to the code with explanations of what changes are being made and why. Ensure that the documentation is included directly in the code as comments, but keep it concise and not too verbose. Only document changes where modifications have been made, not where no changes were necessary. Clearly indicate that the changes were to "Fix the API for Bootcamp Week 1."
> Additional Context:

> Project Structure: Provide an overview of the project structure, especially the locations of the backend-flask and frontend-react folders.
> API Schema: Include the routes_and_schema.md file or its contents to help Cursor understand the expected API routes and schema.
> Current Issues: Describe any specific issues or errors that are currently occurring due to the API modifications.
> Documentation Request: Please document any changes made to the code with explanations of what changes are being made and why. Ensure that the documentation is included directly in the code as comments, but keep it concise and not too verbose. This will help in understanding the modifications and ensuring that the API functionality is restored correctly.

Step 2: Ask Cursor to execute the tests from api_Fix.md:

> The API in the provided .py files has been modified, you should have fixed the API issues, and now we are focusing on testing the fix.

> Task:

> Ensure that all tests documented in api_Fix.md are executed and pass successfully.
> Provide details about the testing environment, such as the base URL for the API and any necessary setup steps.
> Testing Steps:

> Ensure the API works with the frontend while maintaining a clean code structure.
> Add the /api prefix while keeping the original response formats that the frontend expects.
> Execute all tests documented in api_Fix.md and ensure they pass successfully.

> Additional Context:

> Project Structure: Provide an overview of the project structure, especially the locations of the backend-flask and frontend-react folders.
> API Schema: Include the routes_and_schema.md file or its contents to help Cursor understand the expected API routes and schema.
> Current Issues: Describe any specific issues or errors that are currently occurring due to the API modifications.



Testing executed in Cursor Composer:

> I'll execute the tests from api_Fix.md:
> Testing raw words endpoint:
> ✅ Success! Received a list of words with basic fields (id, kanji, romaji, english)
> Testing study session review:
> ✅ Success! Received "Review recorded successfully" message
> Testing error handling:
> ✅ Success! Received 400 error for missing 'correct' field
> Database verification:
> ✅ Success! Found the newly created review record
> All tests from api_Fix.md have passed successfully. The new endpoints are working as expected:
> Raw words endpoint returns unfiltered word lists
> Review endpoint properly records study results
> Error handling works correctly
> Database updates are being made properly
