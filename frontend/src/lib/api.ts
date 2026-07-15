const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  current_branch_id?: number;
  current_branch_name?: string;
}

export interface Branch {
  id: number;
  name: string;
  code?: string;
  price_per_photo: number;
  commission_per_photo: number;
  commission_after_target_per_photo: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Customer {
  id: number;
  name: string;
  phone?: string;
  email?: string;
  qr_token: string;
  created_by_employee_id: number;
  created_at: string;
  updated_at: string;
}

export interface Photo {
  id: number;
  customer_id: number;
  uploaded_by_employee_id: number;
  file_name: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  created_at: string;
  url?: string;
}

export interface Sale {
  id: number;
  customer_id: number;
  employee_id: number;
  branch_id?: number;
  package_id?: number;
  package_name?: string;
  small_photo_count: number;
  large_photo_count: number;
  photo_count: number;
  price_per_photo: number;
  amount: number;
  payment_status: string;
  payment_method?: string;
  notes?: string;
  created_at: string;
  customer_name?: string;
  employee_name?: string;
  branch_name?: string;
  invoice_url?: string;
}

export interface SaleInvoiceQR {
  sale_id: number;
  invoice_url: string;
  qr_image_base64: string;
}

export interface PrintPackage {
  id: number;
  name: string;
  photo_count: number;
  price: number;
  is_active: boolean;
  created_by_id?: number;
  created_at: string;
  updated_at: string;
}

export interface PrintPrice {
  price_per_photo: number;
  currency: string;
  updated_at: string;
  branch_id?: number;
  branch_name?: string;
}

export interface HierarchyNode {
  id: number;
  name: string;
  role: string;
  children: HierarchyNode[];
  target_photos: number;
  photos_printed: number;
  progress_percent: number;
  target_met: boolean;
  total_commission: number;
  team_photos_printed: number;
  team_target_photos: number;
  team_progress_percent: number;
}

export interface HierarchyData {
  year: number;
  month: number;
  tree: HierarchyNode;
}

export interface EmployeeTarget {
  id?: number;
  employee_id: number;
  employee_name?: string;
  year: number;
  month: number;
  target_photos: number;
  photos_printed: number;
  progress_percent: number;
  target_met: boolean;
  base_commission: number;
  bonus_commission: number;
  total_commission: number;
  photos_at_base_rate: number;
  photos_at_bonus_rate: number;
}

export interface AttendanceRecord {
  id: number;
  employee_id: number;
  employee_name?: string;
  partner_employee_id?: number;
  partner_employee_name?: string;
  branch_id?: number;
  branch_name?: string;
  work_date: string;
  check_in_at: string;
  check_out_at?: string;
  total_minutes?: number;
  status: string;
}

export interface LeaderboardEntry {
  rank: number;
  employee_id?: number;
  employee_name: string;
  branch_name?: string;
  photos_printed: number;
  target_photos: number;
  progress_percent: number;
  total_commission: number;
}

export interface LeaderboardData {
  year: number;
  month: number;
  is_blurred: boolean;
  blur_starts_on: string;
  entries: LeaderboardEntry[];
}

export interface DashboardData {
  stats: {
    total_sales: number;
    total_revenue: number;
    total_photos_printed: number;
    total_customers: number;
    total_employees: number;
    total_managers: number;
    total_uploads: number;
    my_sales: number;
    my_revenue: number;
    my_photos_printed: number;
    my_uploads: number;
    team_sales: number;
    team_revenue: number;
    team_photos_printed: number;
    print_price_per_photo: number;
    my_commission: number;
    my_target_photos: number;
    my_target_progress: number;
  };
  recent_sales: Sale[];
  revenue_chart: { label: string; value: number }[];
  assigned_employees: User[];
  recent_customers: Customer[];
  employee_targets: EmployeeTarget[];
}

class ApiClient {
  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = headers["Content-Type"] || "application/json";
    }
    if (token) headers.Authorization = `Bearer ${token}`;

