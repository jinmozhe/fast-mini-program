"""
国际化(i18n)工具模块

提供多语言支持和本地化功能，支持按模块懒加载语言资源。
"""
import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fastapi import Request
from starlette.datastructures import Headers

from app.core.config import settings

logger = logging.getLogger(__name__)


class I18nManager:
    """
    国际化资源管理器
    
    负责加载和管理多语言资源，提供文本获取和参数替换功能。
    支持模块化资源组织和懒加载机制。
    """
    
    def __init__(self, locale_dir: Union[str, Path], default_locale: str = "zh"):
        """
        初始化国际化管理器
        
        Args:
            locale_dir: 语言资源目录路径
            default_locale: 默认语言代码，如未找到指定语言时使用
        """
        self.locale_dir = Path(locale_dir)
        self.default_locale = default_locale
        self.supported_locales = self._discover_supported_locales()
        self._resources: Dict[str, Dict[str, Any]] = {}
        self._loaded_modules: Dict[str, Set[str]] = {}
        
        logger.info(
            f"I18n管理器初始化, 支持的语言: {', '.join(self.supported_locales)}, "
            f"默认语言: {self.default_locale}"
        )
    
    def _discover_supported_locales(self) -> List[str]:
        """发现系统支持的所有语言代码"""
        if not self.locale_dir.exists():
            logger.warning(f"语言资源目录不存在: {self.locale_dir}")
            return [self.default_locale]
        
        return [
            d.name for d in self.locale_dir.iterdir() 
            if d.is_dir() and not d.name.startswith("_")
        ]
    
    def _ensure_locale(self, locale: str) -> str:
        """确保语言代码有效，如无效则返回默认语言"""
        if locale in self.supported_locales:
            return locale
        
        # 尝试匹配语言主要部分 (例如: zh-CN -> zh)
        locale_main = locale.split("-")[0]
        if locale_main in self.supported_locales:
            return locale_main
            
        logger.warning(f"不支持的语言: {locale}, 使用默认语言: {self.default_locale}")
        return self.default_locale
    
    @lru_cache(maxsize=128)
    def _get_resource_path(self, locale: str, module: str, resource_type: str) -> Optional[Path]:
        """获取指定资源文件的路径"""
        locale = self._ensure_locale(locale)
        resource_path = self.locale_dir / locale / module / f"{resource_type}.json"
        
        if not resource_path.exists():
            logger.debug(f"资源文件不存在: {resource_path}")
            return None
            
        return resource_path
    
    def _load_resource(self, locale: str, module: str, resource_type: str) -> Dict[str, Any]:
        """
        加载单个资源文件
        
        如果主要语言资源不存在，会尝试加载默认语言资源
        """
        resource_path = self._get_resource_path(locale, module, resource_type)
        
        # 如果找不到请求的语言资源，尝试使用默认语言
        if resource_path is None and locale != self.default_locale:
            logger.debug(
                f"未找到资源文件 {module}/{resource_type}.json (语言: {locale}), "
                f"尝试使用默认语言: {self.default_locale}"
            )
            resource_path = self._get_resource_path(self.default_locale, module, resource_type)
        
        # 如果仍然找不到，返回空字典
        if resource_path is None:
            logger.warning(
                f"资源文件不存在: {module}/{resource_type}.json "
                f"(语言: {locale} 和默认语言)"
            )
            return {}
        
        try:
            with open(resource_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                
            # 移除元数据节点
            content.pop("metadata", None)
            return content
        except json.JSONDecodeError:
            logger.error(f"无法解析JSON资源文件: {resource_path}")
            return {}
        except Exception as e:
            logger.error(f"加载资源文件失败: {resource_path}, 错误: {e}")
            return {}
    
    def load_module(self, locale: str, module: str, resource_types: Optional[List[str]] = None) -> None:
        """
        加载指定模块的所有资源文件或指定类型的资源文件
        
        Args:
            locale: 语言代码
            module: 模块名称 (如 "user", "auth")
            resource_types: 资源类型列表 (如 ["errors", "messages"])，为None时加载所有类型
        """
        locale = self._ensure_locale(locale)
        
        # 如果该语言的字典不存在，先创建
        if locale not in self._resources:
            self._resources[locale] = {}
        
        # 如果该语言的已加载模块集合不存在，先创建    
        if locale not in self._loaded_modules:
            self._loaded_modules[locale] = set()
        
        # 如果未指定资源类型，尝试发现所有可用类型
        if resource_types is None:
            module_dir = self.locale_dir / locale / module
            if module_dir.exists():
                resource_types = [
                    f.stem for f in module_dir.iterdir() 
                    if f.is_file() and f.suffix == ".json"
                ]
            else:
                # 如果目录不存在，则使用默认资源类型
                resource_types = ["errors", "messages", "labels", "descriptions", "enums"]
        
        # 加载每个资源类型
        for resource_type in resource_types:
            resource_key = f"{module}.{resource_type}"
            resource_data = self._load_resource(locale, module, resource_type)
            
            if resource_data:
                self._resources[locale][resource_key] = resource_data
                logger.debug(f"已加载资源: {resource_key} (语言: {locale})")
        
        # 将模块标记为已加载
        self._loaded_modules[locale].add(module)
        logger.debug(f"已完成模块加载: {module} (语言: {locale})")
    
    def get_text(self, 
                 key: str, 
                 params: Optional[Dict[str, Any]] = None, 
                 locale: str = None, 
                 fallback: str = None) -> str:
        """
        获取指定键的本地化文本
        
        Args:
            key: 资源键，格式为 "module.type.KEY" 或 "module.type.CATEGORY.KEY"
            params: 用于替换文本中占位符的参数字典
            locale: 语言代码，如为None则使用默认语言
            fallback: 当找不到对应文本时的回退文本
            
        Returns:
            本地化文本，如未找到则返回回退文本或键名
        
        Example:
            >>> i18n.get_text("user.errors.USER_NOT_FOUND", {"user_id": 123})
            "未找到用户：123"
        """
        if locale is None:
            locale = self.default_locale
        else:
            locale = self._ensure_locale(locale)
        
        # 解析资源键
        if key.count(".") < 2:
            logger.warning(f"无效的资源键格式: {key}, 正确格式应为: 'module.type.KEY'")
            return fallback if fallback is not None else key
        
        parts = key.split(".", 2)
        module, resource_type, item_key = parts
        
        # 按需加载模块资源
        if locale not in self._loaded_modules or module not in self._loaded_modules[locale]:
            self.load_module(locale, module, [resource_type])
        
        # 获取资源字典
        resource_key = f"{module}.{resource_type}"
        resource_dict = self._resources.get(locale, {}).get(resource_key, {})
        
        # 处理多级键 (如 "CATEGORY.KEY")
        value = resource_dict
        for key_part in item_key.split("."):
            if not isinstance(value, dict) or key_part not in value:
                if fallback is not None:
                    # 尝试获取回退文本
                    return self.get_text(fallback, params, locale)
                else:
                    # 使用键名作为最后回退
                    logger.debug(f"找不到本地化文本: {key} (语言: {locale})")
                    return item_key
            value = value[key_part]
        
        # 确保结果是字符串
        if not isinstance(value, str):
            logger.warning(f"本地化资源不是字符串: {key} = {value}")
            return item_key
        
        # 替换参数
        if params:
            try:
                return value.format(**params)
            except KeyError as e:
                logger.warning(f"替换参数失败，缺少键: {e}, 文本: {value}")
                return value
            except Exception as e:
                logger.warning(f"替换参数时出错: {e}, 文本: {value}")
                return value
        
        return value
    
    def get_preferred_locale(self, request: Request) -> str:
        """
        从请求中获取用户偏好的语言
        
        首先检查查询参数、Cookie、请求头，然后回退到默认语言
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            语言代码
        """
        # 尝试从查询参数获取
        query_locale = request.query_params.get("locale")
        if query_locale and query_locale in self.supported_locales:
            return query_locale
        
        # 尝试从Cookie获取
        cookie_locale = request.cookies.get("locale")
        if cookie_locale and cookie_locale in self.supported_locales:
            return cookie_locale
        
        # 尝试从Accept-Language头获取
        accept_language = request.headers.get("accept-language")
        if accept_language:
            locales = self._parse_accept_language(accept_language)
            for locale in locales:
                ensured_locale = self._ensure_locale(locale)
                if ensured_locale != self.default_locale:  # 不等于默认语言表示找到了匹配项
                    return ensured_locale
        
        # 回退到默认语言
        return self.default_locale
    
    @staticmethod
    def _parse_accept_language(header: str) -> List[str]:
        """解析Accept-Language请求头，返回按优先级排序的语言代码列表"""
        if not header:
            return []
        
        # 拆分语言代码和优先级
        languages = []
        for item in header.split(","):
            parts = item.strip().split(";q=")
            if len(parts) == 1:
                languages.append((parts[0].strip(), 1.0))
            else:
                try:
                    languages.append((parts[0].strip(), float(parts[1])))
                except (ValueError, IndexError):
                    languages.append((parts[0].strip(), 0.0))
        
        # 按优先级排序
        languages.sort(key=lambda x: x[1], reverse=True)
        return [lang for lang, _ in languages]


# 创建全局单例实例
i18n = I18nManager(
    locale_dir=settings.LOCALE_DIR,
    default_locale=settings.DEFAULT_LOCALE
)


def get_text(key: str, params: Optional[Dict[str, Any]] = None, locale: str = None) -> str:
    """
    便捷函数：获取本地化文本
    
    Args:
        key: 资源键，格式为 "module.type.KEY"
        params: 参数字典
        locale: 语言代码
        
    Returns:
        本地化文本
    """
    return i18n.get_text(key, params, locale)


def preload_modules(locales: Optional[List[str]] = None, modules: Optional[List[str]] = None) -> None:
    """
    预加载指定模块和语言的资源
    
    在应用启动时调用此函数可以提前加载常用资源
    
    Args:
        locales: 要加载的语言列表，如为None则加载所有支持的语言
        modules: 要加载的模块列表，如为None则不加载任何模块
    """
    if modules is None:
        return
    
    if locales is None:
        locales = i18n.supported_locales
    
    for locale in locales:
        for module in modules:
            i18n.load_module(locale, module)
    
    logger.info(f"已预加载 {len(modules)} 个模块的资源，语言: {', '.join(locales)}")