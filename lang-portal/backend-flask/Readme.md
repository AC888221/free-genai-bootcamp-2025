I modified the existing backend API in two stages:
API Fixes: Initially, I addressed issues with the existing API by:
Removing Unused APIs: Identified and removed APIs that were no longer necessary for the application.
Enhancing Functionality: Improved the remaining endpoints, including fixing route paths and ensuring correct response structures to enhance overall API reliability.
Language Adaptation: After fixing the API, I transitioned the system from supporting Japanese to Putonghua by:
Updating Data Handling: Adjusted the database schema, renaming columns to accommodate Putonghua language requirements, ensuring that all text fields were compatible with the new language.
Localization: Implemented localization strategies to support Putonghua, including changes to hardcoded strings and ensuring that API responses were appropriately translated.
These modifications ensured that the backend could effectively serve a Putonghua-speaking user base while maintaining data integrity and functionality.

## Setting up the database

```sh
invoke init-db
```

This will do the following:
- create the words.db (Sqlite3 database)
- run the migrations found in `seeds/`
- run the seed data found in `seed/`

Please note that migrations and seed data is manually coded to be imported in the `lib/db.py`. So you need to modify this code if you want to import other seed data.

## Clearing the database

Simply delete the `words.db` to clear entire database.

## Running the backend api

```sh
python app.py 
```

This should start the flask app on port `5000`
