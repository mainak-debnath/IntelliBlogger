export interface SaveBlogResponse {
    id: number;
    title: string;
    message: string;
    status: 'created' | 'updated' | 'exists';
}
