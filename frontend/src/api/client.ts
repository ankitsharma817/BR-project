import axios, { AxiosError } from 'axios';

const BASE_URL = '/api/v1';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401 try refresh once, else redirect to login
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as any;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh-token`, { refresh_token: refresh });
          const newToken = data.data.access_token;
          localStorage.setItem('access_token', newToken);
          original.headers.Authorization = `Bearer ${newToken}`;
          return api(original);
        } catch {
          localStorage.clear();
          window.location.href = '/login';
        }
      } else {
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string, full_name: string) =>
    api.post('/auth/register', { email, password, full_name }),
  logout: (refresh_token: string) =>
    api.post('/auth/logout', { refresh_token }),
  profile: () => api.get('/auth/profile'),
};

// ── BR Projects ───────────────────────────────────────────────────────────────
export const brApi = {
  list: (page = 1, pageSize = 20, status?: string) =>
    api.get('/br-projects', { params: { page, page_size: pageSize, status } }),
  get: (id: string) => api.get(`/br-projects/${id}`),
  create: (data: object) => api.post('/br-projects', data),
  update: (id: string, data: object) => api.put(`/br-projects/${id}`, data),
  delete: (id: string) => api.delete(`/br-projects/${id}`),
  uploadDocument: (id: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post(`/br-projects/${id}/documents`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  listRequirements: (id: string, category?: string, priority?: string) =>
    api.get(`/br-projects/${id}/requirements`, { params: { category, priority } }),
  createRequirement: (id: string, data: object) =>
    api.post(`/br-projects/${id}/requirements`, data),
  updateRequirement: (brId: string, reqId: string, data: object) =>
    api.put(`/br-projects/${brId}/requirements/${reqId}`, data),
  deleteRequirement: (brId: string, reqId: string) =>
    api.delete(`/br-projects/${brId}/requirements/${reqId}`),
};

// ── Proposals ─────────────────────────────────────────────────────────────────
export const proposalApi = {
  list: (brId: string, page = 1, pageSize = 20, status?: string) =>
    api.get(`/br-projects/${brId}/proposals`, { params: { page, page_size: pageSize, status } }),
  get: (brId: string, proposalId: string) =>
    api.get(`/br-projects/${brId}/proposals/${proposalId}`),
  upload: (brId: string, file: File, meta: Record<string, string | number | undefined>) => {
    const params: Record<string, string> = { vendor_name: String(meta.vendor_name) };
    if (meta.vendor_contact) params.vendor_contact = String(meta.vendor_contact);
    if (meta.vendor_email) params.vendor_email = String(meta.vendor_email);
    if (meta.proposed_cost !== undefined) params.proposed_cost = String(meta.proposed_cost);
    if (meta.proposed_timeline_months !== undefined) params.proposed_timeline_months = String(meta.proposed_timeline_months);
    const form = new FormData();
    form.append('file', file);
    return api.post(`/br-projects/${brId}/proposals`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params,
    });
  },
  delete: (brId: string, proposalId: string) =>
    api.delete(`/br-projects/${brId}/proposals/${proposalId}`),
  status: (proposalId: string) =>
    api.get(`/proposals/${proposalId}/upload-status`),
};

// ── Matching ──────────────────────────────────────────────────────────────────
export const matchingApi = {
  getResult: (proposalId: string) => api.get(`/proposals/${proposalId}/match`),
  getAnalysis: (proposalId: string) => api.get(`/proposals/${proposalId}/analysis`),
  recalculate: (proposalId: string) => api.post(`/proposals/${proposalId}/recalculate`),
  history: (proposalId: string) => api.get(`/proposals/${proposalId}/history`),
  compare: (proposalIds: string[]) => api.post('/proposals/compare', { proposal_ids: proposalIds }),
};

// ── Feedback ──────────────────────────────────────────────────────────────────
export const feedbackApi = {
  submit: (proposalId: string, data: object) =>
    api.post(`/proposals/${proposalId}/feedback`, data),
  list: (proposalId: string) => api.get(`/proposals/${proposalId}/feedback`),
};

// ── Admin ─────────────────────────────────────────────────────────────────────
export const adminApi = {
  dashboard: () => api.get('/dashboard'),
  health: () => api.get('/dashboard/system-health'),
  activities: (limit = 20) => api.get('/dashboard/activities', { params: { limit } }),
  auditLogs: (page = 1) => api.get('/admin/audit-logs', { params: { page } }),
  feedbackReport: () => api.get('/admin/feedback-quality-report'),
  aiStats: () => api.get('/admin/ai-learning/stats'),
};
