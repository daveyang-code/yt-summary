import os
from flask import Flask, render_template_string, request, jsonify
import re
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    video_id_match = re.search(
        r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})",
        url,
    )
    return video_id_match.group(1) if video_id_match else None


def get_transcript(video_id):
    """Retrieve transcript for a given YouTube video ID"""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript]), None
    except Exception as e:
        return None, str(e)


def generate_summary(transcript):
    """Generate summary using Gemini AI"""
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Prepare prompt for summarization
        prompt = f"""Please provide a concise summary of the following transcript. 
        Focus on the main points and key insights. Limit the summary to 3-4 paragraphs:

        {transcript}"""

        # Generate summary
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        return None, str(e)


# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Summarizer</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-4xl">
        <h1 class="text-2xl font-bold mb-4 text-center">Video Summarizer</h1>
        
        <div class="mb-4">
            <input 
                type="text" 
                id="videoUrl" 
                placeholder="Enter YouTube Video URL" 
                class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
        </div>
        
        <button 
            id="summarizeBtn" 
            class="w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600 transition duration-300"
        >
            Summarize
        </button>
        
        <div id="loadingSpinner" class="hidden text-center mt-4">
            <div class="animate-spin inline-block w-6 h-6 border-4 border-blue-500 rounded-full border-t-transparent"></div>
            <p>Processing...</p>
        </div>
        
        <div id="errorContainer" class="hidden mt-4 bg-red-100 text-red-800 p-3 rounded-md"></div>
        
        <div id="resultContainer" class="mt-4">
            <div id="transcriptSection" class="hidden">
                <h2 class="font-bold mb-2">Transcript:</h2>
                <div id="transcriptContent" class="bg-gray-100 p-3 rounded-md max-h-48 overflow-y-auto text-sm"></div>
            </div>
            
            <div id="summarySection" class="hidden mt-4">
                <h2 class="font-bold mb-2">Summary:</h2>
                <div id="summaryContent" class="bg-blue-50 p-3 rounded-md"></div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('summarizeBtn').addEventListener('click', async () => {
            const videoUrl = document.getElementById('videoUrl').value;
            if (!videoUrl) {
                alert('Please enter a YouTube URL');
                return;
            }
            
            const loadingSpinner = document.getElementById('loadingSpinner');
            const errorContainer = document.getElementById('errorContainer');
            const transcriptSection = document.getElementById('transcriptSection');
            const summarySection = document.getElementById('summarySection');
            const transcriptContent = document.getElementById('transcriptContent');
            const summaryContent = document.getElementById('summaryContent');

            // Reset previous results
            loadingSpinner.classList.remove('hidden');
            errorContainer.classList.add('hidden');
            transcriptSection.classList.add('hidden');
            summarySection.classList.add('hidden');

            try {
                const response = await fetch('/summarize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ videoUrl })
                });

                const data = await response.json();

                if (data.status === 'success') {
                    transcriptContent.textContent = data.transcript;
                    summaryContent.textContent = data.summary;
                    
                    transcriptSection.classList.remove('hidden');
                    summarySection.classList.remove('hidden');
                } else {
                    errorContainer.textContent = data.error || 'An error occurred';
                    errorContainer.classList.remove('hidden');
                }
            } catch (error) {
                console.error('Error:', error);
                errorContainer.textContent = 'An error occurred while processing the request.';
                errorContainer.classList.remove('hidden');
            } finally {
                loadingSpinner.classList.add('hidden');
            }
        });
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Render the main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route("/summarize", methods=["POST"])
def summarize():
    """Handle transcript summarization request"""
    try:
        # Get video URL from request
        video_url = request.json.get("videoUrl")

        # Extract video ID
        video_id = extract_video_id(video_url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL", "status": "error"}), 400

        # Fetch transcript
        transcript, transcript_error = get_transcript(video_id)
        if transcript_error:
            return (
                jsonify(
                    {
                        "error": f"Error retrieving transcript: {transcript_error}",
                        "status": "error",
                    }
                ),
                500,
            )

        # Generate summary
        summary, summary_error = generate_summary(transcript)
        if summary_error:
            return (
                jsonify(
                    {
                        "error": f"Error generating summary: {summary_error}",
                        "status": "error",
                    }
                ),
                500,
            )

        # Return successful response
        return jsonify(
            {"transcript": transcript, "summary": summary, "status": "success"}
        )

    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
