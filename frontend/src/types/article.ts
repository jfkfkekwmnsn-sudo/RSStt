export type ArticleStatus = 
  | 'pending' 
  | 'approved' 
  | 'rejected' 
  | 'scheduled' 
  | 'published' 
  | 'failed' 
  | 'duplicate' 
  | 'needs_review';

export interface ImageInfo {
  url: string;
  alt?: string;
  width?: number;
  height?: number;
  is_main: boolean;
}

export interface QualityFactors {
  has_image: number;
  text_length: number;
  freshness: number;
  source_trust: number;
  uniqueness: number;
}

export interface PriorityFactors {
  category_weight: number;
  quality_bonus: number;
  freshness_bonus: number;
  source_bonus: number;
  media_bonus: number;
}

export interface Article {
  id: string;
  token: string;
  project_id?: string;
  source_id?: string;
  source_name?: string;
  url: string;
  title: string;
  description?: string;
  content_clean?: string;
  pub_date?: string;
  category?: string;
  tags?: string[];
  images?: ImageInfo[];
  main_image_url?: string;
  quality_score: number;
  quality_factors?: QualityFactors;
  priority_score: number;
  priority_factors?: PriorityFactors;
  status: ArticleStatus;
  batch_id?: string;
  ai_used: boolean;
  ai_metadata?: Record<string, any>;
  moderated_at?: string;
  moderator_id?: string;
  moderator_name?: string;
  rejection_reason?: string;
  published_at?: string;
  scheduled_at?: string;
  published_target_id?: string;
  published_external_id?: string;
  similar_to_id?: string;
  similarity_score?: number;
  created_at: string;
  updated_at: string;
}

export interface ArticleListItem {
  id: string;
  token: string;
  title: string;
  category?: string;
  source_id?: string;
  source_name?: string;
  status: ArticleStatus;
  quality_score: number;
  priority_score: number;
  has_image: boolean;
  ai_used: boolean;
  pub_date?: string;
  created_at: string;
}

export interface ArticleDetail extends Article {
  similar_articles?: ArticleListItem[];
  versions_count: number;
}

export interface ArticleVersion {
  id: string;
  article_id: string;
  version_number: number;
  title: string;
  content_clean?: string;
  category?: string;
  tags?: string[];
  main_image_url?: string;
  created_at: string;
  created_by_id?: string;
  created_by_name?: string;
  change_summary?: string;
}

export interface ArticleFilters {
  status?: ArticleStatus[];
  category?: string;
  source_id?: string;
  has_image?: boolean;
  ai_used?: boolean;
  min_quality?: number;
  min_priority?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface ArticleUpdate {
  title?: string;
  description?: string;
  content_clean?: string;
  category?: string;
  tags?: string[];
  main_image_url?: string;
}

export interface ArticleApproveRequest {
  target_id?: string;
  schedule_at?: string;
  use_ai_rewrite?: boolean;
}

export interface ArticlePreview {
  text: string;
  has_image: boolean;
  image_url?: string;
  estimated_length: number;
  warnings: string[];
  is_valid_for_telegram: boolean;
}