import { useState, useEffect, useCallback } from 'react';
import { getJobStatus } from '../api/client';

export function useJobPolling(jobId, interval = 2000) {
    const [status, setStatus] = useState(null);
    const [error, setError] = useState(null);
    const [isPolling, setIsPolling] = useState(false);

    useEffect(() => {
        if (!jobId) return;

        let timeoutId;
        let mounted = true;

        const poll = async () => {
            try {
                const result = await getJobStatus(jobId);

                if (!mounted) return;

                setStatus(result);

                if (result.status === 'completed' || result.status === 'failed') {
                    setIsPolling(false);
                } else {
                    timeoutId = setTimeout(poll, interval);
                }
            } catch (err) {
                if (!mounted) return;
                setError(err.message);
                setIsPolling(false);
            }
        };

        setIsPolling(true);
        setError(null);
        poll();

        return () => {
            mounted = false;
            clearTimeout(timeoutId);
            setIsPolling(false);
        };
    }, [jobId, interval]);

    return { status, error, isPolling };
}
