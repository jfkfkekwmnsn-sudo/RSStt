from typing import Optional, List, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum


class ConditionOperator(str, Enum):
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"
    EXISTS = "exists"


class RuleCondition(BaseModel):
    field: str  # quality, category, source_id, has_image, title, content, tags, etc.
    operator: ConditionOperator
    value: Any


class ActionType(str, Enum):
    AUTO_APPROVE = "auto_approve"
    AUTO_REJECT = "auto_reject"
    SET_PRIORITY = "set_priority"
    SET_CATEGORY = "set_category"
    ADD_TAGS = "add_tags"
    REMOVE_TAGS = "remove_tags"
    ROUTE_TO_TARGET = "route_to_target"
    REQUIRE_REVIEW = "require_review"
    APPLY_TEMPLATE = "apply_template"
    AI_REWRITE = "ai_rewrite"


class RuleAction(BaseModel):
    action: ActionType
    value: Optional[Any] = None


class RuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    priority: int = Field(100, ge=1, le=1000)
    conditions: List[RuleCondition] = Field(..., min_items=1)
    actions: List[RuleAction] = Field(..., min_items=1)


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=1000)
    conditions: Optional[List[RuleCondition]] = None
    actions: Optional[List[RuleAction]] = None


class RuleResponse(RuleBase):
    id: UUID
    project_id: Optional[UUID] = None
    version: int
    times_matched: int
    last_matched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RuleDryRunRequest(BaseModel):
    limit: int = Field(10, ge=1, le=100)


class RuleDryRunResult(BaseModel):
    article_id: UUID
    article_title: str
    matched: bool
    actions_would_apply: List[RuleAction] = []


class RuleDryRunResponse(BaseModel):
    rule_id: UUID
    rule_name: str
    total_tested: int
    matched_count: int
    results: List[RuleDryRunResult]