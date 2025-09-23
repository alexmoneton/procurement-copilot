'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { apiClient, UserProfile, UserProfileCreate } from '@/lib/api'

const CPV_CODES = [
  { code: '45000000', name: 'Construction work' },
  { code: '72000000', name: 'IT services' },
  { code: '50000000', name: 'Repair and maintenance services' },
  { code: '79000000', name: 'Business services' },
  { code: '71000000', name: 'Architectural and engineering services' },
  { code: '73000000', name: 'Research and development services' },
  { code: '80000000', name: 'Education and training services' },
  { code: '85000000', name: 'Health and social work services' },
  { code: '90000000', name: 'Sewage, refuse, cleaning services' },
  { code: '92000000', name: 'Recreational, cultural and sporting services' }
]

const COUNTRIES = [
  'DE', 'FR', 'NL', 'IT', 'ES', 'PL', 'SE', 'NO', 'DK', 'FI', 'AT', 'BE', 'CH', 'IE', 'PT', 'CZ', 'HU', 'SK', 'SI', 'HR', 'BG', 'RO', 'LT', 'LV', 'EE', 'CY', 'MT', 'LU'
]

const COMPANY_SIZES = [
  'micro', 'small', 'medium', 'large'
]

const EXPERIENCE_LEVELS = [
  'beginner', 'intermediate', 'advanced', 'expert'
]

export default function ProfilePage() {
  const [, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    company_name: '',
    target_value_range: [50000, 2000000] as [number, number],
    preferred_countries: [] as string[],
    cpv_expertise: [] as string[],
    company_size: 'medium',
    experience_level: 'intermediate'
  })

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      setLoading(true)
      const response = await apiClient.getUserProfile()
      
      if (response.error) {
        if (response.error.includes('404')) {
          // Profile doesn't exist yet, use defaults
          setProfile(null)
        } else {
          setError(response.error)
        }
      } else if (response.data) {
        setProfile(response.data)
        setFormData({
          company_name: response.data.company_name || '',
          target_value_range: response.data.target_value_range || [50000, 2000000],
          preferred_countries: response.data.preferred_countries || [],
          cpv_expertise: response.data.cpv_expertise || [],
          company_size: response.data.company_size || 'medium',
          experience_level: response.data.experience_level || 'intermediate'
        })
      }
    } catch {
      setError('Failed to load profile')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      const profileData: UserProfileCreate = {
        company_name: formData.company_name || undefined,
        target_value_range: formData.target_value_range,
        preferred_countries: formData.preferred_countries.length > 0 ? formData.preferred_countries : undefined,
        cpv_expertise: formData.cpv_expertise.length > 0 ? formData.cpv_expertise : undefined,
        company_size: formData.company_size,
        experience_level: formData.experience_level
      }

      const response = await apiClient.createUserProfile(profileData)
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        setProfile(response.data)
        setSuccess('Profile saved successfully!')
      }
    } catch {
      setError('Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  const handleCountryToggle = (country: string) => {
    setFormData(prev => ({
      ...prev,
      preferred_countries: prev.preferred_countries.includes(country)
        ? prev.preferred_countries.filter(c => c !== country)
        : [...prev.preferred_countries, country]
    }))
  }

  const handleCpvToggle = (cpv: string) => {
    setFormData(prev => ({
      ...prev,
      cpv_expertise: prev.cpv_expertise.includes(cpv)
        ? prev.cpv_expertise.filter(c => c !== cpv)
        : [...prev.cpv_expertise, cpv]
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
              <h1 className="text-xl font-bold text-[#003399]" style={{fontFamily: 'Manrope, sans-serif'}}>TenderPulse</h1>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium" style={{backgroundColor: 'rgba(0, 51, 153, 0.1)', color: '#003399'}}>
                Profile Setup • Personalize Your Experience
              </span>
            </div>
          </div>
          <Link href="/app" className="text-sm font-medium text-gray-600 hover:text-[#003399] transition-colors">
            ← Back to Dashboard
          </Link>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800">{success}</p>
        </div>
      )}
      
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Profile Form */}
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Company Profile</h2>
          <p className="text-gray-600">
            Set up your profile to get personalized tender recommendations and smart matching scores.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Company Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company Name
            </label>
            <input
              type="text"
              value={formData.company_name}
              onChange={(e) => setFormData(prev => ({ ...prev, company_name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your company name"
            />
          </div>

          {/* Target Value Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Contract Value Range (€)
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Minimum</label>
                <input
                  type="number"
                  value={formData.target_value_range[0]}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    target_value_range: [parseInt(e.target.value) || 0, prev.target_value_range[1]]
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="50000"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Maximum</label>
                <input
                  type="number"
                  value={formData.target_value_range[1]}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    target_value_range: [prev.target_value_range[0], parseInt(e.target.value) || 0]
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="2000000"
                />
              </div>
            </div>
          </div>

          {/* Preferred Countries */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Preferred Countries
            </label>
            <div className="grid grid-cols-4 gap-2">
              {COUNTRIES.map(country => (
                <label key={country} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.preferred_countries.includes(country)}
                    onChange={() => handleCountryToggle(country)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{country}</span>
                </label>
              ))}
            </div>
          </div>

          {/* CPV Expertise */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              CPV Expertise Areas
            </label>
            <div className="space-y-2">
              {CPV_CODES.map(cpv => (
                <label key={cpv.code} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.cpv_expertise.includes(cpv.code)}
                    onChange={() => handleCpvToggle(cpv.code)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">
                    {cpv.code} - {cpv.name}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Company Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company Size
            </label>
            <select
              value={formData.company_size}
              onChange={(e) => setFormData(prev => ({ ...prev, company_size: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {COMPANY_SIZES.map(size => (
                <option key={size} value={size}>
                  {size.charAt(0).toUpperCase() + size.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Experience Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Experience Level
            </label>
            <select
              value={formData.experience_level}
              onChange={(e) => setFormData(prev => ({ ...prev, experience_level: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {EXPERIENCE_LEVELS.map(level => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
