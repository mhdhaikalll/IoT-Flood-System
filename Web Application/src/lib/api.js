/**
 * API Service for Flood Detection System
 * 
 * This module provides functions to interact with the FastAPI backend
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

/**
 * Check backend health status
 */
export async function getHealth() {
    try {
        const response = await fetch(`${BACKEND_URL}/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Health check failed:', error);
        return null;
    }
}

/**
 * Get flood prediction
 * @param {string} nodeId - Optional node ID to filter prediction
 * @param {number} hoursAhead - Hours to predict ahead (default: 6)
 */
export async function getPrediction(nodeId = null, hoursAhead = 6) {
    try {
        const response = await fetch(`${BACKEND_URL}/api/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                node_id: nodeId,
                hours_ahead: hoursAhead
            }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Prediction failed:', error);
        throw error;
    }
}

/**
 * Get historical sensor data
 * @param {string} nodeId - Optional node ID to filter data
 * @param {number} limit - Maximum records to return (default: 100)
 */
export async function getHistory(nodeId = null, limit = 100) {
    try {
        const params = new URLSearchParams();
        if (nodeId) params.append('node_id', nodeId);
        params.append('limit', limit.toString());
        
        const response = await fetch(`${BACKEND_URL}/api/history?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Failed to get history:', error);
        return { count: 0, data: [] };
    }
}

/**
 * Get status for a specific node
 * @param {string} nodeId - Node ID
 */
export async function getNodeStatus(nodeId) {
    try {
        const response = await fetch(`${BACKEND_URL}/api/status/${nodeId}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Failed to get status for node ${nodeId}:`, error);
        return null;
    }
}

/**
 * Submit sensor data (for testing/simulation)
 * @param {Object} data - Sensor data object
 */
export async function submitSensorData(data) {
    try {
        const response = await fetch(`${BACKEND_URL}/api/sensor-data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Failed to submit sensor data:', error);
        throw error;
    }
}

/**
 * Get all nodes with their status (online/offline detection)
 * Uses the dedicated /api/nodes endpoint for proper status tracking
 */
export async function getAllNodes() {
    try {
        const response = await fetch(`${BACKEND_URL}/api/nodes`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Failed to get nodes:', error);
        // Fallback to old method if new endpoint fails
        return await getAllNodesFallback();
    }
}

/**
 * Fallback method to get nodes from history
 */
async function getAllNodesFallback() {
    try {
        const history = await getHistory(null, 1000);
        const nodes = new Map();
        
        for (const reading of history.data) {
            const nodeId = reading.node_id;
            if (!nodes.has(nodeId) || 
                new Date(reading.timestamp) > new Date(nodes.get(nodeId).timestamp)) {
                nodes.set(nodeId, reading);
            }
        }
        
        const nodesList = Array.from(nodes.entries()).map(([nodeId, data]) => ({
            node_id: nodeId,
            location: data.location || 'Unknown',
            status: 'unknown',
            is_online: false,
            last_seen: data.timestamp,
            last_seen_ago: 'Unknown',
            water_level: parseFloat(data.ultrasonic_value) || 0,
            rain_intensity: parseFloat(data.rain_sensor_value) || 0,
            piezo_value: parseFloat(data.piezo_value) || 0,
            flood_risk: 'unknown',
            risk_percentage: 0
        }));
        
        return {
            count: nodesList.length,
            nodes: nodesList,
            summary: {
                online: 0,
                idle: 0,
                offline: nodesList.length,
                total: nodesList.length
            }
        };
    } catch (error) {
        console.error('Failed to get nodes (fallback):', error);
        return { count: 0, nodes: [], summary: { online: 0, idle: 0, offline: 0, total: 0 } };
    }
}

/**
 * Format risk level with color class
 * @param {string} risk - Risk level (low, moderate, high, critical)
 */
export function getRiskColor(risk) {
    const colors = {
        low: 'text-green-500',
        moderate: 'text-yellow-500',
        high: 'text-orange-500',
        critical: 'text-red-500'
    };
    return colors[risk?.toLowerCase()] || 'text-gray-500';
}

/**
 * Format risk level with background color class
 * @param {string} risk - Risk level
 */
export function getRiskBgColor(risk) {
    const colors = {
        low: 'bg-green-100 dark:bg-green-900',
        moderate: 'bg-yellow-100 dark:bg-yellow-900',
        high: 'bg-orange-100 dark:bg-orange-900',
        critical: 'bg-red-100 dark:bg-red-900'
    };
    return colors[risk?.toLowerCase()] || 'bg-gray-100 dark:bg-gray-900';
}

/**
 * Get status badge color classes
 * @param {string} status - Node status (online, idle, offline)
 */
export function getStatusColor(status) {
    const colors = {
        online: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100',
        idle: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100',
        offline: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
    };
    return colors[status?.toLowerCase()] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100';
}

export default {
    getHealth,
    getPrediction,
    getHistory,
    getNodeStatus,
    submitSensorData,
    getAllNodes,
    getRiskColor,
    getRiskBgColor
};
