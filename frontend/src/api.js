/**
 * API service module for making requests to the backend
 */

const API_BASE_URL = 'http://127.0.0.1:5000/api/v1';

const toQuery = (filters = {}) => {
  const {
    locationId,
    startDate,
    endDate,
    metric,
    qualityThreshold,
  } = filters;

  const params = {
    ...(locationId ? { location_id: locationId } : {}),
    ...(startDate ? { start_date: startDate } : {}),
    ...(endDate ? { end_date: endDate } : {}),
    ...(metric ? { metric } : {}),
    ...(qualityThreshold ? { quality_threshold: qualityThreshold } : {}),
  };

  return new URLSearchParams(params).toString();
};

const request = async (path, params) => {
  const qs = params ? `?${toQuery(params)}` : '';
  const url = `${API_BASE_URL}${path}${qs}`;

  let res;
  try {
    res = await fetch(url, {
      headers: { Accept: 'application/json' },
    });
  } catch (networkErr) {
    const err = new Error('Network error connecting to API');
    err.cause = networkErr;
    throw err;
  }

  const isJson = (res.headers.get('content-type') || '').includes('application/json');
  const body = isJson ? await res.json().catch(() => null) : await res.text();

  if (!res.ok) {
    const message =
      (body && body.error) ||
      (typeof body === 'string' && body) ||
      `Request failed with status ${res.status}`;
    const err = new Error(message);
    err.status = res.status;
    err.body = body;
    throw err;
  }

  return body;
};

/**
 * Fetch climate data with optional filters
 * @param {Object} filters - Filter parameters
 * @returns {Promise<Array>} - Array of climate records
 */
export const getClimateData = async (filters = {}) => {
  try {
    const payload = await request('/climate', filters);
    return payload?.data ?? [];
  } catch (error) {
    console.error('API Error (getClimateData):', error);
    throw error;
  }
};

/**
 * Fetch all available locations
 * @returns {Promise<Array>} - Array of locations
 */
export const getLocations = async () => {
  try {
    const payload = await request('/locations');
    return payload?.data ?? [];
  } catch (error) {
    console.error('API Error (getLocations):', error);
    throw error;
  }
};

/**
 * Fetch all available metrics
 * @returns {Promise<Array>} - Array of metrics
 */
export const getMetrics = async () => {
  try {
    const payload = await request('/metrics');
    return payload?.data ?? [];
  } catch (error) {
    console.error('API Error (getMetrics):', error);
    throw error;
  }
};

/**
 * Fetch climate summary statistics with optional filters
 * @param {Object} filters - Filter parameters
 * @returns {Promise<Object>} - Summary keyed by metric
 */

export const getClimateSummary = async (filters = {}) => {
  try {
    const payload = await request('/summary', filters);
    return payload?.data ?? {};
  } catch (error) {
    console.error('API Error (getClimateSummary):', error);
    throw error;
  }
};

/**
 * Fetch trend analysis with optional filters
 * @param {Object} filters - Filter parameters
 * @returns {Promise<Object>} - Trend analysis keyed by metric
 */
export const getTrends = async (filters = {}) => {
  try {
    const payload = await request('/trends', filters);
    return payload?.data ?? {};
  } catch (error) {
    console.error('API Error (getTrends):', error);
    throw error;
  }
};