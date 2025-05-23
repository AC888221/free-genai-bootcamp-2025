# Lang Portal Backend Documentation

[Jump to Bootcamp Week 1: Backend Implementation Report](https://github.com/AC888221/free-genai-bootcamp-2025/blob/main/lang-portal/backend-flask/README.md#bootcamp-week-1-backend-implementation-report)

## Getting Started

### Prerequisites
- Python 3.7 or higher
- Flask
- SQLite3
- Required Python packages (listed in `requirements.txt`)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/AC888221/free-genai-bootcamp-2025.git
   cd lang-portal/backend-flask
   ```

2. **Set Up a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the Database**
   ```bash
   invoke init-db
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```
   The Flask app will start on port `5000`.

### API Endpoints
The backend provides several API endpoints for managing study sessions, groups, and words. All endpoints are prefixed with `/api`. For example:
- **Create a Study Session**: `POST /api/study-sessions`
- **Submit a Review**: `POST /api/study-sessions/:id/review`
- **Get Group Words**: `GET /api/groups/:id/words/raw`


# API Documentation

## Base URL
`http://localhost:5000/api`

## Endpoints

### 1. Create a Study Session
- **Endpoint**: `POST /study-sessions`
- **Description**: Creates a new study session.
- **Request Body**:
  ```json
  {
    "group_id": 1,
    "study_activity_id": 1,
    "created_at": "2024-03-20T12:00:00Z"
  }
  ```
- **Response**:
  - **201 Created**: Returns the created study session object.
    ```json
    {
      "id": 1,
      "group_id": 1,
      "study_activity_id": 1,
      "created_at": "2024-03-20T12:00:00Z"
    }
    ```

### 2. Submit a Review
- **Endpoint**: `POST /study-sessions/:id/review`
- **Description**: Submits a review for a specific study session.
- **Path Parameters**:
  - `id`: The ID of the study session.
- **Request Body**:
  ```json
  {
    "word_id": 1,
    "correct": true
  }
  ```
- **Response**:
  - **201 Created**: Returns a success message.
    ```json
    {
      "message": "Review recorded successfully"
    }
    ```
  - **400 Bad Request**: Returns an error if required fields are missing.
    ```json
    {
      "error": "Missing required fields"
    }
    ```
  - **500 Internal Server Error**: Returns an error if there is a server issue.
    ```json
    {
      "error": "Error message"
    }
    ```

### 3. Get Group Words
- **Endpoint**: `GET /groups/:id/words/raw`
- **Description**: Retrieves a list of words associated with a specific group.
- **Path Parameters**:
  - `id`: The ID of the group.
- **Response**:
  - **200 OK**: Returns a list of words.
    ```json
    [
      {
        "id": 1,
        "jiantizi": "学习",
        "pinyin": "xué xí",
        "english": "study"
      },
      {
        "id": 2,
        "jiantizi": "书",
        "pinyin": "shū",
        "english": "book"
      }
    ]
    ```
  - **404 Not Found**: Returns an error if the group does not exist.
    ```json
    {
      "error": "Group not found"
    }
    ```

### 4. Get Study Session Details
- **Endpoint**: `GET /study-sessions/:id`
- **Description**: Retrieves details of a specific study session.
- **Path Parameters**:
  - `id`: The ID of the study session.
- **Response**:
  - **200 OK**: Returns the study session details.
    ```json
    {
      "id": 1,
      "group_id": 1,
      "study_activity_id": 1,
      "created_at": "2024-03-20T12:00:00Z"
    }
    ```
  - **404 Not Found**: Returns an error if the study session does not exist.
    ```json
    {
      "error": "Study session not found"
    }
    ```

## Error Handling
All endpoints return appropriate HTTP status codes and error messages for invalid requests. Common error responses include:
- **400 Bad Request**: Indicates that the request was invalid or missing required fields.
- **404 Not Found**: Indicates that the requested resource could not be found.
- **500 Internal Server Error**: Indicates that an unexpected error occurred on the server.

## Testing the API
To test the API endpoints, tools like Postman or curl can be used. Below are examples of how to test the endpoints using curl:

### Example: Create a Study Session
```bash
curl -X POST http://localhost:5000/api/study-sessions \
-H "Content-Type: application/json" \
-d '{"group_id": 1, "study_activity_id": 1, "created_at": "2024-03-20T12:00:00Z"}'
```

### Example: Submit a Review
```bash
curl -X POST http://localhost:5000/api/study-sessions/1/review \
-H "Content-Type: application/json" \
-d '{"word_id": 1, "correct": true}'
```

### Example: Get Group Words
```bash
curl http://localhost:5000/api/groups/1/words/raw
```

### Example: Get Study Session Details
```bash
curl http://localhost:5000/api/study-sessions/1
```

## Bootcamp Week 1: Backend Implementation Report

The backend API was modified in two stages, following the plans outlined in `api_Fix.md` and `lang-portal_Adapt.md`.

### 1. API Fixes
- **Route Path Updates**: All endpoints were updated to include the `/api` prefix, enhancing clarity and organization.
- **Removed Unused APIs**: Redundant APIs were identified and eliminated, resulting in a cleaner codebase.
- **Enhanced Functionality**: Improvements were made to existing endpoints, ensuring correct response structures for a consistent API experience.
- **Missing Endpoints**: Implemented missing endpoints, such as the POST `/api/study-sessions/:id/review`, ensuring seamless integration with existing features.
- **Testing**: Verified route paths and tested API functionality, e.g., using curl, to ensure all changes worked as intended.

### 2. Language Adaptation
- **Database Schema Updates**: Renamed columns to accommodate Putonghua requirements, changing `kanji` to `jiantizi` and `romaji` to `pinyin`. This required careful data migration to prevent loss.
- **Localization**: Implemented strategies to support Putonghua, including translating hardcoded strings and API responses.
- **Updated Response Structures**: Modified API response structures to reflect new naming conventions, ensuring consistency.
- **Testing**: Verified database storage, API responses, and UI rendering for Putonghua to ensure proper functionality.

## Challenges Faced
Significant challenges encountered during the implementation included:
- **Database Migration**: Ensuring data integrity during column renaming.
- **Localization**: Adapting the application for a new language, requiring technical and cultural considerations.
- **Thorough Testing**: Validating all changes through extensive testing to prevent regressions.

## Conclusion
These modifications enable the backend to effectively serve a Putonghua-speaking user base while maintaining data integrity and functionality.
