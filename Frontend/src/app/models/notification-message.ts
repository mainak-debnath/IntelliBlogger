export interface NotificationMessage {
    type: 'success' | 'error' | 'info';
    message: string;
    show: boolean;
}