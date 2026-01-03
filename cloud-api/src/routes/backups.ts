/**
 * Backup CRUD operations
 */

import { Env, ApiKeyData, ListBackupsResponse } from '../types';
import {
  uploadBackup,
  downloadBackup,
  deleteBackup,
  backupExists,
  getBackupMetadata,
  listBackups,
  wouldExceedQuota,
} from '../storage';
import { authorizeDevice } from '../auth';
import { jsonResponse, errorResponse } from '../utils';

/**
 * PUT /v1/backups/:device_id/:key
 * Upload encrypted backup
 */
export async function handleUpload(
  request: Request,
  env: Env,
  deviceId: string,
  key: string,
  apiKeyData: ApiKeyData
): Promise<Response> {
  // Authorize device
  if (!authorizeDevice(deviceId, apiKeyData)) {
    return errorResponse('forbidden', 'Device ID does not match API key', 403);
  }

  // Validate key format
  if (!key || key.length === 0 || key.length > 255) {
    return errorResponse('invalid_request', 'Invalid backup key', 400);
  }

  // Get content length
  const contentLength = request.headers.get('content-length');
  if (!contentLength) {
    return errorResponse('invalid_request', 'Content-Length header required', 400);
  }

  const uploadSize = parseInt(contentLength, 10);
  const maxSizeMB = parseInt(env.MAX_BACKUP_SIZE_MB || '100', 10);
  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  if (uploadSize > maxSizeBytes) {
    return errorResponse(
      'payload_too_large',
      `Backup size exceeds maximum of ${maxSizeMB}MB`,
      413
    );
  }

  // Check quota
  const quotaCheck = await wouldExceedQuota(env, deviceId, apiKeyData.tier, uploadSize);
  if (quotaCheck.exceeded) {
    return errorResponse(
      'quota_exceeded',
      `Upload would exceed storage quota. Used: ${Math.round(quotaCheck.currentUsage / 1024 / 1024)}MB, Quota: ${Math.round(quotaCheck.quota / 1024 / 1024)}MB`,
      413
    );
  }

  // Get optional metadata from headers
  const checksum = request.headers.get('x-backup-checksum') || undefined;
  const contentType = request.headers.get('content-type') || 'application/octet-stream';

  // Upload to R2
  try {
    const body = request.body;
    if (!body) {
      return errorResponse('invalid_request', 'Request body required', 400);
    }

    const metadata = await uploadBackup(env, deviceId, key, body, {
      checksum,
      contentType,
    });

    return jsonResponse(
      {
        success: true,
        message: 'Backup uploaded successfully',
        metadata,
      },
      201
    );
  } catch (error) {
    console.error('Upload error:', error);
    return errorResponse('upload_failed', 'Failed to upload backup', 500);
  }
}

/**
 * GET /v1/backups/:device_id/:key
 * Download backup
 */
export async function handleDownload(
  request: Request,
  env: Env,
  deviceId: string,
  key: string,
  apiKeyData: ApiKeyData
): Promise<Response> {
  // Authorize device
  if (!authorizeDevice(deviceId, apiKeyData)) {
    return errorResponse('forbidden', 'Device ID does not match API key', 403);
  }

  try {
    const object = await downloadBackup(env, deviceId, key);

    if (!object) {
      return errorResponse('not_found', 'Backup not found', 404);
    }

    // Return the encrypted blob
    const headers = new Headers();
    headers.set('Content-Type', object.httpMetadata?.contentType || 'application/octet-stream');
    headers.set('Content-Length', String(object.size));

    if (object.customMetadata?.checksum) {
      headers.set('X-Backup-Checksum', object.customMetadata.checksum);
    }

    if (object.customMetadata?.uploaded_at) {
      headers.set('X-Uploaded-At', object.customMetadata.uploaded_at);
    }

    // Add CORS headers
    headers.set('Access-Control-Allow-Origin', '*');
    headers.set('Access-Control-Expose-Headers', 'X-Backup-Checksum, X-Uploaded-At');

    return new Response(object.body, {
      status: 200,
      headers,
    });
  } catch (error) {
    console.error('Download error:', error);
    return errorResponse('download_failed', 'Failed to download backup', 500);
  }
}

