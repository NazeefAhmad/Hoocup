# Chatbot API

A FastAPI-based chatbot API with emotion detection and memory capabilities.

## Deployment Instructions

### Prerequisites
- Python 3.9+
- Git
- Railway.app account

### Environment Variables
The following environment variables need to be set in your deployment platform:
- `OPENAI_API_KEY`: Your OpenAI API key
- `PINECONE_API_KEY`: Your Pinecone API key

### Local Development
1. Clone the repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your environment variables
6. Run the server: `python api.py`

### Deployment to Railway
1. Create a new project on Railway.app
2. Connect your GitHub repository
3. Add the required environment variables in Railway's dashboard
4. Deploy!

## API Endpoints

### Health Check
- `GET /health`: Check API health status

### Chat
- `POST /chat`: Send a message to the chatbot
  - Request body:
    ```json
    {
      "user_id": "string",
      "message": "string"
    }
    ```
  - Response:
    ```json
    {
      "response": "string",
      "emotion": "string",
      "cost": "float"
    }
    ``` 