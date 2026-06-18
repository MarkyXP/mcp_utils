from fastapi import APIRouter, HTTPException, Query

from app.services.youtube import get_transcript, search, get_channel_videos, get_channel_id

router = APIRouter(prefix="/youtube", tags=["youtube"])


@router.get("/search")
def api_search_youtube_videos(
    search_term: str = Query(..., description="Search query"),
    num_videos: int = Query(5, ge=1, le=50, description="Number of videos (1-50)"),
):
    """Search YouTube for videos based on a query."""
    try:
        results = search(search_term, num_videos)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"results": results, "count": len(results)}


@router.get("/transcript")
async def api_get_youtube_transcript(
    video_url_or_title: str = Query(..., description="YouTube video URL or video ID"),
):
    """Extract transcript from a YouTube video."""
    try:
        transcript = get_transcript(video_url_or_title)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return transcript


@router.get("/channel/id")
def api_get_channel_id(
    channel_name: str = Query(..., description="YouTube channel name or handle"),
):
    """Resolve a YouTube channel name/handle to its channel ID."""
    try:
        channel_id = get_channel_id(channel_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"channel_id": channel_id}


@router.get("/channel/videos")
def api_get_channel_videos(
    channel_id: str = Query(pattern="^UC[a-zA-Z0-9]{22}", description="YouTube channel ID"),
    n: int = Query(10, ge=1, le=50, description="Number of videos (1-50)"),
):
    """Fetch the latest n videos from a YouTube channel."""
    try:
        videos = get_channel_videos(channel_id, n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"videos": videos, "count": len(videos)}
