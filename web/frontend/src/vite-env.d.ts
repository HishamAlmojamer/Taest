/// <reference types="vite/client" />
declare module 'axios' {
  export interface AxiosRequestConfig {
    data?: any;
    params?: any;
    headers?: any;
  }
  export interface AxiosResponse {
    data: any;
    status: number;
    statusText: string;
    headers: any;
    config: AxiosRequestConfig;
  }
  export interface AxiosError {
    response?: AxiosResponse;
    message: string;
    config: AxiosRequestConfig;
  }
  const axios: {
    create(config?: any): any;
    get<T>(url: string, config?: any): Promise<AxiosResponse<T>>;
    post<T>(url: string, data?: any, config?: any): Promise<AxiosResponse<T>>;
    put<T>(url: string, data?: any, config?: any): Promise<AxiosResponse<T>>;
    delete<T>(url: string, config?: any): Promise<AxiosResponse<T>>;
  };
  export default axios;
}
