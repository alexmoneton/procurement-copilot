"""
Admin endpoints for cluster management
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ....db.session import get_db
from ....services.publish_controller import PublishController

router = APIRouter()


class ForcePublishRequest(BaseModel):
    count: int = 100


@router.post("/clusters/{cluster_id}/force-publish")
async def force_publish_cluster(
    cluster_id: str,
    request: ForcePublishRequest,
    db: AsyncSession = Depends(get_db)
):
    """Force publish pages from a cluster (override quality gates)."""
    try:
        controller = PublishController(db)
        published_count = await controller.force_publish_cluster(cluster_id, request.count)
        
        return {
            "status": "success",
            "message": f"Force published {published_count} pages",
            "published": published_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Force publish failed: {str(e)}")


@router.get("/cluster-status")
async def get_cluster_status(db: AsyncSession = Depends(get_db)):
    """Get status of all clusters."""
    try:
        controller = PublishController(db)
        statuses = await controller.get_all_cluster_status()
        
        return statuses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cluster status: {str(e)}")


@router.post("/clusters/{cluster_id}/pause")
async def pause_cluster(
    cluster_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Pause publishing for a cluster."""
    try:
        controller = PublishController(db)
        success = await controller.pause_cluster(cluster_id)
        
        return {
            "status": "success",
            "message": f"Cluster {cluster_id} paused"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause cluster: {str(e)}")


@router.post("/clusters/{cluster_id}/resume")
async def resume_cluster(
    cluster_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Resume publishing for a cluster."""
    try:
        controller = PublishController(db)
        success = await controller.resume_cluster(cluster_id)
        
        return {
            "status": "success",
            "message": f"Cluster {cluster_id} resumed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume cluster: {str(e)}")
