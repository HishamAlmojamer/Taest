import { get, post, put } from './client';
import type { PaginatedResponse } from '@/types';

export async function getProjects(params?: Record<string, unknown>) {
  return await get<PaginatedResponse<unknown>>('/projects', params);
}

export async function getProject(id: string) {
  return await get(`/projects/${id}`);
}

export async function createProject(data: unknown) {
  return await post('/projects', data);
}

export async function updateProject(id: string, data: unknown) {
  return await put(`/projects/${id}`, data);
}

export async function getProjectTasks(projectId: string) {
  return await get(`/projects/${projectId}/tasks`);
}

export async function createProjectTask(projectId: string, data: unknown) {
  return await post(`/projects/${projectId}/tasks`, data);
}

export async function updateProjectTask(projectId: string, taskId: string, data: unknown) {
  return await put(`/projects/${projectId}/tasks/${taskId}`, data);
}
