/**
 * R2 storage operations
 */

import { Env, BackupMetadata, UsageData, TIERS } from './types';

/**
 * Generate R2 object key from device_id and backup key
 */
export function getObjectKey(deviceId: string, key: string): string {
  // Sanitize inputs
  const sanitizedDeviceId = deviceId.replace(/[^a-zA-Z0-9_-]/g, '');
  const sanitizedKey = key.replace(/[^a-zA-Z0-9_.-]/g, '');
  return `${sanitizedDeviceId}/${sanitizedKey}`;
}

/**
 * Upload encrypted backup to R2
 */
export async function uploadBackup(
  env: Env,
  deviceId: string,
  key: string,
  data: ReadableStream | ArrayBuffer,
  metadata: {
    checksum?: string;
    contentType?: string;
  }
): Promise<BackupMetadata> {
  const objectKey = getObjectKey(deviceId, key);

  // Prepare custom metadata
  const customMetadata: Record<string, string> = {
    device_id: deviceId,
    uploaded_at: new Date().toISOString(),
  };

  if (metadata.checksum) {
    customMetadata.checksum = metadata.checksum;
  }

  // Upload to R2
  await env.BACKUP_BUCKET.put(objectKey, data, {
    httpMetadata: {
      contentType: metadata.contentType || 'application/octet-stream',
    },
    customMetadata,
  });

  // Get object to retrieve size
  const object = await env.BACKUP_BUCKET.head(objectKey);
  if (!object) {
    throw new Error('Failed to retrieve uploaded object');
  }

  return {
    device_id: deviceId,
    key,
    size: object.size,
    uploaded_at: customMetadata.uploaded_at,
    checksum: metadata.checksum,
    content_type: metadata.contentType || 'application/octet-stream',
  };
}

/**
 * Download backup from R2
 */
export async function downloadBackup(
  env: Env,
  deviceId: string,
  key: string
): Promise<R2ObjectBody | null> {
  const objectKey = getObjectKey(deviceId, key);
  return await env.BACKUP_BUCKET.get(objectKey);
}

/**
 * Delete backup from R2
 */
export async function deleteBackup(
  env: Env,
  deviceId: string,
  key: string
): Promise<boolean> {
  const objectKey = getObjectKey(deviceId, key);
  await env.BACKUP_BUCKET.delete(objectKey);
  return true;
}

/**
 * Check if backup exists
 */
export async function backupExists(
  env: Env,
  deviceId: string,
  key: string
): Promise<boolean> {
  const objectKey = getObjectKey(deviceId, key);
  const object = await env.BACKUP_BUCKET.head(objectKey);
  return object !== null;
}

/**
 * Get backup metadata
 */
export async function getBackupMetadata(
  env: Env,
  deviceId: string,
  key: string
): Promise<BackupMetadata | null> {
  const objectKey = getObjectKey(deviceId, key);
  const object = await env.BACKUP_BUCKET.head(objectKey);

  if (!object) {
    return null;
  }

  return {
    device_id: deviceId,
    key,
    size: object.size,
    uploaded_at: object.customMetadata?.uploaded_at || object.uploaded.toISOString(),
    checksum: object.customMetadata?.checksum,
    content_type: object.httpMetadata?.contentType || 'application/octet-stream',
  };
}

/**
 * List all backups for a device
 */
export async function listBackups(
  env: Env,
  deviceId: string
): Promise<Array<{ key: string; size: number; uploaded_at: string; checksum?: string }>> {
  const prefix = `${deviceId}/`;
  const listed = await env.BACKUP_BUCKET.list({ prefix });

  return listed.objects.map((obj) => ({
    key: obj.key.substring(prefix.length), // Remove device_id prefix
    size: obj.size,
    uploaded_at: obj.customMetadata?.uploaded_at || obj.uploaded.toISOString(),
    checksum: obj.customMetadata?.checksum,
  }));
}

/**
 * Get current usage for a device
 */
export async function getUsage(
  env: Env,
  deviceId: string
): Promise<UsageData> {
  const backups = await listBackups(env, deviceId);
  const totalBytes = backups.reduce((sum, backup) => sum + backup.size, 0);

  // Get tier from cached usage data or default to free
  let tier: 'free' | 'basic' | 'pro' | 'clinic' = 'free';
  const cachedUsage = await env.USAGE.get(`usage:${deviceId}`, 'json');
  if (cachedUsage && typeof cachedUsage === 'object' && 'tier' in cachedUsage) {
    tier = (cachedUsage as UsageData).tier;
  }

  const usage: UsageData = {
    device_id: deviceId,
    tier,
    total_bytes: totalBytes,
    backup_count: backups.length,
    last_updated: new Date().toISOString(),
  };

  // Cache usage data (expires after 1 hour)
  await env.USAGE.put(`usage:${deviceId}`, JSON.stringify(usage), {
    expirationTtl: 3600,
  });

  return usage;
}

/**
 * Check if upload would exceed quota
 */
export async function wouldExceedQuota(
  env: Env,
  deviceId: string,
  tier: 'free' | 'basic' | 'pro' | 'clinic',
  uploadSize: number
): Promise<{ exceeded: boolean; currentUsage: number; quota: number }> {
  const usage = await getUsage(env, deviceId);
  const quota = TIERS[tier].storage_bytes;
  const newTotal = usage.total_bytes + uploadSize;

  return {
    exceeded: newTotal > quota,
    currentUsage: usage.total_bytes,
    quota,
  };
}
