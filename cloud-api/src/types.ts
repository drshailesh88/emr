/**
 * TypeScript types and interfaces for DocAssist Cloud API
 */

export interface Env {
  BACKUP_BUCKET: R2Bucket;
  API_KEYS: KVNamespace;
  USAGE: KVNamespace;
  RATE_LIMIT: KVNamespace;
  ENVIRONMENT: string;
  MAX_REQUESTS_PER_MINUTE: string;
  MAX_BACKUP_SIZE_MB: string;
}

export interface ApiKeyData {
  api_key: string;
  device_id: string;
  tier: Tier;
  created_at: string;
  last_used_at?: string;
}

export type Tier = 'free' | 'basic' | 'pro' | 'clinic';

export interface TierConfig {
  storage_bytes: number;
  price: number;
}

export const TIERS: Record<Tier, TierConfig> = {
  free: { storage_bytes: 1 * 1024 * 1024 * 1024, price: 0 },      // 1 GB
  basic: { storage_bytes: 10 * 1024 * 1024 * 1024, price: 99 },   // 10 GB
  pro: { storage_bytes: 50 * 1024 * 1024 * 1024, price: 299 },    // 50 GB
  clinic: { storage_bytes: 200 * 1024 * 1024 * 1024, price: 999 } // 200 GB
};

export interface BackupMetadata {
  device_id: string;
  key: string;
  size: number;
  uploaded_at: string;
  checksum?: string;
  content_type: string;
}

export interface UsageData {
  device_id: string;
  tier: Tier;
  total_bytes: number;
  backup_count: number;
  last_updated: string;
}

export interface AccountInfo {
  device_id: string;
  tier: Tier;
  quota_bytes: number;
  used_bytes: number;
  backup_count: number;
  percentage_used: number;
}

export interface ApiError {
  error: string;
  message: string;
  status: number;
}

export interface ListBackupsResponse {
  device_id: string;
  backups: Array<{
    key: string;
    size: number;
    uploaded_at: string;
    checksum?: string;
  }>;
  total_count: number;
  total_size: number;
}

export interface RateLimitInfo {
  count: number;
  reset_at: number;
}
