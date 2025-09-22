/**
 * API client for communicating with the backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.tenderpulse.eu';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface Tender {
  id: string;
  tender_ref: string;
  source: 'TED' | 'BOAMP_FR';
  title: string;
  summary?: string;
  publication_date: string;
  deadline_date?: string;
  cpv_codes: string[];
  buyer_name?: string;
  buyer_country: string;
  value_amount?: number;
  currency?: string;
  url: string;
  created_at: string;
  updated_at: string;
  smart_score?: number;  // Intelligence score 0-100
  competition_level?: string;  // Expected competition
  deadline_urgency?: string;  // Deadline strategy
}

export interface SavedFilter {
  id: string;
  user_id: string;
  name: string;
  keywords: string[];
  cpv_codes: string[];
  countries: string[];
  min_value?: number;
  max_value?: number;
  notify_frequency: 'daily' | 'weekly';
  last_notified_at?: string;
  created_at: string;
  updated_at: string;
}

export interface SavedFilterCreate {
  name: string;
  keywords: string[];
  cpv_codes: string[];
  countries: string[];
  min_value?: number;
  max_value?: number;
  notify_frequency: 'daily' | 'weekly';
}

export interface SavedFilterUpdate {
  name?: string;
  keywords?: string[];
  cpv_codes?: string[];
  countries?: string[];
  min_value?: number;
  max_value?: number;
  notify_frequency?: 'daily' | 'weekly';
}

export interface CheckoutSession {
  url: string;
}

export interface BillingPortal {
  url: string;
}

class ApiClient {
  private baseUrl: string;
  private userEmail: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  setUserEmail(email: string | null) {
    this.userEmail = email;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    // Add user email header for authentication
    if (this.userEmail) {
      headers['X-User-Email'] = this.userEmail;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          error: errorData.detail || errorData.message || `HTTP ${response.status}`,
        };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Tenders
  async getTenders(params: {
    query?: string;
    cpv?: string;
    country?: string;
    from?: string;
    to?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<ApiResponse<{ tenders: Tender[]; total: number }>> {
    const searchParams = new URLSearchParams();
    
    if (params.query) searchParams.set('query', params.query);
    if (params.cpv) searchParams.set('cpv', params.cpv);
    if (params.country) searchParams.set('country', params.country);
    if (params.from) searchParams.set('from', params.from);
    if (params.to) searchParams.set('to', params.to);
    if (params.limit) searchParams.set('limit', params.limit.toString());
    if (params.offset) searchParams.set('offset', params.offset.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/tenders/tenders${queryString ? `?${queryString}` : ''}`;
    
    return this.request(endpoint);
  }

  async getTender(tenderRef: string): Promise<ApiResponse<Tender>> {
    return this.request(`/api/v1/tenders/tenders/${tenderRef}`);
  }

  // Saved Filters
  async getSavedFilters(): Promise<ApiResponse<SavedFilter[]>> {
    return this.request('/api/v1/filters');
  }

  async createSavedFilter(filter: SavedFilterCreate): Promise<ApiResponse<SavedFilter>> {
    return this.request('/api/v1/filters', {
      method: 'POST',
      body: JSON.stringify(filter),
    });
  }

  async updateSavedFilter(id: string, filter: SavedFilterUpdate): Promise<ApiResponse<SavedFilter>> {
    return this.request(`/api/v1/filters/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(filter),
    });
  }

  async deleteSavedFilter(id: string): Promise<ApiResponse<void>> {
    return this.request(`/api/v1/filters/${id}`, {
      method: 'DELETE',
    });
  }

  // Billing
  async createCheckoutSession(priceId: string): Promise<ApiResponse<CheckoutSession>> {
    const response = await fetch('/api/stripe/checkout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ price_id: priceId }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return {
        error: errorData.error || `HTTP ${response.status}`,
      }
    }

    const data = await response.json()
    return { data }
  }

  async getBillingPortal(): Promise<ApiResponse<BillingPortal>> {
    const response = await fetch('/api/stripe/portal', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return {
        error: errorData.error || `HTTP ${response.status}`,
      }
    }

    const data = await response.json()
    return { data }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.request('/api/v1/health');
  }
}

// Create a singleton instance
export const apiClient = new ApiClient();

// Export the class for testing
export { ApiClient };
