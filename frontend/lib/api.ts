import type {
  TrainingCase,
  PreAuthCaseInput,
  PreAuthSkillOutput,
  SchemaField,
  ValidationSummary,
  ValidationProgressEvent,
} from './types'
import { ApiError } from './types'

/**
 * API base URL configuration.
 *
 * Development: Defaults to http://localhost:8000
 * Production: Set NEXT_PUBLIC_API_URL environment variable to your backend URL.
 *
 * Example for Docker deployment:
 *   NEXT_PUBLIC_API_URL=http://backend:8000
 *
 * Example for Vercel:
 *   Set NEXT_PUBLIC_API_URL in your project environment variables.
 */
const BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/+$/, '')

// Export for use in components (e.g., Navbar API docs link)
export { BASE }

// ── Core fetch wrapper ────────────────────────────────────
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response

  // Build headers: only set Content-Type for methods that typically have a body
  const method = (init?.method || 'GET').toUpperCase()
  const shouldSetContentType = method !== 'GET' && method !== 'HEAD'

  try {
    const baseHeaders: Record<string, string> = shouldSetContentType
      ? { 'Content-Type': 'application/json' }
      : {}

    if (process.env.NEXT_PUBLIC_API_KEY) {
      baseHeaders['Authorization'] = `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`
    }

    res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { ...baseHeaders, ...(init?.headers as Record<string, string> | undefined) },
    })
  } catch {
    // Network error — backend unreachable
    throw new ApiError(
      0,
      'Unable to connect to the analysis service. Is the backend running?'
    )
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    let message: string
    if (typeof body?.detail === 'string') {
      message = body.detail
    } else if (typeof body?.detail?.message === 'string') {
      message = body.detail.message
    } else if (Array.isArray(body?.detail) && body.detail.length > 0) {
      const first = body.detail[0]
      const loc = Array.isArray(first?.loc)
        ? first.loc.filter((l: unknown) => l !== 'body').join(' -> ')
        : ''
      message = loc ? `Validation error on '${loc}': ${first.msg}` : (first.msg ?? `Request failed with status ${res.status}`)
    } else {
      message = `Request failed with status ${res.status}`
    }
    throw new ApiError(res.status, message, body)
  }

  return res.json() as Promise<T>
}


export async function fetchTrainingCases(): Promise<TrainingCase[]> {
  return apiFetch<TrainingCase[]>('/api/cases')
}
export async function fetchHealth(): Promise<{ status: string; model: string }> {
  return apiFetch<{ status: string; model: string }>('/api/health')
}

export async function fetchCaseById(id: string): Promise<TrainingCase> {
  return apiFetch<TrainingCase>(`/api/cases/${id}`)
}


export async function fetchInputSchema(): Promise<SchemaField[]> {
  return apiFetch<SchemaField[]>('/api/schema')
}
export async function analyzeCase(
  input: PreAuthCaseInput
): Promise<PreAuthSkillOutput> {
  return apiFetch<PreAuthSkillOutput>('/api/analyze', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

/** Sends .xlsx file upload, returns full output */
export async function uploadAndAnalyze(file: File): Promise<PreAuthSkillOutput> {
  let res: Response

  const formData = new FormData()
  formData.append('file', file)

  try {
    const headers: Record<string, string> = {}
    if (process.env.NEXT_PUBLIC_API_KEY) {
      headers['Authorization'] = `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`
    }

    res = await fetch(`${BASE}/api/analyze/upload`, {
      method: 'POST',
      body: formData,
      headers,
      // Do NOT set Content-Type here — browser sets multipart boundary automatically
    })
  } catch {
    throw new ApiError(
      0,
      'Unable to connect to the analysis service. Is the backend running?'
    )
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const message =
      body?.detail?.message ||
      (typeof body?.detail === 'string' ? body.detail : null) ||
      `Upload failed with status ${res.status}`
    throw new ApiError(res.status, message, body)
  }

  return res.json() as Promise<PreAuthSkillOutput>
}

/** Returns the PreAuthCaseInput for the full complex case (PA-001) */
export async function fetchComplexCaseInput(): Promise<PreAuthCaseInput> {
  return apiFetch<PreAuthCaseInput>('/api/complex-case/input')
}

/** Runs all 10 training cases, returns accuracy table */
export async function runValidation(): Promise<ValidationSummary> {
  return apiFetch<ValidationSummary>('/api/validate-all')
}

/**
 * Runs validation with Server-Sent Events for real-time progress.
 * Returns an async iterable of progress events.
 */
export async function* runValidationStream(): AsyncIterable<ValidationProgressEvent> {
   const headers: Record<string, string> = {}
   if (process.env.NEXT_PUBLIC_API_KEY) {
     headers['Authorization'] = `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`
   }

   const response = await fetch(`${BASE}/api/validate-all/stream`, { headers })

   if (!response.ok) {
     const body = await response.json().catch(() => ({}))
     const message =
       body?.detail?.message ||
       (typeof body?.detail === 'string' ? body.detail : null) ||
       `Request failed with status ${response.status}`
     throw new ApiError(response.status, message, body)
   }

   const reader = response.body?.getReader()
   if (!reader) {
     throw new ApiError(0, 'No response body from validation stream')
   }

   const decoder = new TextDecoder()
   let buffer = ''

   try {
     while (true) {
       const { done, value } = await reader.read()
       if (done) break

       buffer += decoder.decode(value, { stream: true })

       // Process complete SSE events (separated by double newlines)
       const events = buffer.split('\n\n')
       buffer = events.pop() || '' // Keep incomplete event in buffer

       for (const event of events) {
         const lines = event.split('\n')
         for (const line of lines) {
           if (line.startsWith('data: ')) {
             const data = line.slice(6)
             if (data) {
               try {
                 yield JSON.parse(data) as ValidationProgressEvent
               } catch {
                 // Skip malformed JSON
               }
             }
           }
         }
       }
     }
   } finally {
     reader.releaseLock()
   }
 }