/**
 * DELETE /v1/backups/:device_id/:key
 * Delete backup
 */
export async function handleDelete(
  request: Request,
  env: Env,
  deviceId: string,
  key: string,
  apiKeyData: ApiKeyData
): Promise<Response> {
  // Authorize device
  if (!authorizeDevice(deviceId, apiKeyData)) {
    return errorResponse('forbidden', 'Device ID does not match API key', 403);
  }

  try {
    // Check if exists first
    const exists = await backupExists(env, deviceId, key);
    if (!exists) {
      return errorResponse('not_found', 'Backup not found', 404);
    }

    await deleteBackup(env, deviceId, key);

    return jsonResponse({
      success: true,
      message: 'Backup deleted successfully',
    });
  } catch (error) {
    console.error('Delete error:', error);
    return errorResponse('delete_failed', 'Failed to delete backup', 500);
  }
}

/**
 * GET /v1/backups/:device_id
 * List all backups for device
 */
export async function handleList(
  request: Request,
  env: Env,
  deviceId: string,
  apiKeyData: ApiKeyData
): Promise<Response> {
  // Authorize device
  if (!authorizeDevice(deviceId, apiKeyData)) {
    return errorResponse('forbidden', 'Device ID does not match API key', 403);
  }

  try {
    const backups = await listBackups(env, deviceId);

    const response: ListBackupsResponse = {
      device_id: deviceId,
      backups,
      total_count: backups.length,
      total_size: backups.reduce((sum, b) => sum + b.size, 0),
    };

    return jsonResponse(response);
  } catch (error) {
    console.error('List error:', error);
    return errorResponse('list_failed', 'Failed to list backups', 500);
  }
}

/**
 * HEAD /v1/backups/:device_id/:key
 * Check if backup exists
 */
export async function handleExists(
  request: Request,
  env: Env,
  deviceId: string,
  key: string,
  apiKeyData: ApiKeyData
): Promise<Response> {
  // Authorize device
  if (!authorizeDevice(deviceId, apiKeyData)) {
    return errorResponse('forbidden', 'Device ID does not match API key', 403);
  }

  try {
    const exists = await backupExists(env, deviceId, key);

    if (exists) {
      const metadata = await getBackupMetadata(env, deviceId, key);
      const headers = new Headers();
      headers.set('X-Backup-Exists', 'true');

      if (metadata) {
        headers.set('Content-Length', String(metadata.size));
        headers.set('X-Uploaded-At', metadata.uploaded_at);
        if (metadata.checksum) {
          headers.set('X-Backup-Checksum', metadata.checksum);
        }
      }

      // Add CORS headers
      headers.set('Access-Control-Allow-Origin', '*');
      headers.set('Access-Control-Expose-Headers', 'X-Backup-Exists, X-Uploaded-At, X-Backup-Checksum');

      return new Response(null, { status: 200, headers });
    } else {
      return new Response(null, { status: 404 });
    }
  } catch (error) {
    console.error('Exists check error:', error);
    return errorResponse('check_failed', 'Failed to check backup existence', 500);
  }
}

/**
 * GET /v1/backups/:device_id/:key/metadata
 * Get backup metadata
 */
export async function handleGetMetadata(
  request: Request,
  env: Env,
  deviceId: string,
  key: string,
  apiKeyData: ApiKeyData
): Promise<Response> {
  // Authorize device
  if (!authorizeDevice(deviceId, apiKeyData)) {
    return errorResponse('forbidden', 'Device ID does not match API key', 403);
  }

  try {
    const metadata = await getBackupMetadata(env, deviceId, key);

    if (!metadata) {
      return errorResponse('not_found', 'Backup not found', 404);
    }

    return jsonResponse(metadata);
  } catch (error) {
    console.error('Metadata error:', error);
    return errorResponse('metadata_failed', 'Failed to retrieve metadata', 500);
  }
}
