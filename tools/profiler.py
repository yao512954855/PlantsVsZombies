"""
性能剖析工具 - 实时监控系统性能

提供 FPS、CPU、内存使用率的实时监控与瓶颈检测。
支持性能报告生成和热点分析。

使用方式:
    from tools.profiler import Profiler
    
    profiler = Profiler()
    profiler.start()
    
    # 游戏循环中
    with profiler.frame():
        # 游戏逻辑
        pass
    
    profiler.stop()
    profiler.generate_report("performance_report.json")
"""

from __future__ import annotations
import time
import statistics
import json
import psutil
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from contextlib import contextmanager
from collections import deque
import threading


@dataclass
class FrameMetrics:
    """单帧性能指标"""
    frame_number: int
    frame_time_ms: float
    fps: float
    cpu_percent: float
    memory_mb: float
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "frame_number": self.frame_number,
            "frame_time_ms": round(self.frame_time_ms, 3),
            "fps": round(self.fps, 2),
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_mb": round(self.memory_mb, 2),
            "timestamp": self.timestamp
        }


@dataclass
class PerformanceReport:
    """性能报告数据类"""
    total_frames: int
    duration_seconds: float
    avg_fps: float
    min_fps: float
    max_fps: float
    avg_frame_time_ms: float
    avg_cpu_percent: float
    avg_memory_mb: float
    fps_stability: float  # 标准差/平均值，越小越稳定
    frame_time_p95_ms: float  # 95% 分位数
    frame_time_p99_ms: float  # 99% 分位数
    slowest_frames: List[Dict[str, Any]]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_frames": self.total_frames,
            "duration_seconds": round(self.duration_seconds, 2),
            "avg_fps": round(self.avg_fps, 2),
            "min_fps": round(self.min_fps, 2),
            "max_fps": round(self.max_fps, 2),
            "avg_frame_time_ms": round(self.avg_frame_time_ms, 3),
            "avg_cpu_percent": round(self.avg_cpu_percent, 2),
            "avg_memory_mb": round(self.avg_memory_mb, 2),
            "fps_stability": round(self.fps_stability, 4),
            "frame_time_p95_ms": round(self.frame_time_p95_ms, 3),
            "frame_time_p99_ms": round(self.frame_time_p99_ms, 3),
            "slowest_frames": self.slowest_frames[:10],
            "recommendations": self.recommendations
        }


