"""Pydantic schemas for all NetBox-style models. Used for request/response validation.
All models support: id, name (or specific name field), description, comments, tags (List[str]), custom_fields (Dict).
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra='allow')
    description: Optional[str] = ''
    comments: Optional[str] = ''
    tags: Optional[List[str]] = []
    custom_fields: Optional[Dict[str, Any]] = {}


class BaseUpdateSchema(BaseModel):
    model_config = ConfigDict(extra='allow')
    description: Optional[str] = None
    comments: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


# ============= ORGANIZATION =============
class RegionCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class RegionUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class SiteGroupCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class SiteGroupUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class SiteCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    status: str = 'active'  # planned, staging, active, decommissioning, retired
    region_id: Optional[str] = None
    group_id: Optional[str] = None
    tenant_id: Optional[str] = None
    facility: Optional[str] = ''
    asns: Optional[List[str]] = []
    time_zone: Optional[str] = ''
    physical_address: Optional[str] = ''
    shipping_address: Optional[str] = ''
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SiteUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    status: Optional[str] = None
    region_id: Optional[str] = None
    group_id: Optional[str] = None
    tenant_id: Optional[str] = None
    facility: Optional[str] = None
    asns: Optional[List[str]] = None
    time_zone: Optional[str] = None
    physical_address: Optional[str] = None
    shipping_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    site_id: str
    parent_id: Optional[str] = None
    status: str = 'active'
    tenant_id: Optional[str] = None
    facility: Optional[str] = ''


class LocationUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    site_id: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    tenant_id: Optional[str] = None
    facility: Optional[str] = None


class TenantGroupCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class TenantGroupUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class TenantCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    group_id: Optional[str] = None


class TenantUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    group_id: Optional[str] = None


class ContactGroupCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class ContactGroupUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class ContactRoleCreate(BaseSchema):
    name: str
    slug: Optional[str] = None


class ContactRoleUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None


class ContactCreate(BaseSchema):
    name: str
    group_id: Optional[str] = None
    title: Optional[str] = ''
    phone: Optional[str] = ''
    email: Optional[str] = ''
    address: Optional[str] = ''
    link: Optional[str] = ''


class ContactUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    group_id: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    link: Optional[str] = None


class ContactAssignmentCreate(BaseSchema):
    content_type: str  # e.g., 'site', 'device'
    object_id: str
    contact_id: str
    role_id: Optional[str] = None
    priority: Optional[str] = 'primary'


class ContactAssignmentUpdate(BaseUpdateSchema):
    content_type: Optional[str] = None
    object_id: Optional[str] = None
    contact_id: Optional[str] = None
    role_id: Optional[str] = None
    priority: Optional[str] = None


# ============= RACKS =============
class RackRoleCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    color: Optional[str] = '10b981'


class RackRoleUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    color: Optional[str] = None


class RackCreate(BaseSchema):
    name: str
    facility_id: Optional[str] = ''
    site_id: str
    location_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: str = 'active'
    role_id: Optional[str] = None
    serial: Optional[str] = ''
    asset_tag: Optional[str] = ''
    type: Optional[str] = '4-post-cabinet'  # 2-post-frame, 4-post-frame, 4-post-cabinet, wall-frame, wall-cabinet
    width: int = 19  # 10, 19, 21, 23 inches
    u_height: int = 42
    starting_unit: int = 1
    desc_units: bool = False  # numbering descending?
    outer_width: Optional[int] = None
    outer_depth: Optional[int] = None
    outer_unit: Optional[str] = 'mm'
    weight: Optional[float] = None
    max_weight: Optional[int] = None
    weight_unit: Optional[str] = 'kg'
    mounting_depth: Optional[int] = None
    form_factor: Optional[str] = None


class RackUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    facility_id: Optional[str] = None
    site_id: Optional[str] = None
    location_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[str] = None
    serial: Optional[str] = None
    asset_tag: Optional[str] = None
    type: Optional[str] = None
    width: Optional[int] = None
    u_height: Optional[int] = None
    starting_unit: Optional[int] = None
    desc_units: Optional[bool] = None
    outer_width: Optional[int] = None
    outer_depth: Optional[int] = None
    outer_unit: Optional[str] = None
    weight: Optional[float] = None
    max_weight: Optional[int] = None
    weight_unit: Optional[str] = None
    mounting_depth: Optional[int] = None
    form_factor: Optional[str] = None


class RackReservationCreate(BaseSchema):
    rack_id: str
    units: List[int]
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None


class RackReservationUpdate(BaseUpdateSchema):
    rack_id: Optional[str] = None
    units: Optional[List[int]] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
