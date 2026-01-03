/**
 * Utility functions
 */

import { ApiError } from './types';

/**
 * Create JSON response with CORS headers
 */
export function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, HEAD, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Backup-Checksum',
      'Access-Control-Expose-Headers': 'X-Backup-Checksum, X-Uploaded-At, X-Backup-Exists',
    },
  });
}

/**
 * Create error response
 */
export function errorResponse(
  error: string,
  message: string,
  status = 400
): Response {
  const apiError: ApiError = {
    error,
    message,
    status,
  };
  return jsonResponse(apiError, status);
}

/**
 * Handle CORS preflight requests
 */
export function handleCors(): Response {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, HEAD, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Backup-Checksum',
      'Access-Control-Max-Age': '86400',
    },
  });
}

/**
 * Parse URL path parameters
 */
export function parsePathParams(pathname: string): {
  deviceId?: string;
  key?: string;
  action?: string;
} {
  const parts = pathname.split('/').filter(Boolean);

  // Expected format: /v1/backups/:device_id/:key?/:action?
  if (parts.length < 3 || parts[0] !== 'v1' || parts[1] !== 'backups') {
    return {};
  }

  return {
    deviceId: parts[2],
    key: parts[3],
    action: parts[4],
  };
}
