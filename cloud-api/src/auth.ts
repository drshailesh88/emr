/**
 * Authentication and authorization handlers
 */

import { Env, ApiKeyData, ApiError } from './types';

/**
 * Extract Bearer token from Authorization header
 */
export function extractToken(request: Request): string | null {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }
  return authHeader.substring(7); // Remove 'Bearer ' prefix
}

/**
 * Validate API key and return associated data
 */
export async function validateApiKey(
  apiKey: string,
  env: Env
): Promise<ApiKeyData | null> {
  try {
    const data = await env.API_KEYS.get(apiKey, 'json');
    if (!data) {
      return null;
    }

    // Update last_used_at timestamp
    const apiKeyData = data as ApiKeyData;
    apiKeyData.last_used_at = new Date().toISOString();
    await env.API_KEYS.put(apiKey, JSON.stringify(apiKeyData));

    return apiKeyData;
  } catch (error) {
    console.error('Error validating API key:', error);
    return null;
  }
}

/**
 * Check if request is rate limited
 * Returns true if rate limit exceeded
 */
export async function isRateLimited(
  apiKey: string,
  env: Env
): Promise<boolean> {
  const maxRequests = parseInt(env.MAX_REQUESTS_PER_MINUTE || '100', 10);
  const now = Date.now();
  const windowMs = 60 * 1000; // 1 minute
  const key = `ratelimit:${apiKey}:${Math.floor(now / windowMs)}`;

  try {
    const current = await env.RATE_LIMIT.get(key);
    const count = current ? parseInt(current, 10) : 0;

    if (count >= maxRequests) {
      return true;
    }

    // Increment counter
    await env.RATE_LIMIT.put(
      key,
      String(count + 1),
      { expirationTtl: 120 } // 2 minutes TTL to be safe
    );

    return false;
  } catch (error) {
    console.error('Error checking rate limit:', error);
    // Fail open - allow request if rate limit check fails
    return false;
  }
}

/**
 * Authenticate request and return API key data
 */
export async function authenticate(
  request: Request,
  env: Env
): Promise<{ success: true; data: ApiKeyData } | { success: false; error: ApiError }> {
  // Extract token
  const token = extractToken(request);
  if (!token) {
    return {
      success: false,
      error: {
        error: 'unauthorized',
        message: 'Missing or invalid Authorization header',
        status: 401
      }
    };
  }

  // Check rate limit
  const rateLimited = await isRateLimited(token, env);
  if (rateLimited) {
    return {
      success: false,
      error: {
        error: 'rate_limit_exceeded',
        message: 'Too many requests. Please try again later.',
        status: 429
      }
    };
  }

  // Validate API key
  const apiKeyData = await validateApiKey(token, env);
  if (!apiKeyData) {
    return {
      success: false,
      error: {
        error: 'unauthorized',
        message: 'Invalid API key',
        status: 401
      }
    };
  }

  return { success: true, data: apiKeyData };
}

/**
 * Check if device_id in request matches authenticated device
 */
export function authorizeDevice(
  requestDeviceId: string,
  apiKeyData: ApiKeyData
): boolean {
  return requestDeviceId === apiKeyData.device_id;
}
