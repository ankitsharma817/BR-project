export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface BRProject {
  id: string;
  title: string;
  description?: string;
  status: string;
  deadline?: string;
  budget_min?: number;
  budget_max?: number;
  created_at: string;
  updated_at: string;
  requirement_count: number;
  proposal_count: number;
}

export interface Requirement {
  id: string;
  text: string;
  category: string;
  priority: string;
  source: string;
  created_at: string;
}

export interface Proposal {
  id: string;
  project_id: string;
  vendor_name: string;
  vendor_contact?: string;
  vendor_email?: string;
  filename: string;
  proposed_cost?: number;
  proposed_timeline_months?: number;
  status: string;
  overall_score?: number;
  uploaded_at: string;
  requirement_count?: number;
}

export interface RequirementMatching {
  id: string;
  br_requirement_text: string;
  br_requirement_category: string;
  br_requirement_priority: string;
  proposal_requirement_text?: string;
  score: number;
  label: string;
  explanation?: string;
}

export interface MatchingResult {
  id: string;
  proposal_id: string;
  overall_score: number;
  functional_score?: number;
  technical_score?: number;
  compliance_score?: number;
  security_score?: number;
  timeline_score?: number;
  resource_score?: number;
  deliverables_score?: number;
  executive_summary?: string;
  calculated_at: string;
  version: number;
  requirement_matchings: RequirementMatching[];
}

export interface RiskItem {
  level: string;
  description: string;
  category?: string;
}

export interface RecommendationItem {
  priority: string;
  action: string;
  reason?: string;
}

export interface MatchAnalysis {
  result_id: string;
  risks: RiskItem[];
  recommendations: RecommendationItem[];
  strengths: string[];
  gaps: string[];
}

export interface Feedback {
  id: string;
  proposal_id: string;
  feedback_type: string;
  rating?: number;
  comment?: string;
  corrected_score?: number;
  original_score?: number;
  is_useful?: boolean;
  created_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DashboardStats {
  total_br_projects: number;
  total_proposals: number;
  total_matched: number;
  total_users: number;
  avg_match_score?: number;
  pending_processing: number;
  total_feedback: number;
}

export interface SystemHealth {
  database: string;
  redis: string;
  gpu: string;
  gpu_name?: string;
  gpu_memory_gb?: number;
}
