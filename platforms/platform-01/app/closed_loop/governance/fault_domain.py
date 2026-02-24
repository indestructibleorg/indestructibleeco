"""
故障域与降级策略系统 (Fault Domain & Degradation)

强制治理规范核心组件
任何一段挂掉，系统如何保证不断尾（重试、隔离、fallback、停机保护）
"""

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable, Set
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class FaultDomain(Enum):
    """故障域层级"""
    GLOBAL = "global"          # 全局故障域
    ZONE = "zone"              # 区域故障域
    MODULE = "module"          # 模块故障域
    INSTANCE = "instance"      # 实例故障域


class ServiceStatus(Enum):
    """服务状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DOWN = "down"


class DegradationLevel(Enum):
    """降级级别"""
    NONE = "none"              # 无降级
    PARTIAL = "partial"        # 部分降级
    FULL = "full"              # 完全降级
    EMERGENCY = "emergency"    # 紧急模式


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"          # 关闭（正常）
    OPEN = "open"              # 打开（熔断）
    HALF_OPEN = "half_open"    # 半开（试探）


@dataclass
class HealthCheck:
    """健康检查"""
    service_name: str
    status: ServiceStatus
    last_check: datetime
    response_time_ms: float
    error_rate: float
    consecutive_failures: int = 0
    consecutive_successes: int = 0


@dataclass
class RetryPolicy:
    """重试策略"""
    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    retryable_exceptions: List[str] = field(default_factory=list)
    
    def get_delay(self, attempt: int) -> float:
        """获取第N次重试的延迟"""
        delay = self.initial_delay_seconds * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay_seconds)
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """判断是否应重试"""
        if attempt >= self.max_retries:
            return False
        
        exception_type = type(exception).__name__
        if self.retryable_exceptions and exception_type not in self.retryable_exceptions:
            return False
        
        return True


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 30
    half_open_max_calls: int = 3
    success_threshold: int = 2


class CircuitBreaker:
    """
    熔断器
    
    防止故障扩散
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行被熔断保护的函数
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
        
        Returns:
            函数返回值
        
        Raises:
            CircuitBreakerOpenError: 熔断器打开时
        """
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                # 检查是否可以进入半开状态
                if self._can_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker {self.name} entering half-open state")
                else:
                    raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker {self.name} half-open limit reached"
                    )
                self.half_open_calls += 1
        
        # 执行函数
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """成功回调"""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._reset()
                    logger.info(f"Circuit breaker {self.name} closed")
            else:
                self.failure_count = 0
    
    async def _on_failure(self):
        """失败回调"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker {self.name} opened from half-open")
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker {self.name} opened")
    
    def _can_attempt_reset(self) -> bool:
        """检查是否可以尝试重置"""
        if self.last_failure_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout_seconds
    
    def _reset(self):
        """重置熔断器"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
    
    def get_state(self) -> CircuitBreakerState:
        """获取当前状态"""
        return self.state


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""
    pass


class FaultIsolator:
    """
    故障隔离器
    
    隔离故障组件，防止影响扩散
    """
    
    def __init__(self):
        self._isolated_services: Set[str] = set()
        self._isolation_reasons: Dict[str, str] = {}
        self._isolation_time: Dict[str, datetime] = {}
    
    def isolate(self, service_name: str, reason: str):
        """隔离服务"""
        self._isolated_services.add(service_name)
        self._isolation_reasons[service_name] = reason
        self._isolation_time[service_name] = datetime.now()
        
        logger.warning(f"Service {service_name} isolated: {reason}")
    
    def unisolate(self, service_name: str):
        """解除隔离"""
        self._isolated_services.discard(service_name)
        self._isolation_reasons.pop(service_name, None)
        self._isolation_time.pop(service_name, None)
        
        logger.info(f"Service {service_name} unisolated")
    
    def is_isolated(self, service_name: str) -> bool:
        """检查服务是否被隔离"""
        return service_name in self._isolated_services
    
    def get_isolated_services(self) -> List[str]:
        """获取被隔离的服务列表"""
        return list(self._isolated_services)
    
    def get_isolation_info(self, service_name: str) -> Optional[Dict]:
        """获取隔离信息"""
        if service_name not in self._isolated_services:
            return None
        
        return {
            "service": service_name,
            "reason": self._isolation_reasons.get(service_name),
            "isolated_at": self._isolation_time.get(service_name).isoformat() if service_name in self._isolation_time else None
        }


class GracefulDegradation:
    """
    优雅降级
    
    在资源不足时降低服务质量，保证核心功能可用
    """
    
    def __init__(self):
        self._degradation_level = DegradationLevel.NONE
        self._disabled_features: Set[str] = set()
        self._reduced_limits: Dict[str, float] = {}
    
    def set_level(self, level: DegradationLevel):
        """设置降级级别"""
        old_level = self._degradation_level
        self._degradation_level = level
        
        # 根据级别调整功能
        if level == DegradationLevel.PARTIAL:
            self._disabled_features = {"non_critical_alerts", "detailed_metrics"}
            self._reduced_limits = {"max_concurrent_actions": 3}
        elif level == DegradationLevel.FULL:
            self._disabled_features = {"non_critical_alerts", "detailed_metrics", "advanced_analytics"}
            self._reduced_limits = {"max_concurrent_actions": 1}
        elif level == DegradationLevel.EMERGENCY:
            self._disabled_features = {"all_non_critical"}
            self._reduced_limits = {"max_concurrent_actions": 0}
        else:
            self._disabled_features = set()
            self._reduced_limits = {}
        
        logger.warning(f"Degradation level changed: {old_level.value} -> {level.value}")
    
    def get_level(self) -> DegradationLevel:
        """获取当前降级级别"""
        return self._degradation_level
    
    def is_feature_enabled(self, feature: str) -> bool:
        """检查功能是否启用"""
        return feature not in self._disabled_features
    
    def get_limit(self, resource: str, default: float = float('inf')) -> float:
        """获取资源限制"""
        return self._reduced_limits.get(resource, default)


class KillSwitch:
    """
    停机保护（Kill Switch）
    
    紧急情况下停止自动修复，防止二次伤害
    """
    
    def __init__(self):
        self._enabled = False
        self._triggered_at: Optional[datetime] = None
        self._trigger_reason: Optional[str] = None
        self._trigger_metrics: Dict[str, Any] = {}
        
        # 触发条件配置
        self._triggers: List[Dict[str, Any]] = [
            {"metric": "error_rate", "threshold": 0.5, "duration_seconds": 120},
            {"metric": "system_availability", "threshold": 0.5, "duration_seconds": 60},
        ]
    
    def check_triggers(self, metrics: Dict[str, float]) -> bool:
        """
        检查是否触发停机保护
        
        Args:
            metrics: 当前指标值
        
        Returns:
            是否触发
        """
        for trigger in self._triggers:
            metric_name = trigger["metric"]
            threshold = trigger["threshold"]
            
            if metric_name in metrics:
                value = metrics[metric_name]
                
                # 简单的阈值比较
                if metric_name == "error_rate":
                    if value > threshold:
                        return True
                elif metric_name == "system_availability":
                    if value < threshold:
                        return True
        
        return False
    
    def trigger(self, reason: str, metrics: Dict[str, Any]):
        """触发停机保护"""
        self._enabled = True
        self._triggered_at = datetime.now()
        self._trigger_reason = reason
        self._trigger_metrics = metrics
        
        logger.critical(f"KILL SWITCH TRIGGERED: {reason}")
    
    def reset(self):
        """重置停机保护"""
        self._enabled = False
        self._triggered_at = None
        self._trigger_reason = None
        self._trigger_metrics = {}
        
        logger.info("Kill switch reset")
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "enabled": self._enabled,
            "triggered_at": self._triggered_at.isoformat() if self._triggered_at else None,
            "trigger_reason": self._trigger_reason,
            "trigger_metrics": self._trigger_metrics
        }


class FaultDomainManager:
    """
    故障域管理器
    
    管理不同层级的故障域和降级策略
    """
    
    def __init__(self):
        # 健康状态
        self._health_status: Dict[str, HealthCheck] = {}
        
        # 熔断器
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # 故障隔离
        self._fault_isolator = FaultIsolator()
        
        # 优雅降级
        self._degradation = GracefulDegradation()
        
        # 停机保护
        self._kill_switch = KillSwitch()
        
        # 降级策略
        self._fallbacks: Dict[str, Callable] = {}
    
    def register_service(
        self,
        service_name: str,
        fault_domain: FaultDomain,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        """注册服务"""
        # 创建熔断器
        if circuit_breaker_config:
            self._circuit_breakers[service_name] = CircuitBreaker(
                service_name,
                circuit_breaker_config
            )
        
        logger.info(f"Service {service_name} registered in {fault_domain.value} domain")
    
    def register_fallback(self, service_name: str, fallback: Callable):
        """注册降级方案"""
        self._fallbacks[service_name] = fallback
    
    async def execute_with_resilience(
        self,
        service_name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        带弹性保护的执行
        
        执行流程:
        1. 检查停机保护
        2. 检查服务隔离
        3. 检查降级级别
        4. 使用熔断器执行
        5. 失败时尝试降级方案
        """
        # 1. 检查停机保护
        if self._kill_switch.is_enabled():
            raise KillSwitchEnabledError("Kill switch is enabled")
        
        # 2. 检查服务隔离
        if self._fault_isolator.is_isolated(service_name):
            raise ServiceIsolatedError(f"Service {service_name} is isolated")
        
        # 3. 检查降级级别
        if not self._degradation.is_feature_enabled(service_name):
            logger.warning(f"Service {service_name} disabled due to degradation")
            return None
        
        # 4. 使用熔断器执行
        circuit_breaker = self._circuit_breakers.get(service_name)
        
        if circuit_breaker:
            try:
                return await circuit_breaker.call(func, *args, **kwargs)
            except CircuitBreakerOpenError:
                # 熔断器打开，尝试降级方案
                return await self._try_fallback(service_name, *args, **kwargs)
        else:
            # 无熔断器，直接执行
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 失败时尝试降级方案
                return await self._try_fallback(service_name, *args, **kwargs)
    
    async def _try_fallback(self, service_name: str, *args, **kwargs) -> Any:
        """尝试降级方案"""
        fallback = self._fallbacks.get(service_name)
        
        if fallback:
            logger.info(f"Using fallback for {service_name}")
            return await fallback(*args, **kwargs)
        
        logger.warning(f"No fallback available for {service_name}")
        return None
    
    def update_health(
        self,
        service_name: str,
        status: ServiceStatus,
        response_time_ms: float,
        error_rate: float
    ):
        """更新健康状态"""
        health = self._health_status.get(service_name)
        
        if health:
            # 更新现有记录
            health.status = status
            health.last_check = datetime.now()
            health.response_time_ms = response_time_ms
            health.error_rate = error_rate
            
            if status in [ServiceStatus.UNHEALTHY, ServiceStatus.DOWN]:
                health.consecutive_failures += 1
                health.consecutive_successes = 0
            else:
                health.consecutive_successes += 1
                health.consecutive_failures = 0
        else:
            # 创建新记录
            self._health_status[service_name] = HealthCheck(
                service_name=service_name,
                status=status,
                last_check=datetime.now(),
                response_time_ms=response_time_ms,
                error_rate=error_rate
            )
        
        # 检查是否需要隔离
        if health and health.consecutive_failures >= 5:
            self._fault_isolator.isolate(
                service_name,
                f"Consecutive failures: {health.consecutive_failures}"
            )
    
    def get_health_status(self, service_name: str) -> Optional[HealthCheck]:
        """获取健康状态"""
        return self._health_status.get(service_name)
    
    def get_all_health_status(self) -> Dict[str, HealthCheck]:
        """获取所有健康状态"""
        return self._health_status.copy()
    
    def set_degradation_level(self, level: DegradationLevel):
        """设置降级级别"""
        self._degradation.set_level(level)
    
    def trigger_kill_switch(self, reason: str, metrics: Dict[str, Any]):
        """触发停机保护"""
        self._kill_switch.trigger(reason, metrics)
    
    def reset_kill_switch(self):
        """重置停机保护"""
        self._kill_switch.reset()
    
    def get_status(self) -> Dict[str, Any]:
        """获取整体状态"""
        return {
            "kill_switch": self._kill_switch.get_status(),
            "degradation_level": self._degradation.get_level().value,
            "isolated_services": self._fault_isolator.get_isolated_services(),
            "circuit_breakers": {
                name: cb.get_state().value
                for name, cb in self._circuit_breakers.items()
            },
            "health_summary": {
                "healthy": sum(1 for h in self._health_status.values() if h.status == ServiceStatus.HEALTHY),
                "degraded": sum(1 for h in self._health_status.values() if h.status == ServiceStatus.DEGRADED),
                "unhealthy": sum(1 for h in self._health_status.values() if h.status == ServiceStatus.UNHEALTHY),
                "down": sum(1 for h in self._health_status.values() if h.status == ServiceStatus.DOWN),
            }
        }


class KillSwitchEnabledError(Exception):
    """停机保护启用异常"""
    pass


class ServiceIsolatedError(Exception):
    """服务隔离异常"""
    pass


class RetryExecutor:
    """
    重试执行器
    
    带重试逻辑的执行器
    """
    
    def __init__(self, policy: RetryPolicy):
        self.policy = policy
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        带重试的执行
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
        
        Returns:
            函数返回值
        
        Raises:
            最后一次异常
        """
        last_exception = None
        
        for attempt in range(self.policy.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.policy.max_retries:
                    if self.policy.should_retry(e, attempt):
                        delay = self.policy.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.warning(f"Exception not retryable: {e}")
                        raise
                else:
                    logger.error(f"All {self.policy.max_retries + 1} attempts failed")
        
        if last_exception is not None:
            raise last_exception
        raise RuntimeError("RetryExecutor: execution failed but no exception was captured")
