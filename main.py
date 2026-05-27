#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
植物大战僵尸 - 主程序入口
工业级重构版本 v2.0
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PlantsVsZombies.data.src.PVZ import Pvz


def main():
    """主函数入口"""
    print("=" * 60)
    print("植物大战僵尸 - 工业级重构版")
    print("版本：2.0.0")
    print("=" * 60)
    
    try:
        # 创建游戏实例
        game = Pvz()
        # 启动游戏主循环
        game.run()
    except KeyboardInterrupt:
        print("\n游戏已退出")
    except Exception as e:
        print(f"\n发生错误：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
