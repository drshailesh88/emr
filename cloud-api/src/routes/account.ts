/**
 * Account information and quota management
 */

import { Env, ApiKeyData, AccountInfo, TIERS } from '../types';
import { getUsage } from '../storage';
import { jsonResponse, errorResponse } from '../utils';

/**
 * GET /v1/account
 * Get account information including quota and usage
 */
export async function handleGetAccount(
  request: Request,
  env: Env,
  apiKeyData: ApiKeyData
): Promise<Response> {
  try {
    const usage = await getUsage(env, apiKeyData.device_id);
    const quota = TIERS[apiKeyData.tier].storage_bytes;

    const accountInfo: AccountInfo = {
      device_id: apiKeyData.device_id,
      tier: apiKeyData.tier,
      quota_bytes: quota,
      used_bytes: usage.total_bytes,
      backup_count: usage.backup_count,
      percentage_used: Math.round((usage.total_bytes / quota) * 100 * 100) / 100, // 2 decimal places
    };

    return jsonResponse(accountInfo);
  } catch (error) {
    console.error('Account info error:', error);
    return errorResponse('account_failed', 'Failed to retrieve account information', 500);
  }
}
