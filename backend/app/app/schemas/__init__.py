from datetime import date, datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None


class UserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    role: str
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserRoleUpdate(BaseModel):
    role: str = Field(pattern="^(admin|manager|employee)$")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    current_branch_id: Optional[int] = None
    current_branch_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SelectBranchRequest(BaseModel):
    branch_id: int = Field(gt=0)


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class CustomerBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: Optional[str]
    email: Optional[str]
    qr_token: str
    created_by_employee_id: int
    created_at: datetime
    updated_at: datetime


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    uploaded_by_employee_id: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    created_at: datetime
    url: Optional[str] = None


class SaleBase(BaseModel):
    customer_id: int
    photo_count: Optional[int] = Field(None, gt=0)
    small_photo_count: int = Field(0, ge=0)
    large_photo_count: int = Field(0, ge=0)
    notes: Optional[str] = None


class SaleCreate(SaleBase):
    branch_id: Optional[int] = None


class SaleUpdate(BaseModel):
    customer_id: Optional[int] = None
    photo_count: Optional[int] = Field(None, gt=0)
    small_photo_count: Optional[int] = Field(None, ge=0)
    large_photo_count: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    employee_id: int
    branch_id: Optional[int] = None
    small_photo_count: int = 0
    large_photo_count: int = 0
    photo_count: int
    price_per_photo: float
    amount: float
    notes: Optional[str]
    created_at: datetime
    customer_name: Optional[str] = None
    employee_name: Optional[str] = None
    branch_name: Optional[str] = None
    invoice_url: Optional[str] = None


class SaleInvoiceQRResponse(BaseModel):
    sale_id: int
    invoice_url: str
    qr_image_base64: str


class BranchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    code: Optional[str] = Field(None, max_length=20)
    price_per_photo: float = Field(gt=0, default=120.0)
    commission_per_photo: float = Field(gt=0, default=6.0)
    commission_after_target_per_photo: float = Field(gt=0, default=12.0)
    is_active: bool = True


class BranchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    code: Optional[str] = Field(None, max_length=20)
    price_per_photo: Optional[float] = Field(None, gt=0)
    commission_per_photo: Optional[float] = Field(None, gt=0)
    commission_after_target_per_photo: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class BranchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: Optional[str] = None
    price_per_photo: float
    commission_per_photo: float
    commission_after_target_per_photo: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BranchEmployeesUpdate(BaseModel):
    employee_ids: list[int] = []


class PrintPriceResponse(BaseModel):
    price_per_photo: float
    currency: str = "EGP"
    updated_at: datetime
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None


class PrintPriceUpdate(BaseModel):
    price_per_photo: float = Field(gt=0)


class ManagerAssignmentCreate(BaseModel):
    manager_id: int
    employee_id: int


class ManagerAssignmentUpdate(BaseModel):
    manager_id: int | None = None
    employee_id: int | None = None


class ManagerAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    manager_id: int
    employee_id: int
    created_at: datetime
    manager_name: Optional[str] = None
    employee_name: Optional[str] = None


class DashboardStats(BaseModel):
    total_sales: int = 0
    total_revenue: float = 0
    total_photos_printed: int = 0
    total_customers: int = 0
    total_employees: int = 0
    total_managers: int = 0
    total_uploads: int = 0
    my_sales: int = 0
    my_revenue: float = 0
    my_photos_printed: float = 0
    my_uploads: int = 0
    team_sales: int = 0
    team_revenue: float = 0
    team_photos_printed: float = 0
    print_price_per_photo: float = 120.0
    my_commission: float = 0
    my_target_photos: int = 0
    my_target_progress: float = 0


class ChartDataPoint(BaseModel):
    label: str
    value: float


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_sales: List[SaleResponse] = []
    revenue_chart: List[ChartDataPoint] = []
    assigned_employees: List[UserResponse] = []
    recent_customers: List[CustomerResponse] = []
    employee_targets: List["EmployeeTargetResponse"] = []


class SearchResult(BaseModel):
    type: str
    id: int
    title: str
    subtitle: Optional[str] = None


class QRCodeResponse(BaseModel):
    customer_id: int
    qr_token: str
    qr_url: str
    qr_image_base64: str


class CustomerPortalResponse(BaseModel):
    customer: CustomerResponse
    photos: List[PhotoResponse]
    sales: List[SaleResponse]


class EmployeeTargetSet(BaseModel):
    employee_id: int
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)
    target_photos: int = Field(gt=0)


class EmployeeTargetResponse(BaseModel):
    id: Optional[int] = None
    employee_id: int
    employee_name: Optional[str] = None
    year: int
    month: int
    target_photos: int
    photos_printed: float = 0
    progress_percent: float = 0
    target_met: bool = False
    base_commission: float = 0
    bonus_commission: float = 0
    total_commission: float = 0
    photos_at_base_rate: float = 0
    photos_at_bonus_rate: float = 0


class HierarchyNode(BaseModel):
    id: int
    name: str
    role: str
    children: List["HierarchyNode"] = []
    target_photos: int = 0
    photos_printed: float = 0
    progress_percent: float = 0
    target_met: bool = False
    total_commission: float = 0
    team_photos_printed: float = 0
    team_target_photos: int = 0
    team_progress_percent: float = 0


class HierarchyResponse(BaseModel):
    year: int
    month: int
    tree: HierarchyNode


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_name: Optional[str] = None
    partner_employee_id: Optional[int] = None
    partner_employee_name: Optional[str] = None
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    work_date: date
    check_in_at: datetime
    check_out_at: Optional[datetime] = None
    total_minutes: Optional[int] = None
    status: str


class AttendanceCheckOutRequest(BaseModel):
    partner_employee_id: Optional[int] = None
