
import logging
import math
from typing import Union, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CalculationResult:
    result: Union[int, float]
    expression: str
    error: Optional[str] = None


class CalculatorTool:
    """
    科学计算器工具，支持复杂数学计算
    """
    
    name = "calculate"
    description = "执行数学计算，支持四则运算、函数等"
    
    SAFE_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "sqrt": math.sqrt,
        "pow": pow,
        "exp": math.exp,
        "log": math.log,
        "log10": math.log10,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "pi": math.pi,
        "e": math.e,
    }
    
    def __call__(
        self,
        expression: str,
        precision: int = 10,
    ) -&gt; CalculationResult:
        """
        执行计算
        
        Args:
            expression: 数学表达式字符串
            precision: 结果精度（小数位数）
            
        Returns:
            CalculationResult
        """
        logger.info(f"Calculating: {expression}")
        
        try:
            # 安全的表达式求值
            result = self._safe_eval(expression)
            result = round(result, precision)
            
            return CalculationResult(
                result=result,
                expression=expression,
            )
            
        except Exception as e:
            logger.error(f"Calculation error: {e}")
            return CalculationResult(
                result=0,
                expression=expression,
                error=str(e),
            )
    
    def _safe_eval(self, expression: str) -&gt; Union[int, float]:
        """安全的表达式求值"""
        # 限制可用的命名空间
        local_vars = {}
        global_vars = self.SAFE_FUNCTIONS.copy()
        
        # 检查表达式是否只包含允许的字符
        allowed_chars = set("0123456789.+-*/()%^, _abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        for char in expression:
            if char not in allowed_chars:
                raise ValueError(f"Invalid character: {char}")
        
        # 使用 eval 计算，但限制命名空间
        result = eval(expression, global_vars, local_vars)
        
        if not isinstance(result, (int, float)):
            raise ValueError("Expression must evaluate to a number")
        
        return result

