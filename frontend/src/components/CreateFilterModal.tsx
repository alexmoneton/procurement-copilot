'use client'

import { useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { apiClient, SavedFilterCreate } from '@/lib/api'
import { COUNTRY_OPTIONS, FREQUENCY_OPTIONS, parseKeywords, parseCpvCodes } from '@/lib/utils'

interface CreateFilterModalProps {
  onClose: () => void
  onSuccess: () => void
}

export function CreateFilterModal({ onClose, onSuccess }: CreateFilterModalProps) {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    keywords: '',
    cpvCodes: '',
    countries: [] as string[],
    minValue: '',
    maxValue: '',
    notifyFrequency: 'daily' as 'daily' | 'weekly',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const filterData: SavedFilterCreate = {
        name: formData.name,
        keywords: parseKeywords(formData.keywords),
        cpv_codes: parseCpvCodes(formData.cpvCodes),
        countries: formData.countries,
        min_value: formData.minValue ? parseFloat(formData.minValue) : undefined,
        max_value: formData.maxValue ? parseFloat(formData.maxValue) : undefined,
        notify_frequency: formData.notifyFrequency,
      }

      const response = await apiClient.createSavedFilter(filterData)
      
      if (response.data) {
        onSuccess()
      } else {
        console.error('Failed to create filter:', response.error)
        // In a real app, you'd show an error toast here
      }
    } catch (error) {
      console.error('Error creating filter:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCountryChange = (countryCode: string) => {
    setFormData(prev => ({
      ...prev,
      countries: prev.countries.includes(countryCode)
        ? prev.countries.filter(c => c !== countryCode)
        : [...prev.countries, countryCode]
    }))
  }

  return (
    <Transition.Root show={true} as="div">
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as="div"
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as="div"
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                <div className="absolute right-0 top-0 hidden pr-4 pt-4 sm:block">
                  <button
                    type="button"
                    className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    onClick={onClose}
                  >
                    <span className="sr-only">Close</span>
                    <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                  </button>
                </div>
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                    <Dialog.Title as="h3" className="text-base font-semibold leading-6 text-gray-900">
                      Create New Filter
                    </Dialog.Title>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Set up a filter to monitor tenders matching your criteria.
                      </p>
                    </div>
                  </div>
                </div>
                <form onSubmit={handleSubmit} className="mt-6 space-y-6">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium leading-6 text-gray-900">
                      Filter Name
                    </label>
                    <div className="mt-2">
                      <input
                        type="text"
                        name="name"
                        id="name"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                        placeholder="e.g., IT Services France"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="keywords" className="block text-sm font-medium leading-6 text-gray-900">
                      Keywords
                    </label>
                    <div className="mt-2">
                      <input
                        type="text"
                        name="keywords"
                        id="keywords"
                        value={formData.keywords}
                        onChange={(e) => setFormData(prev => ({ ...prev, keywords: e.target.value }))}
                        className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                        placeholder="e.g., software, development, IT"
                      />
                    </div>
                    <p className="mt-1 text-xs text-gray-500">Separate keywords with commas</p>
                  </div>

                  <div>
                    <label htmlFor="cpvCodes" className="block text-sm font-medium leading-6 text-gray-900">
                      CPV Codes
                    </label>
                    <div className="mt-2">
                      <input
                        type="text"
                        name="cpvCodes"
                        id="cpvCodes"
                        value={formData.cpvCodes}
                        onChange={(e) => setFormData(prev => ({ ...prev, cpvCodes: e.target.value }))}
                        className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                        placeholder="e.g., 72000000, 30200000"
                      />
                    </div>
                    <p className="mt-1 text-xs text-gray-500">Separate CPV codes with commas</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium leading-6 text-gray-900">
                      Countries
                    </label>
                    <div className="mt-2 max-h-32 overflow-y-auto border border-gray-300 rounded-md p-2">
                      <div className="grid grid-cols-2 gap-2">
                        {COUNTRY_OPTIONS.map((country) => (
                          <label key={country.code} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={formData.countries.includes(country.code)}
                              onChange={() => handleCountryChange(country.code)}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <span className="ml-2 text-sm text-gray-900">
                              {country.name}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="minValue" className="block text-sm font-medium leading-6 text-gray-900">
                        Min Value (€)
                      </label>
                      <div className="mt-2">
                        <input
                          type="number"
                          name="minValue"
                          id="minValue"
                          value={formData.minValue}
                          onChange={(e) => setFormData(prev => ({ ...prev, minValue: e.target.value }))}
                          className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                          placeholder="0"
                        />
                      </div>
                    </div>
                    <div>
                      <label htmlFor="maxValue" className="block text-sm font-medium leading-6 text-gray-900">
                        Max Value (€)
                      </label>
                      <div className="mt-2">
                        <input
                          type="number"
                          name="maxValue"
                          id="maxValue"
                          value={formData.maxValue}
                          onChange={(e) => setFormData(prev => ({ ...prev, maxValue: e.target.value }))}
                          className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                          placeholder="1000000"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <label htmlFor="notifyFrequency" className="block text-sm font-medium leading-6 text-gray-900">
                      Notification Frequency
                    </label>
                    <div className="mt-2">
                      <select
                        name="notifyFrequency"
                        id="notifyFrequency"
                        value={formData.notifyFrequency}
                        onChange={(e) => setFormData(prev => ({ ...prev, notifyFrequency: e.target.value as 'daily' | 'weekly' }))}
                        className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                      >
                        {FREQUENCY_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="mt-5 sm:mt-6 sm:grid sm:grid-flow-row-dense sm:grid-cols-2 sm:gap-3">
                    <button
                      type="submit"
                      disabled={loading}
                      className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 sm:col-start-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Creating...' : 'Create Filter'}
                    </button>
                    <button
                      type="button"
                      className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:col-start-1 sm:mt-0"
                      onClick={onClose}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  )
}
