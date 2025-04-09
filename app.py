from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

# 🔐 Replace with your actual YouTube API Key
API_KEY = "AIzaSyBBV7RCI4BCjeH4BuLPfYqCBy7_DWAeHFQ"

# ✅ Get channel details
def get_channel_data(channel_name):
    search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={channel_name}&key={API_KEY}"
    search_response = requests.get(search_url).json()

    if "items" not in search_response or not search_response["items"]:
        return {"error": "Channel not found"}

    channel_id = search_response["items"][0]["id"]["channelId"]

    channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={API_KEY}"
    channel_response = requests.get(channel_url).json()

    if "items" not in channel_response:
        return {"error": "Error fetching channel details"}

    channel_data = channel_response["items"][0]

    return {
        "channel_id": channel_id,
        "title": channel_data["snippet"]["title"],
        "description": channel_data["snippet"]["description"],
        "subscribers": int(channel_data["statistics"].get("subscriberCount", 0)),
        "total_views": int(channel_data["statistics"].get("viewCount", 0)),
        "total_videos": int(channel_data["statistics"].get("videoCount", 0)),
        "thumbnail": channel_data["snippet"]["thumbnails"]["high"]["url"]
    }

# ✅ Get latest videos
def get_latest_videos(channel_id):
    video_url = f"https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={channel_id}&part=snippet,id&order=date&maxResults=5"
    video_response = requests.get(video_url).json()

    video_data = []
    for item in video_response.get("items", []):
        video_data.append({
            "video_id": item["id"].get("videoId", ""),
            "title": item["snippet"]["title"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
        })
    return video_data

# ✅ Generate and save graph
def create_stats_graph(channel_name, subscribers, views, videos):
    labels = ['Subscribers', 'Total Views', 'Total Videos']
    values = [subscribers, views, videos]
    colors = ['skyblue', 'lightgreen', 'salmon']

    plt.figure(figsize=(8, 6))
    bars = plt.bar(labels, values, color=colors)

    plt.title(f"{channel_name} - Channel Statistics", fontsize=14)
    plt.ylabel("Count")
    plt.xticks(rotation=10)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + max(1, yval * 0.01), f'{yval:,}', ha='center', fontsize=9)

    plt.tight_layout()

    if not os.path.exists("static"):
        os.makedirs("static")

    filename = f"{channel_name.replace(' ', '_')}_stats.png"
    filepath = os.path.join("static", filename)
    plt.savefig(filepath)
    plt.close()

    return "/" + filepath

# ✅ API route to fetch data
@app.route("/channel", methods=["GET"])
def channel():
    channel_name = request.args.get("name")
    if not channel_name:
        return jsonify({"error": "Channel name is required"}), 400

    channel_info = get_channel_data(channel_name)
    if "error" in channel_info:
        return jsonify(channel_info), 404

    videos = get_latest_videos(channel_info["channel_id"])
    channel_info["videos"] = videos

    graph_path = create_stats_graph(
        channel_info["title"],
        channel_info["subscribers"],
        channel_info["total_views"],
        channel_info["total_videos"]
    )

    channel_info["graph"] = graph_path  # 👈 Send graph path in response

    return jsonify(channel_info)

# ✅ Home route for frontend
@app.route("/")
def home():
    return render_template("index.html")

# ✅ Optional: favicon.ico route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('.', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    app.run(debug=True)
