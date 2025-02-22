# Lang Portal Frontend Documentation

[Jump to Bootcamp Week 1: Frontend Implementation Report](https://github.com/AC888221/free-genai-bootcamp-2025/blob/main/lang-portal/frontend-react/README.md#bootcamp-week-1-frontend-implementation-report)

## Overview
The Lang Portal frontend is built using React and Vite, providing a user-friendly interface for language learning resources. This documentation outlines the setup, implementation, and usage of the frontend application.

## Getting Started

### Prerequisites
- Node.js (version 14 or higher)
- npm or yarn

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/AC888221/free-genai-bootcamp-2025.git
   cd lang-portal/frontend-react
   ```

2. **Install Dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Run the Development Server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```
   The application will be available at `http://localhost:3000`.

### Building for Production
To build the application for production, run:
```bash
npm run build
# or
yarn build
```
The production files will be generated in the `dist` directory.

## Key Features
- **Language Adaptation**: The UI has been adapted from Japanese to Putonghua, ensuring a seamless user experience.
- **API Integration**: The frontend interacts with the backend API, allowing for dynamic data retrieval and submission.
- **Responsive Design**: The application is designed to be responsive, providing a consistent experience across devices.

## Bootcamp Week 1: Frontend Implementation Report

The frontend was modified to adapt the user interface from Japanese to Putonghua, ensuring effective communication with the updated backend.

### Key Changes

1. **Language Adaptation**: All text elements were updated to Putonghua, including buttons, labels, and instructional text.

2. **API Adjustments**: API calls were modified to align with updated backend endpoints as specified in `api_Fix.md`, including the addition of the `/api` prefix.

3. **User Interface Updates**: Layout and design adjustments were made to accommodate changes in text length and formatting:
   - Font changes for Putonghua characters to enhance readability.
   - Component updates to handle varying text lengths and prevent layout issues.

4. **Testing**: Comprehensive testing verified:
   - Text updates for accurate Putonghua translations.
   - API interactions for successful data retrieval and submission.
   - UI rendering across different devices and screen sizes.

### Challenges Faced
Several key challenges were encountered during the frontend implementation:
- **Translation Accuracy**: Achieving precise translations to ensure that the intended meaning and context were maintained throughout the user interface.
- **API Integration**: Modifying API calls to align with the updated backend endpoints necessitated thorough testing to confirm that all interactions functioned correctly.
- **UI Adaptation**: Adjusting the user interface to accommodate varying text lengths and formatting
- **Cross-Device Compatibility**: Ensuring that the application rendered correctly across various devices and screen sizes.

## Conclusion
The adaptation of the user interface and API interactions effectively meets user needs while enhancing usability and performance.
