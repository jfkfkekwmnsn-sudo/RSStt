from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import re

from app.models.rule import Rule
from app.models.article import Article, ArticleStatus
from app.models.source import Source
from app.schemas.rule import RuleCondition, RuleAction, ConditionOperator, ActionType
import structlog

logger = structlog.get_logger()


class RulesService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def apply_rules(self, article: Article) -> List[Dict[str, Any]]:
        """Apply all active rules to an article"""
        # Get active rules ordered by priority
        query = select(Rule).where(
            Rule.is_active == True
        ).order_by(Rule.priority)
        
        result = await self.db.execute(query)
        rules = result.scalars().all()
        
        applied_actions = []
        
        for rule in rules:
            if await self._check_conditions(article, rule.conditions):
                # Apply actions
                actions = await self._apply_actions(article, rule.actions)
                applied_actions.extend(actions)
                
                # Update rule stats
                rule.times_matched += 1
                rule.last_matched_at = datetime.now()
                
                logger.info(
                    "Rule matched",
                    rule_id=str(rule.id),
                    rule_name=rule.name,
                    article_id=str(article.id),
                    actions=actions
                )
                
                # Check if any action stops further processing
                if any(a.get("stops_processing") for a in actions):
                    break
        
        return applied_actions
    
    async def _check_conditions(self, article: Article, conditions: Dict) -> bool:
        """Check if all conditions match"""
        condition_list = conditions.get("conditions", [])
        match_type = conditions.get("match", "all")  # all or any
        
        if not condition_list:
            return True
        
        results = []
        for cond_data in condition_list:
            cond = RuleCondition(**cond_data)
            matches = await self._check_single_condition(article, cond)
            results.append(matches)
        
        if match_type == "all":
            return all(results)
        else:
            return any(results)
    
    async def _check_single_condition(self, article: Article, condition: RuleCondition) -> bool:
        """Check single condition against article"""
        field = condition.field
        operator = condition.operator
        value = condition.value
        
        # Get field value from article
        article_value = await self._get_field_value(article, field)
        
        # Apply operator
        if operator == ConditionOperator.EQUALS:
            return article_value == value
        
        elif operator == ConditionOperator.NOT_EQUALS:
            return article_value != value
        
        elif operator == ConditionOperator.GREATER_THAN:
            return article_value is not None and article_value > value
        
        elif operator == ConditionOperator.GREATER_EQUAL:
            return article_value is not None and article_value >= value
        
        elif operator == ConditionOperator.LESS_THAN:
            return article_value is not None and article_value < value
        
        elif operator == ConditionOperator.LESS_EQUAL:
            return article_value is not None and article_value <= value
        
        elif operator == ConditionOperator.IN:
            return article_value in value if isinstance(value, list) else False
        
        elif operator == ConditionOperator.NOT_IN:
            return article_value not in value if isinstance(value, list) else True
        
        elif operator == ConditionOperator.CONTAINS:
            if isinstance(article_value, str):
                return value.lower() in article_value.lower()
            elif isinstance(article_value, list):
                return value in article_value
            return False
        
        elif operator == ConditionOperator.NOT_CONTAINS:
            if isinstance(article_value, str):
                return value.lower() not in article_value.lower()
            elif isinstance(article_value, list):
                return value not in article_value
            return True
        
        elif operator == ConditionOperator.REGEX:
            if isinstance(article_value, str):
                return bool(re.search(value, article_value, re.IGNORECASE))
            return False
        
        elif operator == ConditionOperator.EXISTS:
            return article_value is not None and article_value != ""
        
        return False
    
    async def _get_field_value(self, article: Article, field: str) -> Any:
        """Get field value from article"""
        # Direct article fields
        direct_fields = {
            "quality": article.quality_score,
            "quality_score": article.quality_score,
            "priority": article.priority_score,
            "priority_score": article.priority_score,
            "category": article.category,
            "title": article.title,
            "content": article.content_clean,
            "description": article.description,
            "tags": article.tags or [],
            "has_image": bool(article.main_image_url),
            "source_id": str(article.source_id) if article.source_id else None,
            "status": article.status.value,
            "ai_used": article.ai_used,
        }
        
        if field in direct_fields:
            return direct_fields[field]
        
        # Source fields
        if field.startswith("source.") and article.source_id:
            source_field = field.replace("source.", "")
            query = select(Source).where(Source.id == article.source_id)
            result = await self.db.execute(query)
            source = result.scalar_one_or_none()
            
            if source:
                source_fields = {
                    "name": source.name,
                    "type": source.type.value,
                    "is_trusted": source.is_trusted,
                    "reputation": source.reputation_score,
                }
                return source_fields.get(source_field)
        
        # Text length
        if field == "text_length":
            return len(article.content_clean or "")
        
        return None
    
    async def _apply_actions(self, article: Article, actions: Dict) -> List[Dict[str, Any]]:
        """Apply rule actions to article"""
        action_list = actions.get("actions", [])
        applied = []
        
        for action_data in action_list:
            action = RuleAction(**action_data)
            result = await self._apply_single_action(article, action)
            if result:
                applied.append(result)
        
        return applied
    
    async def _apply_single_action(self, article: Article, action: RuleAction) -> Optional[Dict[str, Any]]:
        """Apply single action"""
        if action.action == ActionType.AUTO_APPROVE:
            article.status = ArticleStatus.APPROVED
            article.moderated_at = datetime.now()
            return {"action": "auto_approve", "stops_processing": True}
        
        elif action.action == ActionType.AUTO_REJECT:
            article.status = ArticleStatus.REJECTED
            article.moderated_at = datetime.now()
            article.rejection_reason = f"Auto-rejected by rule"
            return {"action": "auto_reject", "stops_processing": True}
        
        elif action.action == ActionType.SET_PRIORITY:
            article.priority_score = int(action.value)
            return {"action": "set_priority", "value": action.value}
        
        elif action.action == ActionType.SET_CATEGORY:
            article.category = action.value
            return {"action": "set_category", "value": action.value}
        
        elif action.action == ActionType.ADD_TAGS:
            tags = article.tags or []
            new_tags = action.value if isinstance(action.value, list) else [action.value]
            article.tags = list(set(tags + new_tags))
            return {"action": "add_tags", "value": new_tags}
        
        elif action.action == ActionType.REMOVE_TAGS:
            tags = article.tags or []
            remove_tags = action.value if isinstance(action.value, list) else [action.value]
            article.tags = [t for t in tags if t not in remove_tags]
            return {"action": "remove_tags", "value": remove_tags}
        
        elif action.action == ActionType.REQUIRE_REVIEW:
            article.status = ArticleStatus.NEEDS_REVIEW
            return {"action": "require_review"}
        
        elif action.action == ActionType.AI_REWRITE:
            # Queue AI rewrite task
            from app.workers.tasks import ai_rewrite_task
            ai_rewrite_task.delay(str(article.id))
            return {"action": "ai_rewrite", "queued": True}
        
        return None
    
    async def dry_run(self, rule_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
        """Test rule against recent articles without applying"""
        query = select(Rule).where(Rule.id == rule_id)
        result = await self.db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            return []
        
        # Get recent articles
        articles_query = select(Article).order_by(
            Article.created_at.desc()
        ).limit(limit)
        
        articles_result = await self.db.execute(articles_query)
        articles = articles_result.scalars().all()
        
        results = []
        for article in articles:
            matches = await self._check_conditions(article, rule.conditions)
            results.append({
                "article_id": str(article.id),
                "article_title": article.title,
                "matched": matches,
                "actions_would_apply": rule.actions.get("actions", []) if matches else []
            })
        
        return results
