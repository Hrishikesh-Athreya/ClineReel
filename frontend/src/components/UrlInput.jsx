import { useState } from 'react';

export default function UrlInput({ onSubmit, isDisabled }) {
    const [url, setUrl] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (url.trim() && !isDisabled) {
            onSubmit(url.trim());
        }
    };

    return (
        <div className="flex flex-col gap-3">
            <label className="text-slate-900 dark:text-white text-base font-semibold">
                Project Source
            </label>
            <form onSubmit={handleSubmit} className="relative flex items-center group">
                <span className="absolute left-5 text-slate-400 group-focus-within:text-violet-500 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                </span>
                <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={isDisabled}
                    className="w-full h-16 pl-14 pr-6 rounded-2xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:border-violet-500 focus:ring-4 focus:ring-violet-500/10 transition-all outline-none text-slate-900 dark:text-white placeholder:text-slate-400 text-lg font-medium shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    placeholder="Paste Website URL here..."
                />
            </form>
        </div>
    );
}
