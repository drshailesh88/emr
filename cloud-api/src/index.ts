/**
 * DocAssist Cloud API - Main Worker Entry Point
 *
 * Zero-knowledge encrypted backup storage using Cloudflare Workers + R2
 */

import { Env } from './types';
import { authenticate } from './auth';
import {
  handleUpload,
  handleDownload,
  handleDelete,
  handleList,
  handleExists,
  handleGetMetadata,
} from './routes/backups';
import { handleGetAccount } from './routes/account';
import { jsonResponse, errorResponse, handleCors, parsePathParams } from './utils';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return handleCors();
    }

    const url = new URL(request.url);
    const { pathname } = url;

    // Health check endpoint
    if (pathname === '/health' || pathname === '/') {
      return jsonResponse({
        status: 'ok',
        service: 'docassist-cloud-api',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
      });
    }

    // All API endpoints require authentication
    const authResult = await authenticate(request, env);
    if (!authResult.success) {
      return errorResponse(
        authResult.error.error,
        authResult.error.message,
        authResult.error.status
      );
    }

    const apiKeyData = authResult.data;

    // Route: GET /v1/account
    if (pathname === '/v1/account' && request.method === 'GET') {
      return handleGetAccount(request, env, apiKeyData);
    }

    // Route: Backup operations /v1/backups/:device_id/:key?/:action?
    if (pathname.startsWith('/v1/backups/')) {
      const { deviceId, key, action } = parsePathParams(pathname);

      if (!deviceId) {
        return errorResponse('invalid_request', 'Device ID required', 400);
      }

      // GET /v1/backups/:device_id - List backups
      if (!key && request.method === 'GET') {
        return handleList(request, env, deviceId, apiKeyData);
      }

      if (!key) {
        return errorResponse('invalid_request', 'Backup key required', 400);
      }

      // GET /v1/backups/:device_id/:key/metadata - Get metadata
      if (action === 'metadata' && request.method === 'GET') {
        return handleGetMetadata(request, env, deviceId, key, apiKeyData);
      }

      // PUT /v1/backups/:device_id/:key - Upload backup
      if (request.method === 'PUT') {
        return handleUpload(request, env, deviceId, key, apiKeyData);
      }

      // GET /v1/backups/:device_id/:key - Download backup
      if (request.method === 'GET') {
        return handleDownload(request, env, deviceId, key, apiKeyData);
      }

      // DELETE /v1/backups/:device_id/:key - Delete backup
      if (request.method === 'DELETE') {
        return handleDelete(request, env, deviceId, key, apiKeyData);
      }

      // HEAD /v1/backups/:device_id/:key - Check if exists
      if (request.method === 'HEAD') {
        return handleExists(request, env, deviceId, key, apiKeyData);
      }
    }

    // Route not found
    return errorResponse('not_found', 'Endpoint not found', 404);
  },
};
