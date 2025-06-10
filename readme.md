## Setup Instructions:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   - Create a `.env` file with your API keys
   - Get Azure OpenAI API key from Azure portal
   - Get Google Places API key from Google Cloud Console

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## Key Features:

✅ **Azure OpenAI Integration** - Uses your Azure OpenAI deployment
✅ **Google Places API** - Reliable location and place data
✅ **Context Memory** - Remembers conversation history
✅ **Multiple Query Types** - Tourist places, restaurants, activities, hotels
✅ **Follow-up Questions** - Natural conversation flow
✅ **Search Radius Control** - Adjustable search distance
✅ **Professional UI** - Clean, intuitive interface
✅ **Error Handling** - Robust error management
✅ **Caching** - Efficient resource usage

## API Requirements:
- **Azure OpenAI**: For AI-powered recommendations
- **Google Places API**: For location data and place search (more reliable than alternatives)

The Google Places API is essential for getting accurate, up-to-date information about restaurants, hotels, and attractions with ratings, prices, and reviews.
