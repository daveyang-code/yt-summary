# YouTube Video Summarizer
A Flask web application that automatically generates summaries for YouTube videos by extracting the video transcript using YouTube's internal API and processing the transcript with Google's Gemini AI to create concise summaries

# Features
- Transcript Extraction: Retrieves full video transcripts from YouTube
- AI Summarization: Uses Gemini AI to generate 3-4 paragraph summaries
- Simple Interface: Clean, responsive web interface with Tailwind CSS
- Error Handling: Gracefully handles missing transcripts and API errors

# Stack
- Backend: Python Flask
- AI Service: Google Gemini API
- YouTube API: InnerTube (unofficial YouTube API client)
- Frontend: HTML5 with Tailwind CSS
- Deployment: Can be deployed to any WSGI-compatible hosting