class Profiler:
    """性能剖析器
    
    单例模式，全局唯一实例。
    提供实时性能监控和报告生成功能。
    """
    
    _instance: Optional[Profiler] = None
    
    def __new__(cls) -> Profiler:
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """初始化剖析器"""
        if self._initialized:
            return
        
        self._running = False
        self._frame_count = 0
        self._start_time: Optional[float] = None
        self._metrics_history: deque[FrameMetrics] = deque(maxlen=3600)  # 保留 1 小时数据
        self._frame_times: deque[float] = deque(maxlen=60)  # 最近 60 帧用于 FPS 计算
        self._process = psutil.Process(os.getpid())
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[FrameMetrics], None]] = []
        
        self._initialized = True
    
    def start(self) -> None:
        """开始性能监控"""
        if self._running:
            return
        
        self._running = True
        self._frame_count = 0
        self._start_time = time.time()
        self._metrics_history.clear()
        self._frame_times.clear()
    
    def stop(self) -> None:
        """停止性能监控"""
        self._running = False
    
    @contextmanager
    def frame(self):
        """帧时间上下文管理器
        
        使用方式:
            with profiler.frame():
                # 游戏逻辑
                pass
        """
        frame_start = time.perf_counter()
        yield
        frame_end = time.perf_counter()
        
        if self._running:
            self._record_frame(frame_end - frame_start)
    
    def _record_frame(self, frame_time_seconds: float) -> None:
        """记录帧数据
        
        Args:
            frame_time_seconds: 帧耗时（秒）
        """
        with self._lock:
            self._frame_count += 1
            frame_time_ms = frame_time_seconds * 1000
            self._frame_times.append(frame_time_ms)
            
            # 计算 FPS
            if len(self._frame_times) >= 2:
                avg_frame_time = statistics.mean(self._frame_times)
                current_fps = 1000.0 / avg_frame_time if avg_frame_time > 0 else 0
            else:
                current_fps = 0
            
            # 获取系统指标
            try:
                cpu_percent = self._process.cpu_percent(interval=0)
                memory_info = self._process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
            except Exception:
                cpu_percent = 0
                memory_mb = 0
            
            # 创建指标对象
            metrics = FrameMetrics(
                frame_number=self._frame_count,
                frame_time_ms=frame_time_ms,
                fps=current_fps,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb
            )
            
            self._metrics_history.append(metrics)
            
            # 触发回调
            for callback in self._callbacks:
                try:
                    callback(metrics)
                except Exception as e:
                    print(f"Profiler callback error: {e}")
    
    def get_current_fps(self) -> float:
        """获取当前 FPS
        
        Returns:
            当前帧率
        """
        if len(self._frame_times) < 2:
            return 0.0
        
        avg_frame_time = statistics.mean(self._frame_times)
        return 1000.0 / avg_frame_time if avg_frame_time > 0 else 0.0
    
    def get_average_fps(self, window_frames: int = 30) -> float:
        """获取平均 FPS
        
        Args:
            window_frames: 采样窗口大小
            
        Returns:
            平均帧率
        """
        if len(self._frame_times) < 2:
            return 0.0
        
        window = list(self._frame_times)[-window_frames:]
        avg_frame_time = statistics.mean(window)
        return 1000.0 / avg_frame_time if avg_frame_time > 0 else 0.0
    
    def get_metrics_history(self) -> List[FrameMetrics]:
        """获取历史指标
        
        Returns:
            指标历史列表
        """
        return list(self._metrics_history)
    
    def register_callback(self, callback: Callable[[FrameMetrics], None]) -> None:
        """注册性能回调
        
        Args:
            callback: 回调函数，接收 FrameMetrics 参数
        """
        self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[FrameMetrics], None]) -> None:
        """注销性能回调
        
        Args:
            callback: 要移除的回调函数
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def generate_report(self, filepath: Optional[Path | str] = None) -> PerformanceReport:
        """生成性能报告
        
        Args:
            filepath: 可选的报告文件路径
            
        Returns:
            性能报告对象
        """
        if not self._metrics_history:
            return PerformanceReport(
                total_frames=0,
                duration_seconds=0,
                avg_fps=0,
                min_fps=0,
                max_fps=0,
                avg_frame_time_ms=0,
                avg_cpu_percent=0,
                avg_memory_mb=0,
                fps_stability=0,
                frame_time_p95_ms=0,
                frame_time_p99_ms=0,
                slowest_frames=[],
                recommendations=["No data collected"]
            )
        
        metrics_list = list(self._metrics_history)
        
        # 计算统计数据
        total_frames = len(metrics_list)
        duration = metrics_list[-1].timestamp - metrics_list[0].timestamp if total_frames > 1 else 0
        
        fps_values = [m.fps for m in metrics_list if m.fps > 0]
        frame_times = [m.frame_time_ms for m in metrics_list]
        cpu_values = [m.cpu_percent for m in metrics_list]
        memory_values = [m.memory_mb for m in metrics_list]
        
        avg_fps = statistics.mean(fps_values) if fps_values else 0
        min_fps = min(fps_values) if fps_values else 0
        max_fps = max(fps_values) if fps_values else 0
        
        avg_frame_time = statistics.mean(frame_times)
        avg_cpu = statistics.mean(cpu_values) if cpu_values else 0
        avg_memory = statistics.mean(memory_values) if memory_values else 0
        
        # FPS 稳定性（变异系数）
        fps_stdev = statistics.stdev(fps_values) if len(fps_values) > 1 else 0
        fps_stability = fps_stdev / avg_fps if avg_fps > 0 else 0
        
        # 百分位数
        sorted_times = sorted(frame_times)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)
        p95 = sorted_times[p95_idx] if p95_idx < len(sorted_times) else sorted_times[-1]
        p99 = sorted_times[p99_idx] if p99_idx < len(sorted_times) else sorted_times[-1]
        
        # 最慢的帧
        slowest = sorted(metrics_list, key=lambda m: m.frame_time_ms, reverse=True)[:10]
        slowest_frames = [m.to_dict() for m in slowest]
        
        # 生成建议
        recommendations = self._generate_recommendations(
            avg_fps, min_fps, fps_stability, avg_frame_time, p99, avg_cpu, avg_memory
        )
        
        report = PerformanceReport(
            total_frames=total_frames,
            duration_seconds=duration,
            avg_fps=avg_fps,
            min_fps=min_fps,
            max_fps=max_fps,
            avg_frame_time_ms=avg_frame_time,
            avg_cpu_percent=avg_cpu,
            avg_memory_mb=avg_memory,
            fps_stability=fps_stability,
            frame_time_p95_ms=p95,
            frame_time_p99_ms=p99,
            slowest_frames=slowest_frames,
            recommendations=recommendations
        )
        
        # 保存到文件
        if filepath:
            filepath = Path(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2)
        
        return report
    
    def _generate_recommendations(
        self,
        avg_fps: float,
        min_fps: float,
        fps_stability: float,
        avg_frame_time: float,
        p99_frame_time: float,
        avg_cpu: float,
        avg_memory: float
    ) -> List[str]:
        """生成优化建议
        
        Args:
            avg_fps: 平均 FPS
            min_fps: 最低 FPS
            fps_stability: FPS 稳定性
            avg_frame_time: 平均帧耗时
            p99_frame_time: P99 帧耗时
            avg_cpu: 平均 CPU 使用率
            avg_memory: 平均内存使用
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # FPS 相关建议
        if avg_fps < 30:
            recommendations.append("⚠️ 平均 FPS 低于 30，建议降低渲染质量或减少同屏物体数量")
        elif avg_fps < 60:
            recommendations.append("ℹ️ 平均 FPS 低于 60，可考虑优化渲染管线")
        
        if min_fps < 20:
            recommendations.append("⚠️ 存在严重卡顿（FPS < 20），检查是否有性能热点")
        
        if fps_stability > 0.3:
            recommendations.append("⚠️ FPS 波动较大，建议优化帧时间一致性")
        
        # 帧耗时建议
        if avg_frame_time > 33:  # > 30 FPS
            recommendations.append("ℹ️ 平均帧耗时较高，考虑减少每帧计算量")
        
        if p99_frame_time > 100:  # > 10 FPS
            recommendations.append("⚠️ P99 帧耗时过高，存在偶发卡顿，检查 GC 或资源加载")
        
        # CPU 建议
        if avg_cpu > 80:
            recommendations.append("⚠️ CPU 使用率持续高于 80%，考虑多线程优化")
        elif avg_cpu > 60:
            recommendations.append("ℹ️ CPU 使用率较高，可考虑异步处理非关键逻辑")
        
        # 内存建议
        if avg_memory > 500:
            recommendations.append("⚠️ 内存使用超过 500MB，检查内存泄漏或未释放资源")
        elif avg_memory > 200:
            recommendations.append("ℹ️ 内存使用适中，注意监控长期运行的内存增长")
        
        if not recommendations:
            recommendations.append("✅ 性能表现良好，无需优化")
        
        return recommendations
    
    def reset(self) -> None:
        """重置剖析器"""
        with self._lock:
            self._frame_count = 0
            self._start_time = None
            self._metrics_history.clear()
            self._frame_times.clear()


# 全局剖析器实例
GLOBAL_PROFILER = Profiler()


def get_profiler() -> Profiler:
    """获取全局剖析器实例
    
    Returns:
        全局 Profiler 实例
    """
    return GLOBAL_PROFILER


# 装饰器：自动记录函数执行时间
def profile_function(func: Callable) -> Callable:
    """函数性能剖析装饰器
    
    使用方式:
        @profile_function
        def slow_function():
            time.sleep(0.1)
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = get_profiler()
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        
        print(f"[Profile] {func.__name__}: {elapsed*1000:.3f}ms")
        return result
    
    return wrapper


# 模块导出
__all__ = [
    "FrameMetrics",
    "PerformanceReport",
    "Profiler",
    "GLOBAL_PROFILER",
    "get_profiler",
    "profile_function"
]
