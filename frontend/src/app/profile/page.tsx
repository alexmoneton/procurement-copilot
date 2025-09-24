'use client'

import { useState } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'

export default function ProfilePage() {
  const { user } = useUser()
  const router = useRouter()
  const [formData, setFormData] = useState({
    company: '',
    industry: '',
    countries: [] as string[],
    minValue: '',
    maxValue: '',
    keywords: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const industries = [
    'IT & Software',
    'Construction',
    'Healthcare',
    'Transportation',
    'Energy',
    'Education',
    'Defense',
    'Other'
  ]

  const euCountries = [
    'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic',
    'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece',
    'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg',
    'Malta', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia',
    'Slovenia', 'Spain', 'Sweden'
  ]

  const handleCountryToggle = (country: string) => {
    setFormData(prev => ({
      ...prev,
      countries: prev.countries.includes(country)
        ? prev.countries.filter(c => c !== country)
        : [...prev.countries, country]
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Here you would typically save the profile to your backend
      // For now, we'll just simulate a successful save
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Redirect to dashboard
      router.push('/app')
    } catch (error) {
      console.error('Error saving profile:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Please sign in</h1>
          <p className="text-gray-600">You need to be signed in to set up your profile.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2" style={{fontFamily: 'Manrope, sans-serif'}}>
                Set Up Your Profile
              </h1>
              <p className="text-gray-600">
                Tell us about your business to get personalized tender recommendations
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Company Information */}
              <div>
                <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-2">
                  Company Name
                </label>
                <input
                  type="text"
                  id="company"
                  value={formData.company}
                  onChange={(e) => setFormData(prev => ({ ...prev, company: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003399] focus:border-transparent"
                  placeholder="Enter your company name"
                  required
                />
              </div>

              {/* Industry */}
              <div>
                <label htmlFor="industry" className="block text-sm font-medium text-gray-700 mb-2">
                  Industry
                </label>
                <select
                  id="industry"
                  value={formData.industry}
                  onChange={(e) => setFormData(prev => ({ ...prev, industry: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003399] focus:border-transparent"
                  required
                >
                  <option value="">Select your industry</option>
                  {industries.map(industry => (
                    <option key={industry} value={industry}>{industry}</option>
                  ))}
                </select>
              </div>

              {/* Countries of Interest */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Countries of Interest
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto border border-gray-300 rounded-md p-3">
                  {euCountries.map(country => (
                    <label key={country} className="flex items-center space-x-2 text-sm">
                      <input
                        type="checkbox"
                        checked={formData.countries.includes(country)}
                        onChange={() => handleCountryToggle(country)}
                        className="rounded border-gray-300 text-[#003399] focus:ring-[#003399]"
                      />
                      <span className="text-gray-700">{country}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Contract Value Range */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="minValue" className="block text-sm font-medium text-gray-700 mb-2">
                    Minimum Contract Value (€)
                  </label>
                  <input
                    type="number"
                    id="minValue"
                    value={formData.minValue}
                    onChange={(e) => setFormData(prev => ({ ...prev, minValue: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003399] focus:border-transparent"
                    placeholder="e.g., 50000"
                  />
                </div>
                <div>
                  <label htmlFor="maxValue" className="block text-sm font-medium text-gray-700 mb-2">
                    Maximum Contract Value (€)
                  </label>
                  <input
                    type="number"
                    id="maxValue"
                    value={formData.maxValue}
                    onChange={(e) => setFormData(prev => ({ ...prev, maxValue: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003399] focus:border-transparent"
                    placeholder="e.g., 1000000"
                  />
                </div>
              </div>

              {/* Keywords */}
              <div>
                <label htmlFor="keywords" className="block text-sm font-medium text-gray-700 mb-2">
                  Keywords (comma-separated)
                </label>
                <input
                  type="text"
                  id="keywords"
                  value={formData.keywords}
                  onChange={(e) => setFormData(prev => ({ ...prev, keywords: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003399] focus:border-transparent"
                  placeholder="e.g., software, consulting, maintenance"
                />
              </div>

              {/* Submit Button */}
              <div className="pt-6">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full bg-[#003399] text-white py-3 px-4 rounded-md hover:bg-[#002266] focus:outline-none focus:ring-2 focus:ring-[#003399] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSubmitting ? 'Setting up your profile...' : 'Complete Profile Setup'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}