import api from './client'

// ─── Types ────────────────────────────────────────────────────────────────────

export type UserRole = 'super_admin' | 'manager' | 'staff'
export type ItemStatus = 'available' | 'not_available' | 'today_special'
export type SessionPeriod = 'breakfast' | 'lunch' | 'dinner' | 'all_day'
export type DeviceStatus = 'active' | 'inactive' | 'unregistered'

export interface User {
  id: number; username: string; email: string; full_name: string
  role: UserRole; is_active: boolean; restaurant_id: number | null
  created_at: string; last_login: string | null
}

export interface Restaurant {
  id: number; name: string; slug: string; logo_url: string | null
  is_active: boolean; created_at: string
}

export interface Branch {
  id: number; restaurant_id: number; name: string
  location: string | null; is_active: boolean; created_at: string
}

export interface Device {
  id: number; branch_id: number; name: string; display_number: number
  mac_address: string; screen_size_inch: number | null
  resolution_width: number | null; resolution_height: number | null
  status: DeviceStatus; theme_id: number; active_session: SessionPeriod
  last_seen: string | null; registered_at: string
}

export interface MenuItem {
  id: number; sub_group_id: number; name: string; name_local: string | null
  description: string | null; price: number; image_url: string | null
  status: ItemStatus; is_veg: boolean; sequence: number
  session: SessionPeriod; created_at: string; updated_at: string
}

export interface MenuItemCreate {
  name: string; name_local?: string | null; description?: string | null
  price: number; image_url?: string | null; status?: ItemStatus
  is_veg?: boolean; sequence?: number; session?: SessionPeriod
}

export interface MenuItemUpdate {
  name?: string; name_local?: string | null; description?: string | null
  price?: number; image_url?: string | null; status?: ItemStatus
  is_veg?: boolean; sequence?: number; session?: SessionPeriod
}

export interface MenuSubGroup {
  id: number; group_id: number; name: string; name_local: string | null
  sequence: number; is_active: boolean; created_at: string
  items?: MenuItem[]
}

export interface MenuSubGroupUpdate {
  name?: string; name_local?: string | null; sequence?: number; is_active?: boolean
}

export interface MenuGroup {
  id: number; restaurant_id: number; name: string; name_local: string | null
  instruction: string | null; sequence: number; is_active: boolean
  image_url: string | null; created_at: string
  sub_groups?: MenuSubGroup[]
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (username: string, password: string) =>
    api.post<{ access_token: string; refresh_token: string; user: User }>('/auth/login', { username, password }),
  me: () => api.get<User>('/auth/me'),
}

// ─── Restaurants ──────────────────────────────────────────────────────────────

export const restaurantsApi = {
  list: () => api.get<Restaurant[]>('/restaurants'),
  get: (id: number) => api.get<Restaurant>(`/restaurants/${id}`),
  create: (data: { name: string; slug?: string; logo_url?: string }) =>
    api.post<Restaurant>('/restaurants', data),
  update: (id: number, data: Partial<Restaurant>) =>
    api.patch<Restaurant>(`/restaurants/${id}`, data),
  branches: (id: number) => api.get<Branch[]>(`/restaurants/${id}/branches`),
  createBranch: (id: number, data: { name: string; location?: string }) =>
    api.post<Branch>(`/restaurants/${id}/branches`, data),
}

// ─── Menu Groups ──────────────────────────────────────────────────────────────

