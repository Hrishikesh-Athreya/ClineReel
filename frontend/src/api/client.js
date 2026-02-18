const API_BASE = '/api';

export async function generateVideo(url) {
    const response = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate video');
    }

    return response.json();
}

export async function getJobStatus(jobId) {
    const response = await fetch(`${API_BASE}/status/${jobId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get job status');
    }

    return response.json();
}
