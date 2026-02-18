const STAGE_MESSAGES = {
    scraping: 'Scraping website...',
    analyzing: 'AI is analyzing...',
    storyboarding: 'Designing storyboard...',
    generating: 'Generating video...',
    rendering: 'Rendering video...',
};

export default function VideoPreview({ videoPath, isLoading, stage, stageDetail }) {
    const hasVideo = videoPath && !isLoading;

    const loadingMessage = STAGE_MESSAGES[stage] || 'Processing...';

    return (
        <div className="flex-1 flex flex-col gap-3">
            <div className="flex items-center justify-between">
                <label className="text-slate-900 dark:text-white text-sm font-semibold">
                    Preview
                </label>
                <span className="text-xs font-medium text-slate-400 bg-white dark:bg-slate-800 px-2 py-1 rounded shadow-sm border border-slate-100 dark:border-slate-700">
                    1920 x 1080
                </span>
            </div>
            <div className="relative w-full aspect-video rounded-2xl bg-white dark:bg-slate-800 shadow-sm border border-slate-200 dark:border-slate-700 flex items-center justify-center overflow-hidden">
                {hasVideo ? (
                    <video
                        src={videoPath}
                        controls
                        autoPlay
                        className="w-full h-full object-contain"
                    />
                ) : (
                    <>
                        {/* Background gradient */}
                        <div className="absolute inset-0 bg-gradient-to-br from-slate-100 via-white to-slate-50 dark:from-slate-700 dark:via-slate-800 dark:to-slate-700 opacity-50" />

                        {/* Dot grid overlay */}
                        <div
                            className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]"
                            style={{
                                backgroundImage: 'radial-gradient(#000 1px, transparent 1px)',
                                backgroundSize: '20px 20px'
                            }}
                        />

                        {/* Empty state content */}
                        <div className="relative flex flex-col items-center gap-3">
                            {isLoading ? (
                                <>
                                    <div className="w-16 h-16 rounded-full bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center text-violet-500">
                                        <svg className="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                    </div>
                                    <p className="text-violet-500 text-sm font-medium">{loadingMessage}</p>
                                    {stageDetail && (
                                        <p className="text-slate-400 text-xs max-w-[250px] text-center truncate">{stageDetail}</p>
                                    )}
                                </>
                            ) : (
                                <>
                                    <div className="w-16 h-16 rounded-full bg-slate-50 dark:bg-slate-700 flex items-center justify-center text-slate-300 dark:text-slate-500">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                    </div>
                                    <p className="text-slate-400 text-sm font-medium">Video preview will appear here</p>
                                </>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
