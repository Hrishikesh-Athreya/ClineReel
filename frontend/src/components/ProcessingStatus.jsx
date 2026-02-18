const STAGES = [
    { key: 'scraping', label: 'Scraping website' },
    { key: 'analyzing', label: 'Analyst AI extracting insights' },
    { key: 'storyboarding', label: 'Creative Director designing storyboard' },
    { key: 'generating', label: 'Generating video props' },
    { key: 'rendering', label: 'Building & rendering video' },
];

// Map backend stage to step index
function stageToIndex(stage) {
    const idx = STAGES.findIndex((s) => s.key === stage);
    return idx >= 0 ? idx : -1;
}

function getStepState(stepIndex, activeIndex, jobStatus) {
    if (!jobStatus || jobStatus === 'idle') return 'pending';
    if (jobStatus === 'failed') {
        return stepIndex <= activeIndex ? 'error' : 'pending';
    }
    if (jobStatus === 'completed') return 'completed';

    if (stepIndex < activeIndex) return 'completed';
    if (stepIndex === activeIndex) return 'active';
    return 'pending';
}

function StepIcon({ state }) {
    if (state === 'completed') {
        return (
            <div className="relative z-10 flex-none w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center text-green-600 dark:text-green-400 ring-4 ring-white dark:ring-slate-800">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
            </div>
        );
    }

    if (state === 'active') {
        return (
            <div className="relative z-10 flex-none w-8 h-8">
                <div className="absolute inset-0 bg-violet-500 rounded-full blur opacity-40 animate-pulse" />
                <div className="relative w-full h-full rounded-full bg-white dark:bg-slate-800 border-2 border-violet-500 flex items-center justify-center text-violet-500 ring-4 ring-white dark:ring-slate-800">
                    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                </div>
            </div>
        );
    }

    if (state === 'error') {
        return (
            <div className="relative z-10 flex-none w-8 h-8 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-red-600 dark:text-red-400 ring-4 ring-white dark:ring-slate-800">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </div>
        );
    }

    return (
        <div className="relative z-10 flex-none w-8 h-8 rounded-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-300 dark:text-slate-600 ring-4 ring-white dark:ring-slate-800">
            <div className="w-2 h-2 rounded-full bg-current" />
        </div>
    );
}

export default function ProcessingStatus({ jobStatus, stage, stageDetail }) {
    const activeIndex = stageToIndex(stage);

    // Filter steps: in templated mode (no storyboarding stage), skip the storyboarding step
    // We show all 5 — unused ones will just show as completed quickly
    const steps = STAGES;

    return (
        <div className="flex flex-col gap-5 pt-4">
            <label className="text-slate-900 dark:text-white text-sm font-semibold uppercase tracking-wider opacity-80">
                Processing Status
            </label>
            <div className="flex flex-col gap-0 relative pl-2">
                {/* Vertical line */}
                <div className="absolute left-[19px] top-3 bottom-5 w-0.5 bg-slate-100 dark:bg-slate-700" />

                {steps.map((step, index) => {
                    const state = getStepState(index, activeIndex, jobStatus);
                    const isLast = index === steps.length - 1;
                    const isActive = index === activeIndex;

                    return (
                        <div key={step.key} className={`relative flex gap-4 ${!isLast ? 'pb-8' : ''}`}>
                            <StepIcon state={state} />
                            <div className={`flex flex-col pt-1.5 ${state === 'pending' ? 'opacity-50' : ''}`}>
                                <p className="text-slate-900 dark:text-white text-sm font-semibold">
                                    {step.label}
                                </p>
                                {state === 'completed' && jobStatus !== 'completed' && (
                                    <p className="text-slate-400 text-xs mt-0.5">Completed</p>
                                )}
                                {state === 'completed' && jobStatus === 'completed' && (
                                    <p className="text-green-500 text-xs font-medium mt-0.5">Done</p>
                                )}
                                {state === 'active' && (
                                    <p className="text-violet-500 text-xs font-medium mt-0.5 max-w-[250px] truncate">
                                        {stageDetail || 'Processing...'}
                                    </p>
                                )}
                                {state === 'error' && (
                                    <p className="text-red-500 text-xs font-medium mt-0.5">Failed</p>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