export const menuApi = {
  // Groups
  listGroups: (restaurantId: number) =>
    api.get<MenuGroup[]>(`/menu/restaurants/${restaurantId}/groups`),
  createGroup: (restaurantId: number, data: Partial<MenuGroup>) =>
    api.post<MenuGroup>(`/menu/restaurants/${restaurantId}/groups`, data),
  updateGroup: (id: number, data: Partial<MenuGroup>) =>
    api.patch<MenuGroup>(`/menu/groups/${id}`, data),
  deleteGroup: (id: number) => api.delete(`/menu/groups/${id}`),

  // Sub Groups
  listSubGroups: (groupId: number) =>
    api.get<MenuSubGroup[]>(`/menu/groups/${groupId}/subgroups`),
  createSubGroup: (groupId: number, data: Partial<MenuSubGroup>) =>
    api.post<MenuSubGroup>(`/menu/groups/${groupId}/subgroups`, data),
  updateSubGroup: (id: number, data: MenuSubGroupUpdate) =>
    api.patch<MenuSubGroup>(`/menu/subgroups/${id}`, data),
  deleteSubGroup: (id: number) => api.delete(`/menu/subgroups/${id}`),

  // Items
  listItems: (subGroupId: number) =>
    api.get<MenuItem[]>(`/menu/subgroups/${subGroupId}/items`),
  createItem: (subGroupId: number, data: MenuItemCreate) =>
    api.post<MenuItem>(`/menu/subgroups/${subGroupId}/items`, data),
  updateItem: (id: number, data: MenuItemUpdate) =>
    api.patch<MenuItem>(`/menu/items/${id}`, data),
  deleteItem: (id: number) => api.delete(`/menu/items/${id}`),

  // Full menu + publish
  fullMenu: (restaurantId: number) =>
    api.get<{ restaurant: Restaurant; groups: MenuGroup[]; published_at: string; published_by?: string }>(`/menu/restaurants/${restaurantId}/full`),
  publish: (restaurantId: number) =>
    api.post<{ message: string; restaurant_id: number }>(`/menu/restaurants/${restaurantId}/publish`),

  // Reordering
  reorderGroups: (ids: number[]) =>
    api.post<{ message: string }>('/menu/reorder/groups', { ids }),
  reorderSubGroups: (ids: number[]) =>
    api.post<{ message: string }>('/menu/reorder/subgroups', { ids }),
  reorderItems: (ids: number[]) =>
    api.post<{ message: string }>('/menu/reorder/items', { ids }),
}

// ─── Devices ──────────────────────────────────────────────────────────────────

export const devicesApi = {
  list: (branchId?: number) =>
    api.get<Device[]>('/devices', { params: branchId ? { branch_id: branchId } : {} }),
  get: (id: number) => api.get<Device>(`/devices/${id}`),
  create: (data: Partial<Device> & { name: string; display_number: number; branch_id: number; mac_address?: string }) =>
    api.post<Device>('/devices', data),
  update: (id: number, data: Partial<Device>) =>
    api.patch<Device>(`/devices/${id}`, data),
  delete: (id: number) => api.delete(`/devices/${id}`),
}

// ─── Users ────────────────────────────────────────────────────────────────────

export const usersApi = {
  list: () => api.get<User[]>('/users'),
  create: (data: Partial<User> & { password: string }) =>
    api.post<User>('/users', data),
  update: (id: number, data: Partial<User>) =>
    api.patch<User>(`/users/${id}`, data),
  deactivate: (id: number) => api.patch(`/users/${id}/deactivate`),
  resetPassword: (id: number, new_password: string) =>
    api.post(`/users/${id}/reset-password`, { new_password }),
}

// ─── Templates ────────────────────────────────────────────────────────────────

export interface TemplateItemIn {
  item_id: number
  duration_seconds: number
}

export interface TemplateSaveRequest {
  name: string
  name_local?: string | null
  items: TemplateItemIn[]
}

export interface TemplateItemOut {
  id: number
  template_id: number
  items_id: number
  duration_second: number
  menu_item: MenuItem
}

export interface MenuTemplate {
  id: number
  restaurant_id: number
  name: string
  name_local: string | null
  is_active: boolean
  items: TemplateItemOut[]
}

export const templatesApi = {
  list: (restaurantId: number) =>
    api.get<MenuTemplate[]>(`/templates/restaurant/${restaurantId}`),
  create: (restaurantId: number, data: TemplateSaveRequest) =>
    api.post<MenuTemplate>(`/templates/restaurant/${restaurantId}`, data),
  activate: (templateId: number) =>
    api.patch<MenuTemplate>(`/templates/${templateId}/activate`),
  delete: (templateId: number) =>
    api.delete(`/templates/${templateId}`),
}

