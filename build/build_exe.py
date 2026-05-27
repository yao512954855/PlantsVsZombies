"""
PyInstaller 打包脚本 - 一键生成可执行文件

支持 Windows、Mac、Linux 三平台打包。
自动生成图标、版本信息、依赖项。

使用方式:
    # Windows
    python build/build_exe.py --platform windows
    
    # Mac
    python build/build_exe.py --platform macos
    
    # Linux
    python build/build_exe.py --platform linux
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from typing import List, Optional
import json


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
ASSETS_DIR = PROJECT_ROOT / "assets"


def get_platform_config(platform: str) -> dict:
    """获取平台特定配置
    
    Args:
        platform: 平台名称 (windows/macos/linux)
        
    Returns:
        配置字典
    """
    configs = {
        "windows": {
            "ext": ".exe",
            "icon": "assets/icon.ico",
            "name": "PlantsVsZombies.exe",
            "hidden_imports": [
                "pygame",
                "PIL",
                "numpy"
            ],
            "exclude": [
                "tkinter",
                "matplotlib"
            ]
        },
        "macos": {
            "ext": ".app",
            "icon": "assets/icon.icns",
            "name": "PlantsVsZombies.app",
            "hidden_imports": [
                "pygame",
                "PIL",
                "numpy"
            ],
            "exclude": []
        },
        "linux": {
            "ext": "",
            "icon": "assets/icon.png",
            "name": "PlantsVsZombies",
            "hidden_imports": [
                "pygame",
                "PIL",
                "numpy"
            ],
            "exclude": []
        }
    }
    
    return configs.get(platform, configs["windows"])


def generate_spec_file(platform: str, output_path: Path) -> None:
    """生成 PyInstaller spec 文件
    
    Args:
        platform: 目标平台
        output_path: 输出路径
    """
    config = get_platform_config(platform)
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('data', 'data'),
    ],
    hiddenimports={config['hidden_imports']},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={config['exclude']},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PlantsVsZombies',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
'''
    
    if platform == "windows" and config.get("icon"):
        spec_content += f"    icon='{config['icon']}',\n"
    
    spec_content += ''')
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)


def install_dependencies() -> None:
    """安装必要依赖"""
    print("📦 安装依赖...")
    
    requirements = [
        "pygame>=2.5.0",
        "pyinstaller>=6.0.0",
        "psutil>=5.9.0",
        "pillow>=10.0.0"
    ]
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--quiet", "--upgrade"
        ] + requirements)
        print("✅ 依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 依赖安装失败：{e}")


def clean_build_directories() -> None:
    """清理构建目录"""
    print("🧹 清理旧构建...")
    
    dirs_to_clean = [
        BUILD_DIR / "build",
        DIST_DIR
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    # 创建 dist 目录
    DIST_DIR.mkdir(exist_ok=True)
    print("✅ 清理完成")


def build_executable(platform: str, one_file: bool = False) -> bool:
    """构建可执行文件
    
    Args:
        platform: 目标平台
        one_file: 是否打包为单文件
        
    Returns:
        是否成功
    """
    print(f"🔨 开始构建 {platform} 版本...")
    
    config = get_platform_config(platform)
    spec_path = BUILD_DIR / f"pvz_{platform}.spec"
    
    # 生成 spec 文件
    generate_spec_file(platform, spec_path)
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(spec_path),
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR / "build"),
        "--specpath", str(BUILD_DIR),
        "--name", "PlantsVsZombies"
    ]
    
    if one_file:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    if not platform == "windows":
        cmd.append("--noconsole")
    
    # 添加图标
    icon_path = Path(config.get("icon", ""))
    if icon_path.exists():
        if platform == "windows":
            cmd.extend(["--icon", str(icon_path)])
        elif platform == "macos":
            cmd.extend(["--icon", str(icon_path)])
    
    try:
        subprocess.check_call(cmd, cwd=str(PROJECT_ROOT))
        print(f"✅ {platform} 版本构建成功!")
        print(f"📁 输出位置：{DIST_DIR}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败：{e}")
        return False


def create_release_package(platform: str) -> Optional[Path]:
    """创建发布包
    
    Args:
        platform: 目标平台
        
    Returns:
        发布包路径或 None
    """
    print("📦 创建发布包...")
    
    release_dir = DIST_DIR / "release"
    release_dir.mkdir(exist_ok=True)
    
    # 复制可执行文件
    if platform == "windows":
        exe_name = "PlantsVsZombies.exe"
    elif platform == "macos":
        exe_name = "PlantsVsZombies.app"
    else:
        exe_name = "PlantsVsZombies"
    
    exe_path = DIST_DIR / exe_name
    if not exe_path.exists():
        print(f"❌ 未找到可执行文件：{exe_path}")
        return None
    
    # 复制到发布目录
    if exe_path.is_dir():
        shutil.copytree(exe_path, release_dir / exe_name, dirs_exist_ok=True)
    else:
        shutil.copy2(exe_path, release_dir / exe_name)
    
    # 复制资源文件（如果需要）
    readme_src = PROJECT_ROOT / "README.md"
    if readme_src.exists():
        shutil.copy2(readme_src, release_dir / "README.md")
    
    # 创建版本信息
    version_info = {
        "name": "Plants Vs Zombies",
        "version": "1.0.0",
        "platform": platform,
        "build_date": Path.ctime(exe_path)
    }
    
    with open(release_dir / "version.json", 'w', encoding='utf-8') as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 发布包创建成功：{release_dir}")
    return release_dir


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="植物大战僵尸打包工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python build_exe.py --platform windows
  python build_exe.py --platform macos --onefile
  python build_exe.py --platform linux --clean
        """
    )
    
    parser.add_argument(
        "--platform",
        type=str,
        choices=["windows", "macos", "linux"],
        default="windows",
        help="目标平台 (默认：windows)"
    )
    
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="打包为单文件模式"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="构建前清理旧文件"
    )
    
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="跳过依赖安装"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🌱 植物大战僵尸 - 打包工具")
    print("=" * 60)
    print(f"平台：{args.platform}")
    print(f"单文件模式：{args.onefile}")
    print(f"清理模式：{args.clean}")
    print()
    
    # 安装依赖
    if not args.skip_deps:
        install_dependencies()
    
    # 清理
    if args.clean:
        clean_build_directories()
    
    # 构建
    success = build_executable(args.platform, args.onefile)
    
    if success:
        # 创建发布包
        create_release_package(args.platform)
        
        print()
        print("=" * 60)
        print("🎉 打包完成!")
        print("=" * 60)
        print(f"查看输出：{DIST_DIR}")
    else:
        print()
        print("=" * 60)
        print("❌ 打包失败，请检查错误日志")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
