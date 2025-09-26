'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface ClusterStatus {
  cluster: {
    id: string
    kind: string
    slug: string
    target_daily: number
    threshold_pct: number
    status: string
  }
  pages: {
    total: number
    submitted: number
    indexed: number
    quality_ok: number
    ready_to_publish: number
  }
  metrics: {
    coverage_pct: number
    date: string | null
  }
}

export default function PublishingDashboard() {
  const [clusters, setClusters] = useState<ClusterStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null)

  useEffect(() => {
    fetchClusterStatus()
  }, [])

  const fetchClusterStatus = async () => {
    try {
      const response = await fetch('/api/v1/admin/cluster-status')
      const data = await response.json()
      setClusters(data)
    } catch (error) {
      console.error('Failed to fetch cluster status:', error)
    } finally {
      setLoading(false)
    }
  }

  const pauseCluster = async (clusterId: string) => {
    try {
      await fetch(`/api/v1/admin/clusters/${clusterId}/pause`, {
        method: 'POST'
      })
      fetchClusterStatus()
    } catch (error) {
      console.error('Failed to pause cluster:', error)
    }
  }

  const resumeCluster = async (clusterId: string) => {
    try {
      await fetch(`/api/v1/admin/clusters/${clusterId}/resume`, {
        method: 'POST'
      })
      fetchClusterStatus()
    } catch (error) {
      console.error('Failed to resume cluster:', error)
    }
  }

  const forcePublish = async (clusterId: string, count: number = 100) => {
    try {
      await fetch(`/api/v1/admin/clusters/${clusterId}/force-publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count })
      })
      fetchClusterStatus()
    } catch (error) {
      console.error('Failed to force publish:', error)
    }
  }

  const updateClusterSettings = async (clusterId: string, settings: any) => {
    try {
      await fetch(`/api/v1/admin/clusters/${clusterId}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      })
      fetchClusterStatus()
    } catch (error) {
      console.error('Failed to update cluster settings:', error)
    }
  }

  const runCronJob = async (job: string) => {
    try {
      await fetch(`/api/v1/cron/${job}`, {
        method: 'POST'
      })
      fetchClusterStatus()
    } catch (error) {
      console.error(`Failed to run ${job} job:`, error)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">Loading cluster status...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">SEO Publishing Dashboard</h1>
        <p className="text-gray-600">Monitor and control automated SEO publishing</p>
      </div>

      <Tabs defaultValue="clusters" className="space-y-6">
        <TabsList>
          <TabsTrigger value="clusters">Clusters</TabsTrigger>
          <TabsTrigger value="jobs">Cron Jobs</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="clusters" className="space-y-6">
          <div className="grid gap-6">
            {clusters.map((cluster) => (
              <Card key={cluster.cluster.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {cluster.cluster.slug}
                        <Badge variant={cluster.cluster.status === 'active' ? 'default' : 'secondary'}>
                          {cluster.cluster.status}
                        </Badge>
                      </CardTitle>
                      <p className="text-sm text-gray-600">{cluster.cluster.kind}</p>
                    </div>
                    <div className="flex gap-2">
                      {cluster.cluster.status === 'active' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => pauseCluster(cluster.cluster.id)}
                        >
                          Pause
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => resumeCluster(cluster.cluster.id)}
                        >
                          Resume
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => forcePublish(cluster.cluster.id)}
                      >
                        Force Publish
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold">{cluster.pages.total}</div>
                      <div className="text-sm text-gray-600">Total Pages</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{cluster.pages.submitted}</div>
                      <div className="text-sm text-gray-600">Submitted</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{cluster.pages.indexed}</div>
                      <div className="text-sm text-gray-600">Indexed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-600">{cluster.pages.quality_ok}</div>
                      <div className="text-sm text-gray-600">Quality OK</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">{cluster.pages.ready_to_publish}</div>
                      <div className="text-sm text-gray-600">Ready</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-lg font-semibold">
                        Coverage: {cluster.metrics.coverage_pct}%
                      </div>
                      <div className="text-sm text-gray-600">
                        Threshold: {cluster.cluster.threshold_pct}%
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-600">Daily Target</div>
                      <div className="font-semibold">{cluster.cluster.target_daily}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="jobs" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Cron Jobs</CardTitle>
              <p className="text-sm text-gray-600">Manually trigger automated jobs</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Ingest Job (03:00 CET)</Label>
                  <Button onClick={() => runCronJob('ingest')} className="w-full">
                    Run Ingest
                  </Button>
                </div>
                <div className="space-y-2">
                  <Label>Quality Check (03:30 CET)</Label>
                  <Button onClick={() => runCronJob('quality')} className="w-full">
                    Run Quality Check
                  </Button>
                </div>
                <div className="space-y-2">
                  <Label>GSC Metrics (04:00 CET)</Label>
                  <Button onClick={() => runCronJob('gsc-metrics')} className="w-full">
                    Run GSC Metrics
                  </Button>
                </div>
                <div className="space-y-2">
                  <Label>Publish (04:15 CET)</Label>
                  <Button onClick={() => runCronJob('publish')} className="w-full">
                    Run Publish
                  </Button>
                </div>
                <div className="space-y-2">
                  <Label>Sitemap Refresh (04:30 CET)</Label>
                  <Button onClick={() => runCronJob('sitemap-refresh')} className="w-full">
                    Run Sitemap Refresh
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Cluster Settings</CardTitle>
              <p className="text-sm text-gray-600">Update cluster publishing parameters</p>
            </CardHeader>
            <CardContent>
              {clusters.map((cluster) => (
                <div key={cluster.cluster.id} className="border rounded-lg p-4 mb-4">
                  <h3 className="font-semibold mb-3">{cluster.cluster.slug}</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor={`target-${cluster.cluster.id}`}>Daily Target</Label>
                      <Input
                        id={`target-${cluster.cluster.id}`}
                        type="number"
                        defaultValue={cluster.cluster.target_daily}
                        onChange={(e) => {
                          const value = parseInt(e.target.value)
                          if (!isNaN(value)) {
                            updateClusterSettings(cluster.cluster.id, { target_daily: value })
                          }
                        }}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`threshold-${cluster.cluster.id}`}>Coverage Threshold (%)</Label>
                      <Input
                        id={`threshold-${cluster.cluster.id}`}
                        type="number"
                        defaultValue={cluster.cluster.threshold_pct}
                        onChange={(e) => {
                          const value = parseInt(e.target.value)
                          if (!isNaN(value)) {
                            updateClusterSettings(cluster.cluster.id, { threshold_pct: value })
                          }
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
