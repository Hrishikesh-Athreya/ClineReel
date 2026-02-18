export default function ActionButtons({
    onGenerate,
    onDownload,
    isGenerating,
    canDownload,
    videoPath
}) {
    const handleDownload = () => {
        if (videoPath) {
            // Create a link to download the video
            const link = document.createElement('a');
            link.href = videoPath;
            link.download = 'devpost-ad.mp4';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        onDownload?.();
    };

    return (
        <div className="flex flex-col gap-3">
            <button
                onClick={onGenerate}
                disabled={isGenerating}
                className="w-full h-12 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-xl font-bold shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 transition-all transform active:scale-[0.98] disabled:cursor-not-allowed disabled:transform-none"
            >
                {isGenerating ? (
                    <>
                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Generating...
                    </>
                ) : (
                    <>
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        Generate Video
                    </>
                )}
            </button>

            <button
                onClick={handleDownload}
                disabled={!canDownload}
                className="w-full h-12 bg-transparent hover:bg-slate-200/50 dark:hover:bg-white/5 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-semibold flex items-center justify-center gap-2 transition-colors border border-transparent hover:border-slate-200 dark:hover:border-slate-700 disabled:hover:border-transparent disabled:hover:bg-transparent"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download Ad
            </button>
        </div>
    );
}
