import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number | undefined, currency: string = 'EUR'): string {
  if (!amount) return 'N/A'
  
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('en-EU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(d)
}

export function formatDateTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('en-EU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d)
}

export function getDaysUntilDeadline(deadlineDate: string | undefined): number | null {
  if (!deadlineDate) return null
  
  const deadline = new Date(deadlineDate)
  const now = new Date()
  const diffTime = deadline.getTime() - now.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  return diffDays
}

export function getDeadlineStatus(deadlineDate: string | undefined): 'overdue' | 'urgent' | 'upcoming' | 'none' {
  const days = getDaysUntilDeadline(deadlineDate)
  
  if (days === null) return 'none'
  if (days < 0) return 'overdue'
  if (days <= 7) return 'urgent'
  return 'upcoming'
}

export function getDeadlineColor(status: 'overdue' | 'urgent' | 'upcoming' | 'none'): string {
  switch (status) {
    case 'overdue':
      return 'text-red-600 bg-red-50'
    case 'urgent':
      return 'text-orange-600 bg-orange-50'
    case 'upcoming':
      return 'text-green-600 bg-green-50'
    default:
      return 'text-gray-500 bg-gray-50'
  }
}

export function getSourceColor(source: 'TED' | 'BOAMP_FR'): string {
  switch (source) {
    case 'TED':
      return 'bg-blue-100 text-blue-800'
    case 'BOAMP_FR':
      return 'bg-purple-100 text-purple-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

export function parseKeywords(keywords: string): string[] {
  return keywords
    .split(',')
    .map(k => k.trim())
    .filter(k => k.length > 0)
}

export function formatKeywords(keywords: string[]): string {
  return keywords.join(', ')
}

export function parseCpvCodes(cpvCodes: string): string[] {
  return cpvCodes
    .split(',')
    .map(c => c.trim())
    .filter(c => c.length > 0)
}

export function formatCpvCodes(cpvCodes: string[]): string {
  return cpvCodes.join(', ')
}

export const COUNTRY_OPTIONS = [
  { code: 'FR', name: 'France' },
  { code: 'DE', name: 'Germany' },
  { code: 'ES', name: 'Spain' },
  { code: 'IT', name: 'Italy' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'BE', name: 'Belgium' },
  { code: 'PL', name: 'Poland' },
  { code: 'AT', name: 'Austria' },
  { code: 'PT', name: 'Portugal' },
  { code: 'SE', name: 'Sweden' },
  { code: 'DK', name: 'Denmark' },
  { code: 'FI', name: 'Finland' },
  { code: 'NO', name: 'Norway' },
  { code: 'CH', name: 'Switzerland' },
  { code: 'IE', name: 'Ireland' },
  { code: 'LU', name: 'Luxembourg' },
  { code: 'CZ', name: 'Czech Republic' },
  { code: 'HU', name: 'Hungary' },
  { code: 'SK', name: 'Slovakia' },
  { code: 'SI', name: 'Slovenia' },
  { code: 'HR', name: 'Croatia' },
  { code: 'RO', name: 'Romania' },
  { code: 'BG', name: 'Bulgaria' },
  { code: 'EE', name: 'Estonia' },
  { code: 'LV', name: 'Latvia' },
  { code: 'LT', name: 'Lithuania' },
  { code: 'CY', name: 'Cyprus' },
  { code: 'MT', name: 'Malta' },
] as const

export const FREQUENCY_OPTIONS = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
] as const

export const PLAN_OPTIONS = [
  {
    id: 'starter_99',
    name: 'Starter',
    price: 99,
    currency: 'EUR',
    interval: 'month',
    filters: 1,
    description: 'Perfect for individuals',
    features: [
      '1 saved filter',
      'Daily email alerts',
      'Basic search',
      'Email support',
    ],
  },
  {
    id: 'pro_199',
    name: 'Pro',
    price: 199,
    currency: 'EUR',
    interval: 'month',
    filters: 5,
    description: 'Great for small teams',
    features: [
      '5 saved filters',
      'Daily & weekly alerts',
      'Advanced search',
      'Priority support',
      'API access',
    ],
  },
  {
    id: 'team_399',
    name: 'Team',
    price: 399,
    currency: 'EUR',
    interval: 'month',
    filters: 15,
    description: 'For growing organizations',
    features: [
      '15 saved filters',
      'Custom alert frequency',
      'Advanced analytics',
      'Dedicated support',
      'Full API access',
      'Custom integrations',
    ],
  },
] as const
