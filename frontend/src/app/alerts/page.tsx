'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import Link from 'next/link'
import Image from 'next/image'

// Check if Clerk is properly configured
const hasClerkKeys = typeof window !== 'undefined' && 
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

const alertTemplates = [
  {
    id: 'high_value_opportunities',
    name: 'High-Value Opportunities',
    description: 'Contracts above €500K in your sectors',
    icon: '💰',
    defaultEnabled: true,
    badge: 'Premium'
  },
  {
    id: 'perfect_matches',
    name: 'Perfect Matches',
    description: '90%+ match score opportunities',
    icon: '🎯',
    defaultEnabled: true,
    badge: 'AI-Powered'
  },
  {
    id: 'urgent_deadlines',
    name: 'Urgent Deadlines',
    description: 'Opportunities closing within 7 days',
    icon: '⚡',
    defaultEnabled: false,
    badge: 'Time-Sensitive'
  },
  {
    id: 'low_competition',
    name: 'Low Competition',
    description: 'Fewer than 4 expected bidders',
    icon: '🏆',
    defaultEnabled: true,
    badge: 'High Win Rate'
  },
  {
    id: 'new_buyers',
    name: 'New Buyers',
    description: 'First-time procurement from this organization',
    icon: '🆕',
    defaultEnabled: false,
    badge: 'Opportunity'
  },
  {
    id: 'geographic_expansion',
    name: 'Geographic Opportunities',
    description: 'Similar work in adjacent countries',
    icon: '🌍',
    defaultEnabled: false,
    badge: 'Growth'
  }
]

function AlertsPageContent() {
  const [alertSettings, setAlertSettings] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Initialize with default settings
    const defaultSettings: Record<string, any> = {}
    alertTemplates.forEach(template => {
      defaultSettings[template.id] = {
        enabled: template.defaultEnabled,
        frequency: template.defaultEnabled ? 'instant' : 'weekly'
      }
    })
    setAlertSettings(defaultSettings)
    setLoading(false)
  }, [])

  const toggleAlert = (alertId: string, enabled: boolean) => {
    setAlertSettings(prev => ({
      ...prev,
      [alertId]: {
        ...prev[alertId],
        enabled
      }
    }))
  }

  const setFrequency = (alertId: string, frequency: string) => {
    setAlertSettings(prev => ({
      ...prev,
      [alertId]: {
        ...prev[alertId],
        frequency
      }
    }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-4">
            <Image src="/logo.svg" alt="TenderPulse" width={32} height={32} className="h-8 w-auto" />
            <div>
              <h1 className="text-xl font-bold text-[#003399]" style={{fontFamily: 'Manrope, sans-serif'}}>Alert Settings</h1>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium" style={{backgroundColor: 'rgba(255, 204, 0, 0.1)', color: '#003399'}}>
                Personalized Intelligence
              </span>
            </div>
          </div>
          <Link href="/app" className="text-sm font-medium text-gray-600 hover:text-[#003399] transition-colors">
            ← Back to Dashboard
          </Link>
        </div>
      </div>

      {/* Introduction */}
      <div className="bg-white p-6 rounded-xl shadow-lg mb-8 border border-gray-100">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">
          Personalized Alert Settings
        </h2>
        <p className="text-gray-600 mb-4">
          Configure when and how you want to be notified about new opportunities. Our AI will only send you tenders with high win probability.
        </p>
        
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">🎯</span>
            <h3 className="font-semibold text-blue-900">Smart Alert Preview</h3>
          </div>
          <p className="text-blue-800 text-sm">
            Based on your current settings, you would receive <strong>3-5 high-quality alerts per week</strong> instead of 50+ irrelevant notifications.
          </p>
        </div>
      </div>

      {/* Alert Templates */}
      <div className="space-y-6">
        {alertTemplates.map((template) => {
          const settings = alertSettings[template.id] || { enabled: false, frequency: 'weekly' }
          
          return (
            <div 
              key={template.id} 
              className={`bg-white p-6 rounded-xl shadow-lg border-l-4 transition-all duration-300 ${
                settings.enabled 
                  ? 'border-l-green-500 bg-gradient-to-r from-white to-green-50' 
                  : 'border-l-gray-300'
              }`}
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-4">
                  <div className="text-3xl">{template.icon}</div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {template.name}
                      </h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        template.badge === 'Premium' ? 'bg-yellow-100 text-yellow-800' :
                        template.badge === 'AI-Powered' ? 'bg-blue-100 text-blue-800' :
                        template.badge === 'High Win Rate' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {template.badge}
                      </span>
                    </div>
                    <p className="text-gray-600">
                      {template.description}
                    </p>
                  </div>
                </div>
                
                {/* Toggle Switch */}
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.enabled}
                    onChange={(e) => toggleAlert(template.id, e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`w-14 h-8 rounded-full transition-colors duration-300 ${
                    settings.enabled ? 'bg-green-500' : 'bg-gray-300'
                  }`}>
                    <div className={`w-6 h-6 bg-white rounded-full transition-transform duration-300 transform ${
                      settings.enabled ? 'translate-x-8' : 'translate-x-1'
                    } mt-1`}></div>
                  </div>
                </label>
              </div>
              
              {settings.enabled && (
                <div className="border-t border-gray-200 pt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Notification Frequency:
                  </label>
                  <div className="flex gap-3">
                    {['instant', 'daily', 'weekly'].map((freq) => (
                      <button
                        key={freq}
                        onClick={() => setFrequency(template.id, freq)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                          settings.frequency === freq
                            ? 'bg-[#003399] text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {freq.charAt(0).toUpperCase() + freq.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Save Button */}
      <div className="mt-8 text-center">
        <button 
          className="px-8 py-3 rounded-lg text-white font-semibold text-lg transition-all duration-300 hover:transform hover:translate-y-[-2px] hover:shadow-xl"
          style={{
            background: 'linear-gradient(135deg, #003399, #0052CC)'
          }}
          onClick={() => {
            // In real app, save to backend
            alert('Alert settings saved successfully! 🎉')
          }}
        >
          Save Alert Settings
        </button>
        
        <p className="text-gray-500 text-sm mt-3">
          Changes take effect immediately. You can modify these anytime.
        </p>
      </div>

      {/* Upgrade Prompt */}
      <div className="mt-12 p-6 rounded-xl border-2 border-dashed border-[#FFCC00] bg-gradient-to-r from-yellow-50 to-orange-50">
        <div className="text-center">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            🚀 Unlock All Premium Alerts
          </h3>
          <p className="text-gray-600 mb-4">
            Get access to competitor intelligence, response templates, and advanced filtering with TenderPulse Pro.
          </p>
          <Link 
            href="/pricing"
            className="inline-block px-6 py-3 rounded-lg text-[#003399] font-semibold transition-all duration-300 hover:transform hover:translate-y-[-2px] hover:shadow-lg"
            style={{
              background: 'linear-gradient(135deg, #FFCC00, #FFB000)'
            }}
          >
            Upgrade to Pro →
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function AlertsPage() {
  if (!hasClerkKeys) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Alert Settings</h1>
          <p className="text-gray-600">Authentication is not configured. Please set up Clerk to access alert settings.</p>
        </div>
      </div>
    )
  }

  return <AlertsPageContent />
}
