export * from './api';
export * from './user';
export * from './article';
export * from './source';

// Analytics types
export interface SummaryStats {
  total_articles: number;
  pending_articles: number;
  approved_articles: number;
  rejected_articles: number;
  published_articles: number;
  approval_rate: number;
  avg_processing_time_minutes?: number;
  articles_today: number;
  articles_this_week: number;
}

export interface CategoryStats {
  category: string;
  total: number;
  approved: number;
  rejected: number;
  published: number;
  approval_rate: number;
}

export interface SourceStats {
  source_id: string;
  source_name: string;
  total: number;
  approved: number;
  rejected: number;
  approval_rate: number;
  avg_quality: number;
  reputation_score: number;
}

export interface TimeSeriesPoint {
  date: string;
  count: number;
}

export interface AnalyticsSummary {
  summary: SummaryStats;
  categories: CategoryStats[];
  top_sources: SourceStats[];
  articles_by_day: TimeSeriesPoint[];
  period_start: string;
  period_end: string;
}

// Rule types
export interface RuleCondition {
  field: string;
  operator: string;
  value: unknown;
}

export interface RuleAction {
  action: string;
  value?: unknown;
}

export interface Rule {
  id: string;
  project_id?: string;
  name: string;
  description?: string;
  is_active: boolean;
  priority: number;
  conditions: { conditions: RuleCondition[]; match?: string };
  actions: { actions: RuleAction[] };
  version: number;
  times_matched: number;
  last_matched_at?: string;
  created_at: string;
  updated_at: string;
}

// Template types
export interface Template {
  id: string;
  project_id?: string;
  name: string;
  description?: string;
  scope: string;
  scope_value?: string;
  body: string;
  auto_hashtags?: string[];
  is_active: boolean;
  is_default: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

// Publish Target types
export interface PublishTarget {
  id: string;
  project_id?: string;
  type: string;
  name: string;
  telegram_chat_id?: number;
  telegram_chat_username?: string;
  settings?: Record<string, unknown>;
  is_active: boolean;
  total_published: number;
  last_published_at?: string;
  created_at: string;
  updated_at: string;
}