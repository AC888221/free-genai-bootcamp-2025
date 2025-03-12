# User Testing

## Using the Built-in Swagger UI (Easiest way to start):

Go to http://localhost:8000/docs

1. Test the welcome message by executing the GET request (no parameters needed).

2. Test the /api/agent endpoint by providing a song name and artist
```json
{
  "message_request": "{\"song_name\": \"好一朵美丽的茉莉花\", \"artist\": \"茉莉花\"}"
}
```

3. Test the /api/get_vocabulary endpoint by providing Chinese text, e.g.:

```json
{
  "text": "好一朵美丽的茉莉花好一朵美丽的茉莉花芬芳美丽满枝桠又香又白人人夸让我来将你摘下送给别人家茉莉花呀茉莉花"
}
```

## Using Curl from the command line:

1. Test the /api/agent endpoint:

# For the agent endpoint
curl -X POST "http://localhost:8000/api/agent" \
     -H "Content-Type: application/json" \
     -d '{"message_request": "月亮代表我的心", "artist_name": "邓丽君"}'

2. Test the /api/get_vocabulary endpoint:

# For the vocabulary endpoint
curl -X POST "http://localhost:8000/api/get_vocabulary" \
     -H "Content-Type: application/json" \
     -d '{"text": "月亮代表我的心"}'