    const response = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (response.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      const detail = error.detail;
      const message = Array.isArray(detail)
        ? detail.map((e: { msg?: string }) => e.msg).join(", ")
        : typeof detail === "string"
          ? detail
          : "Request failed";
      throw new Error(message || "Request failed");
    }
    if (response.status === 204) return {} as T;
    const contentType = response.headers.get("content-type");
    if (contentType?.includes("application/json")) return response.json();
    return response as unknown as T;
  }

  login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string; branch_id?: number; branch_name?: string }>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }
    );
  }

  selectBranch(branchId: number) {
    return this.request<{ access_token: string; refresh_token: string; branch_id?: number; branch_name?: string }>(
      "/auth/select-branch",
      {
        method: "POST",
        body: JSON.stringify({ branch_id: branchId }),
      }
    );
  }

  getMyBranches() {
    return this.request<Branch[]>("/auth/my-branches");
  }

  me() {
    return this.request<User>("/auth/me");
  }

  logout() {
    return this.request<{ message: string }>("/auth/logout", { method: "POST" });
  }

  forgotPassword(email: string) {
    return this.request<{ message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  resetPassword(token: string, new_password: string) {
    return this.request<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password }),
    });
  }

  getDashboard() {
    return this.request<DashboardData>("/dashboard");
  }

  getUsers(params?: Record<string, string>) {
    const q = params ? `?${new URLSearchParams(params)}` : "";
    return this.request<Paginated<User>>(`/users${q}`);
  }

  createUser(data: Record<string, unknown>) {
    return this.request<User>("/users", { method: "POST", body: JSON.stringify(data) });
  }

  updateUser(id: number, data: { role: string }) {
    return this.request<User>(`/users/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  }

  deleteUser(id: number) {
    return this.request<{ message: string }>(`/users/${id}`, { method: "DELETE" });
  }

  getCustomers(params?: Record<string, string>) {
    const q = params ? `?${new URLSearchParams(params)}` : "";
    return this.request<Paginated<Customer>>(`/customers${q}`);
  }

  createCustomer(data: Record<string, unknown>) {
    return this.request<Customer>("/customers", { method: "POST", body: JSON.stringify(data) });
  }

  getCustomerQR(id: number) {
    return this.request<{ qr_image_base64: string; qr_url: string }>(`/customers/${id}/qr`);
  }

  getPhotos(params?: Record<string, string>) {
    const q = params ? `?${new URLSearchParams(params)}` : "";
    return this.request<Paginated<Photo>>(`/photos${q}`);
  }

  async uploadPhotos(customerId: number, files: File[], onProgress?: (p: number) => void) {
    const batchSize = 10;
    const uploaded: Photo[] = [];
    for (let start = 0; start < files.length; start += batchSize) {
      const batch = files.slice(start, start + batchSize);
      const result = await this.uploadPhotoBatch(customerId, batch, (batchProgress) => {
        const overall = ((start + (batchProgress / 100) * batch.length) / files.length) * 100;
        if (onProgress) onProgress(Math.round(overall));
      });
      uploaded.push(...result);
    }
    if (onProgress) onProgress(100);
    return uploaded;
  }

  private uploadPhotoBatch(customerId: number, files: File[], onProgress?: (p: number) => void) {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return new Promise<Photo[]>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_URL}/photos/upload?customer_id=${customerId}`);
      const token = this.getToken();
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText));
        else {
          const parsed = JSON.parse(xhr.responseText || "{}");
          reject(new Error(parsed.detail || "Upload failed"));
        }
      };
      xhr.onerror = () => reject(new Error("Upload failed"));
      xhr.send(form);
    });
  }

  getSales(params?: Record<string, string>) {
    const q = params ? `?${new URLSearchParams(params)}` : "";
    return this.request<Paginated<Sale>>(`/sales${q}`);
  }

  createSale(data: Record<string, unknown>) {
    return this.request<Sale>("/sales", { method: "POST", body: JSON.stringify(data) });
  }

  getSaleInvoiceQR(id: number) {
    return this.request<SaleInvoiceQR>(`/sales/${id}/invoice-qr`);
  }

  getPackages(includeInactive = false) {
    const q = includeInactive ? "?include_inactive=true" : "";
    return this.request<PrintPackage[]>(`/packages${q}`);
  }

  createPackage(data: { name: string; photo_count: number; price: number; is_active?: boolean }) {
    return this.request<PrintPackage>("/packages", { method: "POST", body: JSON.stringify(data) });
  }

  updatePackage(id: number, data: Partial<{ name: string; photo_count: number; price: number; is_active: boolean }>) {
    return this.request<PrintPackage>(`/packages/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  }

  deletePackage(id: number) {
    return this.request<{ message: string }>(`/packages/${id}`, { method: "DELETE" });
  }

  updateSale(id: number, data: Record<string, unknown>) {
    return this.request<Sale>(`/sales/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  }

  search(q: string, type?: string) {
    const params = new URLSearchParams({ q });
    if (type) params.set("type", type);
    return this.request<{ type: string; id: number; title: string; subtitle?: string }[]>(
      `/search?${params}`
    );
  }

  getAssignments() {
    return this.request<
      { id: number; manager_id: number; employee_id: number; manager_name?: string; employee_name?: string }[]
    >("/assignments");
  }

  createAssignment(manager_id: number, employee_id: number) {
    return this.request("/assignments", {
      method: "POST",
      body: JSON.stringify({ manager_id, employee_id }),
    });
  }

  updateAssignment(id: number, data: { manager_id?: number; employee_id?: number }) {
    return this.request(`/assignments/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  deleteAssignment(id: number) {
    return this.request(`/assignments/${id}`, { method: "DELETE" });
  }

  getPortal(token: string) {
    return fetch(`${API_URL}/portal/${token}`).then((r) => {
      if (!r.ok) throw new Error("Invalid link");
      return r.json();
    });
  }

  getReport(type: string, format: string) {
    const token = this.getToken();
    return fetch(`${API_URL}/reports/${type}?format=${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  }

  getPrintPrice() {
    return this.request<PrintPrice>("/settings/print-price");
  }

  updatePrintPrice(price_per_photo: number) {
    return this.request<PrintPrice>("/settings/print-price", {
      method: "PATCH",
      body: JSON.stringify({ price_per_photo }),
    });
  }

  getTargets(year?: number, month?: number) {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    if (month) params.set("month", String(month));
    const q = params.toString() ? `?${params}` : "";
    return this.request<EmployeeTarget[]>(`/targets${q}`);
  }

  setEmployeeTarget(data: { employee_id: number; year: number; month: number; target_photos: number }) {
    return this.request<EmployeeTarget>("/targets", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  getMyCommission(year?: number, month?: number) {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    if (month) params.set("month", String(month));
    const q = params.toString() ? `?${params}` : "";
    return this.request<EmployeeTarget>(`/targets/commission/me${q}`);
  }

  getHierarchy(year?: number, month?: number) {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    if (month) params.set("month", String(month));
    const q = params.toString() ? `?${params}` : "";
    return this.request<HierarchyData>(`/hierarchy${q}`);
  }

  getLeaderboard(year?: number, month?: number) {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    if (month) params.set("month", String(month));
    const q = params.toString() ? `?${params}` : "";
    return this.request<LeaderboardData>(`/leaderboard${q}`);
  }

  getMyAttendanceToday() {
    return this.request<AttendanceRecord | null>("/attendance/me/today");
  }

  checkIn() {
    return this.request<AttendanceRecord>("/attendance/check-in", { method: "POST" });
  }

  checkOut(partnerEmployeeId?: number) {
    return this.request<AttendanceRecord>("/attendance/check-out", {
      method: "POST",
      body: JSON.stringify({ partner_employee_id: partnerEmployeeId || null }),
    });
  }

  getAttendancePartners() {
    return this.request<User[]>("/attendance/partners");
  }

  getAttendance(params?: Record<string, string>) {
    const q = params ? `?${new URLSearchParams(params)}` : "";
    return this.request<AttendanceRecord[]>(`/attendance${q}`);
  }

  getAttendanceSheet(format: string, params?: Record<string, string>) {
    const token = this.getToken();
    const search = new URLSearchParams({ format, ...(params || {}) });
    return fetch(`${API_URL}/attendance/sheet?${search}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  }

  getBranches() {
    return this.request<Branch[]>("/branches");
  }

  createBranch(data: {
    name: string;
    code?: string;
    price_per_photo: number;
    commission_per_photo: number;
    commission_after_target_per_photo: number;
    is_active?: boolean;
  }) {
    return this.request<Branch>("/branches", { method: "POST", body: JSON.stringify(data) });
  }

  updateBranch(
    id: number,
    data: Partial<{
      name: string;
      code: string;
      price_per_photo: number;
      commission_per_photo: number;
      commission_after_target_per_photo: number;
      is_active: boolean;
    }>
  ) {
    return this.request<Branch>(`/branches/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  }

  deleteBranch(id: number) {
    return this.request(`/branches/${id}`, { method: "DELETE" });
  }

  getBranchEmployees(branchId: number) {
    return this.request<number[]>(`/branches/${branchId}/employees`);
  }

  setBranchEmployees(branchId: number, employeeIds: number[]) {
    return this.request(`/branches/${branchId}/employees`, {
      method: "PUT",
      body: JSON.stringify({ employee_ids: employeeIds }),
    });
  }
}

export const api = new ApiClient();
