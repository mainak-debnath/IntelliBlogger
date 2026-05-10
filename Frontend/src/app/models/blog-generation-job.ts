export type BlogGenerationJobStatus = 'queued' | 'processing' | 'completed' | 'failed';

export interface BlogGenerationJob {
    id: number;
    youtube_link: string;
    tone: string;
    length: string;
    status: BlogGenerationJobStatus;
    title: string;
    generated_content: string;
    error_message: string;
    started_at: string | null;
    completed_at: string | null;
    created_at: string;
    updated_at: string;
}
