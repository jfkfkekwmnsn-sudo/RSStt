export type SourceType = 'rss' | 'scraper' | 'custom' | 'webhook';

export interface NormalizationRules {
  remove_utm: boolean;
  remove_ref: boolean;
  custom_params_to_remove: string[];
}

export interface Source {
  id: string;
  project_id?: string;
  type: SourceType;
  name: string;
  feed_url: string;
  is_active: boolean;
  is_trusted: boolean;
  fetch_interval_minutes: number;
  max_items_per_fetch: number;
  normalization_rules?: NormalizationRules;
  reputation_score: number;
  total_articles: number;
  approved_articles: number;
  rejected_articles: number;
  last_fetch_at?: string;
  last_error?: string;
  consecutive_errors: number;
  created_at: string;
  updated_at: string;
}

export interface SourceListItem {
  id: string;
  name: string;
  type: SourceType;
  is_active: boolean;
  is_trusted: boolean;
  reputation_score: number;
  total_articles: number;
  last_fetch_at?: string;
  consecutive_errors: number;
  created_at: string;
}

export interface SourceRun {
  id: string;
  source_id: string;
  started_at: string;
  finished_at?: string;
  status: string;
  articles_found: number;
  articles_new: number;
  articles_duplicate: number;
  error_message?: string;
}

export interface SourceCreate {
  name: string;
  feed_url: string;
  type?: SourceType;
  is_active?: boolean;
  is_trusted?: boolean;
  fetch_interval_minutes?: number;
  max_items_per_fetch?: number;
  normalization_rules?: NormalizationRules;
}

export interface SourceUpdate {
  name?: string;
  feed_url?: string;
  is_active?: boolean;
  is_trusted?: boolean;
  fetch_interval_minutes?: number;
  max_items_per_fetch?: number;
  normalization_rules?: NormalizationRules;
}