"""
Publish controller for hands-off SEO system
Manages cluster-based publishing with quality gates
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from ..db.models import PageCluster, Page, ClusterMetric
from ..db.session import get_db


class PublishController:
    """Controls what gets published to Google and when."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def publish_from_cluster(self, cluster_id: str) -> int:
        """
        Publish pages from a cluster based on quality and coverage metrics.
        
        Args:
            cluster_id: The cluster to publish from
            
        Returns:
            Number of pages published
        """
        # Get cluster with pages
        cluster_query = select(PageCluster).options(
            selectinload(PageCluster.pages)
        ).where(PageCluster.id == cluster_id)
        
        result = await self.db.execute(cluster_query)
        cluster = result.scalar_one_or_none()
        
        if not cluster:
            return 0
        
        # Get latest metrics
        latest_metrics = await self._get_latest_metrics(cluster_id)
        coverage = latest_metrics.coverage_pct if latest_metrics else 0
        
        # Check if cluster meets threshold
        if coverage < cluster.threshold_pct:
            print(f"⚠️  Cluster {cluster.slug} coverage {coverage}% below threshold {cluster.threshold_pct}%")
            return 0
        
        # Get pages ready for publishing
        ready_pages_query = select(Page).where(
            Page.cluster_id == cluster_id,
            Page.indexable == False,
            Page.quality_ok == True
        ).limit(cluster.target_daily)
        
        result = await self.db.execute(ready_pages_query)
        ready_pages = result.scalars().all()
        
        if not ready_pages:
            print(f"ℹ️  No pages ready for publishing in cluster {cluster.slug}")
            return 0
        
        # Publish pages
        page_ids = [page.id for page in ready_pages]
        
        await self.db.execute(
            update(Page)
            .where(Page.id.in_(page_ids))
            .values(
                indexable=True,
                published_at=datetime.now(),
                lastmod=datetime.now()
            )
        )
        
        await self.db.commit()
        
        print(f"✅ Published {len(ready_pages)} pages from cluster {cluster.slug}")
        return len(ready_pages)
    
    async def _get_latest_metrics(self, cluster_id: str) -> Optional[ClusterMetric]:
        """Get latest metrics for a cluster."""
        query = select(ClusterMetric).where(
            ClusterMetric.cluster_id == cluster_id
        ).order_by(ClusterMetric.date.desc()).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_cluster_status(self, cluster_id: str) -> Dict[str, Any]:
        """Get current status of a cluster."""
        # Get cluster
        cluster_query = select(PageCluster).where(PageCluster.id == cluster_id)
        result = await self.db.execute(cluster_query)
        cluster = result.scalar_one_or_none()
        
        if not cluster:
            return {}
        
        # Get page counts
        page_counts_query = select(
            func.count(Page.id).label('total'),
            func.count(Page.id).filter(Page.submitted == True).label('submitted'),
            func.count(Page.id).filter(Page.indexable == True).label('indexed'),
            func.count(Page.id).filter(Page.quality_ok == True).label('quality_ok'),
            func.count(Page.id).filter(
                Page.indexable == False,
                Page.quality_ok == True
            ).label('ready_to_publish')
        ).where(Page.cluster_id == cluster_id)
        
        result = await self.db.execute(page_counts_query)
        counts = result.first()
        
        # Get latest metrics
        latest_metrics = await self._get_latest_metrics(cluster_id)
        
        return {
            "cluster": {
                "id": cluster.id,
                "kind": cluster.kind,
                "slug": cluster.slug,
                "target_daily": cluster.target_daily,
                "threshold_pct": cluster.threshold_pct,
                "status": cluster.status
            },
            "pages": {
                "total": counts.total or 0,
                "submitted": counts.submitted or 0,
                "indexed": counts.indexed or 0,
                "quality_ok": counts.quality_ok or 0,
                "ready_to_publish": counts.ready_to_publish or 0
            },
            "metrics": {
                "coverage_pct": latest_metrics.coverage_pct if latest_metrics else 0,
                "date": latest_metrics.date if latest_metrics else None
            }
        }
    
    async def get_all_cluster_status(self) -> List[Dict[str, Any]]:
        """Get status of all clusters."""
        # Get all clusters
        clusters_query = select(PageCluster)
        result = await self.db.execute(clusters_query)
        clusters = result.scalars().all()
        
        statuses = []
        for cluster in clusters:
            status = await self.get_cluster_status(cluster.id)
            statuses.append(status)
        
        return statuses
    
    async def pause_cluster(self, cluster_id: str) -> bool:
        """Pause publishing for a cluster."""
        await self.db.execute(
            update(PageCluster)
            .where(PageCluster.id == cluster_id)
            .values(status="paused")
        )
        await self.db.commit()
        return True
    
    async def resume_cluster(self, cluster_id: str) -> bool:
        """Resume publishing for a cluster."""
        await self.db.execute(
            update(PageCluster)
            .where(PageCluster.id == cluster_id)
            .values(status="active")
        )
        await self.db.commit()
        return True
    
    async def update_cluster_settings(self, cluster_id: str, settings: Dict[str, Any]) -> bool:
        """Update cluster settings."""
        update_data = {}
        
        if "target_daily" in settings:
            update_data["target_daily"] = settings["target_daily"]
        if "threshold_pct" in settings:
            update_data["threshold_pct"] = settings["threshold_pct"]
        
        if update_data:
            await self.db.execute(
                update(PageCluster)
                .where(PageCluster.id == cluster_id)
                .values(**update_data)
            )
            await self.db.commit()
        
        return True
    
    async def force_publish_cluster(self, cluster_id: str, count: int = 100) -> int:
        """Force publish pages from a cluster (override quality gates)."""
        # Get pages ready for publishing
        ready_pages_query = select(Page).where(
            Page.cluster_id == cluster_id,
            Page.indexable == False
        ).limit(count)
        
        result = await self.db.execute(ready_pages_query)
        ready_pages = result.scalars().all()
        
        if not ready_pages:
            return 0
        
        # Publish pages
        page_ids = [page.id for page in ready_pages]
        
        await self.db.execute(
            update(Page)
            .where(Page.id.in_(page_ids))
            .values(
                indexable=True,
                published_at=datetime.now(),
                lastmod=datetime.now()
            )
        )
        
        await self.db.commit()
        
        print(f"🚀 Force published {len(ready_pages)} pages from cluster {cluster_id}")
        return len(ready_pages)
    
    async def create_cluster(self, kind: str, slug: str, target_daily: int = 500, threshold_pct: int = 40) -> str:
        """Create a new page cluster."""
        cluster = PageCluster(
            kind=kind,
            slug=slug,
            target_daily=target_daily,
            threshold_pct=threshold_pct,
            status="active"
        )
        
        self.db.add(cluster)
        await self.db.commit()
        await self.db.refresh(cluster)
        
        print(f"✅ Created cluster {slug} ({kind})")
        return cluster.id
    
    async def ingest_tender_pages(self, tenders: List[Dict[str, Any]], cluster_id: str) -> int:
        """Ingest tender data as pages."""
        created_count = 0
        
        for tender in tenders:
            # Create page URL
            url = f"/seo/tenders/{tender['id']}"
            slug = tender['id']
            
            # Check if page already exists
            existing_query = select(Page).where(Page.url == url)
            result = await self.db.execute(existing_query)
            existing_page = result.scalar_one_or_none()
            
            if existing_page:
                continue
            
            # Create new page
            page = Page(
                cluster_id=cluster_id,
                url=url,
                slug=slug,
                kind="tender",
                indexable=False,  # Start as noindex
                quality_ok=False,  # Will be checked by quality job
                submitted=True,    # Add to sitemap immediately
                lastmod=datetime.now()
            )
            
            self.db.add(page)
            created_count += 1
        
        await self.db.commit()
        print(f"✅ Ingested {created_count} tender pages into cluster {cluster_id}")
        return created_count
